# Phase 5
# Johnathan Saniuk, Amadeusz Piwowarczyk, Vishal Patel
# Purpose: Send a file from client to server using checksum to find errors and resend the packet if an error has occurred
# References: [1] J. Kurose and K. Ross, Computer Networking. Harlow, United Kingdom: Pearson Education Limited, 2017, pp. 159-164.
#             [2] https://stackoverflow.com/questions/10411085/converting-integer-to-binary-in-python
# https://www.geeksforgeeks.org/multithreading-python-set-1/   used to find multithreading

# Enable the creation of sockets
from socket import *
from threading import Timer
import array
import random
import time
import _thread
from Timer_Class import Timer
import os

# Define server name (or IP) and Port#
from typing import Any, Tuple

# start_time = time.time()
serverName = '192.168.1.239'  # input('Please write your IPv4 IP here: ')
'''   '192.168.1.239'   '''
'''   '192.168.1.105'   '''
serverPort = 12000

# Create the client socket. First parameter indicates IPv4, second param indicates UDP
clientSocket = socket(AF_INET, SOCK_DGRAM)
print("clientSocket:", clientSocket)

# *********************** Send client a question to know when files are ready to be sent over
message = ('Enter File Name to transfer file!')
# waits for client to input a message and then message is stored in the "message" variable

clientSocket.sendto(message.encode(), (serverName, serverPort))
# Convert the string message to byte type as we can only send bytes into a socket, done using encode()
# sendto() attaches destination address to message and sends resulting packet into the process's socket (clientSocket)
# We didn't need to specify port number of client because we want the system to do it automatically for us

# Define Window Size (0 to N)
N = 9
N = N.to_bytes(1, byteorder='big')
clientSocket.sendto(N, (serverName, serverPort))
N = int.from_bytes(N, byteorder='big')

modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
# Packet's data arrives inside of variable modifiedMessage and packet's source address is inside serverAddress variable
# serverAddress contains both the server's IP and server's port number
# recvfrom takes the buffer size of 2048 as an input and this size is suitable for most purposes

print(modifiedMessage.decode().upper())
# Prints the modifiedMessage on user's display once it converts the message from bytes to string but now capitalized

# **************************************************


# Store selected image into a variable
FileName = 'picture.bmp'  # input('Write the file name you wish to send: ')
image = open(FileName, 'rb')
file_size = os.stat(FileName).st_size

# Set the packet size and create an index to count packets
packet_size = 1024
packetIndex = 0
print("packet size is:", packet_size)

# Mutexes
base_lock = _thread.allocate_lock()
expected_lock = _thread.allocate_lock()

# Variable to add the Sequence Number to each packet
SeqNum = 0
sendPacket = bytearray()
initialPacket = bytearray()
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

ack_error = 0
data_loss_rate = 0


# Define a make packet function that outputs a packet and an index number
def make_packet(csize, file_name, seq_num):
    packet = file_name.read(csize)

    # Make the checksum and convert it to bytes so it can be appended to the packet
    if len(packet) % 2 != 0:
        packet += b'\0'

    res = sum(array.array("H", packet))
    res = (res >> 16) + (res & 0xffff)
    res += res >> 16

    checksum = (~res) & 0xffff
    bit_sum = checksum.to_bytes(2, byteorder='little')

    # Create the sendPacket by appending sequence number, checksum, and data
    send_packet = bytearray()
    seq_num = seq_num.to_bytes(2, byteorder='big')
    send_packet.extend(seq_num)
    seq_num = int.from_bytes(seq_num, byteorder='big')
    seq_num += 1

    for i in bit_sum:
        send_packet.append(i)
    for j in packet:
        send_packet.append(j)

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


def final_handshake(da_base):
    da_base = da_base.to_bytes(2, byteorder='big')
    final_packet = bytearray()
    for i in da_base:
        final_packet.append(i)
    clientSocket.sendto(final_packet, (serverName, serverPort))
    print("Final packet sent")


def packet_catcher(client_socket):
    global base
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
        NewSeqNum = ackPacket[:2]
        NewSeqNum = int.from_bytes(NewSeqNum, byteorder='big')
        serverChecksum = ackPacket[2:]

        bitsum = packet_Queue[NewSeqNum]
        bitsum = bitsum[2:4]

        if serverChecksum != bitsum:
            # Timeout to resend window
            print("Corrupt Checksum")
        elif ack_corrupt():
            # Timeout to resend window
            print("Corrupt ACK", NewSeqNum)
        elif NewSeqNum > expected_seq_num and serverChecksum == bitsum:
            ack_Queue[NewSeqNum] = True
            print("Out of order ACK", NewSeqNum, "received")
            if base > 20:
                packet_Queue.pop((base - 20), None)
            if timer_window[NewSeqNum % (N + 1)].running():
                timer_window[NewSeqNum % (N + 1)].stop()
        elif NewSeqNum < expected_seq_num:
            # Duplicate ACK, continue on
            print("Duplicate ACK", NewSeqNum, "received")
            if timer_window[NewSeqNum % (N + 1)].running():
                timer_window[NewSeqNum % (N + 1)].stop()
        elif NewSeqNum == expected_seq_num and serverChecksum == bitsum:
            print("Proper ACK", NewSeqNum, "received")
            if timer_window[NewSeqNum % (N + 1)].running():
                timer_window[NewSeqNum % (N + 1)].stop()
            ack_Queue[base] = True
            while base in ack_Queue:
                base_lock.acquire()
                base += 1
                base_lock.release()
                expected_seq_num = base
                print("base =", base)
                if base > 20:
                    packet_Queue.pop((base - 20), None)

        else:
            print("I done goofed")

        if base > (file_size / packet_size):
            image.close()
            _thread.exit()


start2 = time.time()

if __name__ == "__main__":
    # Buffer the packets

    _thread.start_new_thread(packet_catcher, (clientSocket,))

    for x in range(0, N + 1):
        timer_window[x] = Timer(0.05)

    print(timer_window)

    while 1:
        while (base + N + 20) not in packet_Queue and SeqNum <= (file_size / packet_size):
            sendPacket, SeqNum = make_packet(packet_size, image, SeqNum)
            packet_Queue[SeqNum - 1] = sendPacket
            if len(sendPacket) < 1028:
                print("Length of packet_Queue", len(packet_Queue))
                break
        if nextSeqNum == (base + N):
            time.sleep(0.001)

        for x in range(base, base + N):
            if timer_window[x % (N + 1)].timeout():
                print("Packet #", x, "timed out!")
                if timer_window[x % (N + 1)].running():
                    timer_window[x % (N + 1)].stop()
                    data_loss_test = data_loss(data_loss_rate)
                    if not data_loss_test and x < (file_size / packet_size):
                        clientSocket.sendto(packet_Queue[x], (serverName, serverPort))
                        print("Packet #", x, "resent")
                        timer_window[x % (N + 1)].start()
                    elif data_loss_test:
                        print("Packet #", x, "lost again! Ya done goofed!")
                        timer_window[x % (N + 1)].start()

        if nextSeqNum < (base + N) and base < (file_size / packet_size):
            data_loss_test = data_loss(data_loss_rate)
            if not data_loss_test and nextSeqNum not in ack_Queue and nextSeqNum < (file_size / packet_size):
                # If data_loss is false, packet is not lost. Send the packet
                timer_window[nextSeqNum % (N + 1)].start()
                clientSocket.sendto(packet_Queue[nextSeqNum], (serverName, serverPort))
                print("Packet #", nextSeqNum, "sent")
                nextSeqNum += 1
            elif data_loss_test is True:
                # Else if data_loss is True, the packet is "lost" en route to the server.
                # Simulate by not sending the packet
                timer_window[nextSeqNum % (N + 1)].start()
                print(base, "Data was lost!")
                nextSeqNum += 1
        elif base >= (file_size / packet_size):
            final_handshake(base)
            ackPacket, trashdata = clientSocket.recvfrom(2048)
            # Parse the data
            NewSeqNum = ackPacket[:2]
            NewSeqNum = int.from_bytes(NewSeqNum, byteorder='big')
            if NewSeqNum == base:
                if timer_window[NewSeqNum % (N + 1)].running():
                    timer_window[NewSeqNum % (N + 1)].stop()
                break

end2 = start2
print("Total time for completion was %s" % (time.time() - start2))

# RRRRREEEEEEEEEEEeeeeeeeeEEEEEEEEeeeeeeEEEEEeeeEeEEeEEEEEEEEEEEEEEEEE
