# Phase 6 TCP
# Johnathan Saniuk, Amadeusz Piwowarczyk, Vishal Patel
# Purpose: Send a file from client to server using checksum to find errors and resend the packet if an error has occurred
# References: [1] J. Kurose and K. Ross, Computer Networking. Harlow, United Kingdom: Pearson Education Limited, 2017, pp. 159-164.
#             [2] https://stackoverflow.com/questions/10411085/converting-integer-to-binary-in-python
# https://www.geeksforgeeks.org/multithreading-python-set-1/   used to find multithreading

# Enable the creation of sockets
from socket import *
import array
import random
import time
import _thread
from Timer_Class import Timer
import os

# Define server name (or IP) and Port#
from typing import Any, Tuple

# start_time = time.time()
serverName = '192.168.1.239'   # input('Please enter your IPv4 IP here: ')
# '192.168.1.105'
serverPort = 12000

# Create the client socket. First parameter indicates IPv4, second param indicates UDP
clientSocket = socket(AF_INET, SOCK_DGRAM)

# Ask user to enter window size, window size defines number of packets sent at a single time (sliding window if prop ack received)
N = 9    # int(input('Enter window size for packet transfer: '))

# *********************** Ask sender to input simulation Error/Loss during transfer
# print("Enter Error/Loss below. If no Error/Loss, enter a '0' \n")
ack_error = 0   # int(input('Enter ACK Error percent for packet transfer: '))
data_loss_rate = 0   # int(input('Enter Data Loss percent for packet transfer: '))

# print("\nWaiting for server....................\n")

# *********************** Send client a question to know when files are ready to be sent over
message = 'Enter File Name to transfer file!'
# waits for client to input a message and then message is stored in the "message" variable

clientSocket.sendto(message.encode(), (serverName, serverPort))
# Convert the string message to byte type as we can only send bytes into a socket, done using encode()
# sendto() attaches destination address to message and sends resulting packet into the process's socket (clientSocket)
# We didn't need to specify port number of client because we want the system to do it automatically for us

modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
# Packet's data arrives inside of variable modifiedMessage and packet's source address is inside serverAddress variable
# serverAddress contains both the server's IP and server's port number
# recvfrom takes the buffer size of 2048 as an input and this size is suitable for most purposes

print(modifiedMessage.decode().upper())
# Prints the modifiedMessage on user's display once it converts the message from bytes to string but now capitalized

# **************************************************


# Store selected image into a variable
FileName = 'picture.bmp'   # input('Write the file name you wish to send: ')

image = open(FileName, 'rb')
# print("\nFile is being transfered . . .")
file_size = os.stat(FileName).st_size

# Set the packet size and create an index to count packets
packet_size = 1024
# print("packet size is:", packet_size)

# Mutexes
base_lock = _thread.allocate_lock()
packet_Queue_lock = _thread.allocate_lock()

# Variable to add the Sequence Number to each packet
SeqNum = 0
sendPacket = bytearray()
bitsum = 0
# Variable to track which packet in the queue we're on
nextSeqNum = 0
# Create an empty dictionary to store the sent but unacked packets
packet_Queue = {}
# Create a dictionary to store ACKs
ack_Queue = {}
# Dictionary of timers
timer_window = {}
# Beginning of the window
base = 0
# Instantiate Timer
ack_timer = Timer(0.05)
final_flag = False


def make_header(csize, file_name, seq_num):
    global final_flag
    packet = 0
    if not final_flag:
        packet = file_name.read(csize)

        # Make the checksum and convert it to bytes so it can be appended to the packet
        if len(packet) % 2 != 0:
            packet += b'\0'

        res = sum(array.array("H", packet))
        res = (res >> 16) + (res & 0xffff)
        res += res >> 16

        checksum = (~res) & 0xffff
        bit_sum = checksum.to_bytes(2, byteorder='little')
    else:
        bit_sum = b'\x00\x00'

    seq_num = seq_num.to_bytes(4, byteorder='big')
    # print("Seq Num of packet is:", seq_num)
    source_port = serverPort.to_bytes(2, byteorder='little')
    dest_port = 12000
    dest_port = dest_port.to_bytes(2, byteorder='little')
    ACK_Number = b'\x00\x00\x00\x00'
    head_len = b'\x00'
    flag_byte = 0x00
    flag_byte = flag_byte | 0x10
    '''
    CWR = 10000000
    ECE = 010000000
    Urgent = 00100000
    ACK_valid = 00010000
    Push_data = 00001000
    RST = 00000100
    SYN = 00000010
    FIN = 00000001
    '''
    Rec_window = b'\x00\x00'
    Urg_Data = b'\x00\x00'
    Options = b'\x00\x00\x00\x00'
    # Create the sendPacket by appending sequence number, checksum, and data
    header_packet = bytearray()
    for a in source_port:
        header_packet.append(a)
    for b in dest_port:
        header_packet.append(b)
    for c in seq_num:
        header_packet.append(c)
    for d in ACK_Number:
        header_packet.append(d)
    for e in head_len:
        header_packet.append(e)
    header_packet.append(flag_byte)
    for g in Rec_window:
        header_packet.append(g)
    for h in bit_sum:
        header_packet.append(h)
    for i in Urg_Data:
        header_packet.append(i)
    for j in Options:
        header_packet.append(j)

    return header_packet, packet


# Define a make packet function that outputs a packet and an index number
def make_packet(csize, file_name, seq_num):

    send_packet, data_packet = make_header(csize, file_name, seq_num)

    for k in data_packet:
        send_packet.append(k)

    print("Seq Number is:", seq_num)
    seq_num += 1

    return send_packet, seq_num


def data_loss(test_num):
    # Select a random int btwn 0 and 100
    rand_num = random.randrange(0, 100)
    # if randNum is less than the specified error rate, don't send packet
    if rand_num < test_num:
        loss = True
        return loss
    else:
        loss = False
        return loss


def ack_corrupt():
    # Select a random int btwn 0 and 100
    rand_num = random.randrange(0, 100)
    # if randNum is less than the specified error rate, flip the bit
    if rand_num < ack_error:
        return True
    else:
        return False


def packet_catcher(client_socket):
    global base
    global final_flag
    # Variable to track the expected Sequence Number we receive from the Server
    expected_seq_num = 0
    while 1:
        # Try to receive the ACK packet from server. If not received in 50ms, timeout and resend the packet

        if ack_timer.timeout():
            expected_seq_num = base
            print("expected seq num is now:", expected_seq_num)

        # trasdata is the address sent with the ACK. We don't need it
        ackPacket, trashdata = client_socket.recvfrom(2048)

        # Parse the data
        NewSeqNum = ackPacket[4:8]
        NewSeqNum = int.from_bytes(NewSeqNum, byteorder='big')
        serverChecksum = ackPacket[16:18]

        bitsum = packet_Queue[NewSeqNum]
        bitsum = bitsum[16:18]

        print(NewSeqNum, serverChecksum, bitsum)

        if serverChecksum != bitsum:
            # Timeout to resend window
            print("Corrupt Checksum")
            pass
        elif ack_corrupt():
            # Timeout to resend window
            print("Corrupt ACK", NewSeqNum)
            pass
        elif NewSeqNum > expected_seq_num and serverChecksum == bitsum:
            # If NewSeqNum is greater than what we expect, it's an out of order ACK.
            # Receive the ACK into the proper place in the dictionary
            ack_Queue[NewSeqNum] = True
            print("Out of order ACK", NewSeqNum, "received")
            # Stop the timer for this ACK if it's still running
            if timer_window[NewSeqNum % (N + 1)].running():
                timer_window[NewSeqNum % (N + 1)].stop()
        elif NewSeqNum < expected_seq_num:
            # If NewSeqNum is less than what we're expecting, Duplicate ACK
            # continue on and stop it's timer if it's running
            print("Duplicate ACK", NewSeqNum, "received")
            if timer_window[NewSeqNum % (N + 1)].running():
                timer_window[NewSeqNum % (N + 1)].stop()
        elif NewSeqNum == expected_seq_num and serverChecksum == bitsum:
            # Everything checks out, update base and expected, add ACK to dictionary, stop the timer
            print("Proper ACK", NewSeqNum, "received")
            if timer_window[NewSeqNum % (N + 1)].running():
                timer_window[NewSeqNum % (N + 1)].stop()
            ack_Queue[base] = True

        while base in ack_Queue:
            # If the base exists in the ack_Queue, we can start shifting the window.
            # Shift the window for every in order packet in the ack_Queue. Stop when you hit an unacked packet
            base_lock.acquire()
            base += 1
            base_lock.release()
            expected_seq_num = base
            print("base =", base)
            if base > N:
                packet_Queue_lock.acquire()
                packet_Queue.pop((base - N), None)
                packet_Queue_lock.release()
                ack_Queue.pop((base - N), None)

        if base > (file_size / packet_size):
            # Close the file and the thread if the last ACK is received
            final_flag = True
            image.close()
            _thread.exit()


start2 = time.time()

if __name__ == "__main__":
    # Buffer the packets

    # Start the ACK packet_cather thread
    _thread.start_new_thread(packet_catcher, (clientSocket,))

    for x in range(0, N + 1):
        # Initialize a timer for each potential packet in the window
        timer_window[x] = Timer(0.05)

    while 1:
        while (base + N + 20) not in packet_Queue and SeqNum <= (file_size / packet_size):
            # Make and buffer in new packets up to 20 packets above the current window max
            sendPacket, SeqNum = make_packet(packet_size, image, SeqNum)
            packet_Queue_lock.acquire()
            packet_Queue[SeqNum - 1] = sendPacket
            packet_Queue_lock.release()
            if len(sendPacket) < 1028:
                print("Length of packet_Queue", len(packet_Queue))
                break
        if nextSeqNum == (base + N):
            # If the window is stuck waiting for an ACK, sleep the program for 1ms
            # to keep from looping thousands of times unnecessarily
            time.sleep(0.001)

        for x in range(base, base + N):
            # For each timer, check if it has timed out
            if timer_window[x % (N + 1)].timeout():
                # If a timer has timed out, stop the timer (if it's still running) and resend the packet
                print("Packet #", x, "timed out!")
                if timer_window[x % (N + 1)].running():
                    timer_window[x % (N + 1)].stop()
                    data_loss_test = data_loss(data_loss_rate)
                    if not data_loss_test and x < (file_size / packet_size):
                        # Run the data loss function before sending
                        clientSocket.sendto(packet_Queue[x], (serverName, serverPort))
                        print("Packet #", x, "resent")
                        timer_window[x % (N + 1)].start()
                    elif data_loss_test:
                        # If data is lost start the timer anyway, we don't know if it's been sent or not
                        print("Packet #", x, "lost again! Ya done goofed!")
                        timer_window[x % (N + 1)].start()

        if nextSeqNum < (base + N) and base < (file_size / packet_size):
            data_loss_test = data_loss(data_loss_rate)
            if not data_loss_test and nextSeqNum not in ack_Queue and nextSeqNum < (file_size / packet_size):
                # If data_loss is false, packet is not lost. Start the timer and send the packet
                # Also check to see if nextSeqNum has not been ACKed, and if it's within the total packets in the file
                clientSocket.sendto(packet_Queue[nextSeqNum], (serverName, serverPort))
                print("Packet #", nextSeqNum, "sent")
            elif data_loss_test is True:
                # Else if data_loss is True, the packet is "lost" en route to the server.
                # Simulate by not sending the packet but starting the timer anyway
                print(base, "Data was lost!")
                pass
            # Update nextSeqNum so that the next packet can be sent on the next loop
            timer_window[nextSeqNum % (N + 1)].start()
            nextSeqNum += 1
        elif base >= (file_size / packet_size):
            # At the end of the file, start the final handshake process
            final_packet, data_packet = make_header(packet_size, image, SeqNum)
            clientSocket.sendto(final_packet, (serverName, serverPort))
            print("Final packet sent")
            break



end2 = start2
print("Total time for completion was %s" % (time.time() - start2))

# RRRRREEEEEEEEEEEeeeeeeeeEEEEEEEEeeeeeeEEEEEeeeEeEEeEEEEEEEEEEEEEEEEE
