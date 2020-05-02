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
serverName = '192.168.1.105'   # input('Please enter your IPv4 IP here: ')
# '192.168.1.239'
# '192.168.1.105'
serverPort = 12000

# Create the client socket. First parameter indicates IPv4, second param indicates UDP
clientSocket = socket(AF_INET, SOCK_DGRAM)

# Ask user to enter window size, window size defines number of packets sent at a single time (sliding window if prop ack received)
N = 20    # int(input('Enter window size for packet transfer: '))

# *********************** Ask sender to input simulation Error/Loss during transfer
# print("Enter Error/Loss below. If no Error/Loss, enter a '0' \n")
ack_error = 0   # int(input('Enter ACK Error percent for packet transfer: '))
data_loss_rate = 0   # int(input('Enter Data Loss percent for packet transfer: '))

# Store selected image into a variable
FileName = 'picture.bmp'   # input('Write the file name you wish to send: ')

image = open(FileName, 'rb')
# print("\nFile is being transfered . . .")
file_size = os.stat(FileName).st_size

# Initial Seq Number after coin flip
initialSeqNum = random.randrange(10, 500, 5)
print('Binary initialSeqNum =', initialSeqNum)

'''
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
'''

# Mutexes
base_lock = _thread.allocate_lock()
packet_Queue_lock = _thread.allocate_lock()
print_lock = _thread.allocate_lock()

# Max Segment Size
MSS = 1024
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
handshake_set_fin = True


def header_maker(seq_num, bit_sum, flag, des_port, ack_num):
    seq_num = seq_num.to_bytes(4, byteorder='big')
    # print("Seq Num of packet is:", seq_num)
    source_port = serverPort.to_bytes(2, byteorder='little')
    dest_port = des_port
    dest_port = dest_port.to_bytes(2, byteorder='little')
    ACK_Number = ack_num
    head_len = b'\x00'
    flag_byte = 0x00
    flag_byte = flag_byte | flag
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

    return header_packet


def make_header(csize, file_name, seq_num, des_port, ack_numb):
    global final_flag
    global handshake_set_fin
    start = True
    packet = 0
    end = 0
    bit_sum = b'\x00\x00'
    dest_port = des_port
    ack_num = ack_numb
    if not start:
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
            flag = 0x00
            handshake_set_fin = True
            end = 1

    elif start == 0:
        start = False

    # if handshake false, send segments
    if not handshake_set_fin:
        flag = 0x00
        header_packet = header_maker(seq_num, bit_sum, flag, dest_port, ack_num)

    # if handshake true and segment is at the end
    elif handshake_set_fin and end == 1:
        flag = 0x01
        header_packet = header_maker(seq_num, bit_sum, flag, dest_port, ack_num)

    # if handshake true and we are initializing communication with receiver
    else:
        flag = 0x02
        header_packet = header_maker(seq_num, bit_sum, flag, dest_port, ack_num)
        handshake_set_fin = False

    # print("header_packet =", header_packet)
    return header_packet, packet


# Define a make packet function that outputs a packet and an index number
def make_packet(csize, file_name, seq_num):

    send_packet, data_packet = make_header(csize, file_name, seq_num)
    #print("data_packet =", data_packet)
    for k in data_packet:
        send_packet.append(k)

    return send_packet, len(data_packet)


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


def parser(rec_pack):
    # Parse data from TCP Segment
    source_port = rec_pack[:2]
    clientPort = source_port
    des_port = rec_pack[2:4]
    seq_num = rec_pack[4:8]
    ack_number = rec_pack[8:12]
    Header_N_unused = rec_pack[12:13]
    Header_Bit_setting = rec_pack[13:14]
    Header_Bit_setting = int.from_bytes(Header_Bit_setting, byteorder='little')
    CWR = (Header_Bit_setting >> 7) & 0x01
    ECE = (Header_Bit_setting >> 6) & 0x01
    Urgent = (Header_Bit_setting >> 5) & 0x01
    ACK_valid = (Header_Bit_setting >> 4) & 0x01
    Push_data = (Header_Bit_setting >> 3) & 0x01
    RST = (Header_Bit_setting >> 2) & 0x01
    SYN = (Header_Bit_setting >> 1) & 0x01
    FIN = (Header_Bit_setting >> 0) & 0x01
    Rec_Window = rec_pack[14:16]
    client_checksum = rec_pack[16:18]
    Urgent_data = rec_pack[18:20]
    Options = rec_pack[20:24]

    return seq_num, des_port, ack_number, SYN, FIN

def packet_catcher(client_socket):
    global base
    global final_flag
    # Variable to track the expected Sequence Number we receive from the Server
    expected_seq_num = 0
    dup_counter = 0
    temp_seq_num = 0
    while 1:
        # Try to receive the ACK packet from server. If not received in 50ms, timeout and resend the packet

        if ack_timer.timeout():
            expected_seq_num = base
            print_lock.acquire()
            print("expected seq num is now:", expected_seq_num)
            print_lock.release()

        # trasdata is the address sent with the ACK. We don't need it
        ackPacket, trashdata = client_socket.recvfrom(2048)

        # Parse the data
        NewSeqNum = ackPacket[4:8]
        NewSeqNum = int.from_bytes(NewSeqNum, byteorder='big')
        serverChecksum = ackPacket[16:18]

        selected_packet = packet_Queue[NewSeqNum]
        segment_size = selected_packet[24:]
        bitsum = selected_packet[16:18]

        print_lock.acquire()
        print("NewSeqNum =", NewSeqNum, "serverChecksum =", serverChecksum, "bitsum =", bitsum)
        print_lock.release()

        if serverChecksum != bitsum:
            # Timeout to resend window
            print_lock.acquire()
            print("Corrupt Checksum")
            print_lock.release()
            pass
        elif ack_corrupt():
            # Timeout to resend window
            print_lock.acquire()
            print("Corrupt ACK", NewSeqNum)
            print_lock.release()
            pass
        elif NewSeqNum > expected_seq_num and serverChecksum == bitsum:
            # If NewSeqNum is greater than what we expect, ACKs were lost but the data was received by the Server
            # Stop the timer for this all previous ACKs if they're still running
            print_lock.acquire()
            print("base =", base, "NewSeqNum =", NewSeqNum)
            print_lock.release()
            for close_timer in range(base % (N * MSS), NewSeqNum % ((N + 1) * MSS), MSS):
                print("close_timer =", close_timer)
                if timer_window[close_timer].running():
                    timer_window[close_timer].stop()
                    print_lock.acquire()
                    print("Timer #", close_timer, "closed!!!!!")
                    print_lock.release()
            else:
                if timer_window[NewSeqNum % (N * MSS)].running():
                    timer_window[NewSeqNum % (N * MSS)].stop()
                    print_lock.acquire()
                    print("Timer #", NewSeqNum % (N * MSS), "closedAAAAA")
                    print_lock.release()
            base_lock.acquire()
            base = (NewSeqNum + len(segment_size))
            base_lock.release()
            expected_seq_num = base
            print_lock.acquire()
            print("base =", base)
            print("Cumulative ACK", NewSeqNum, "received")
            print_lock.release()
        elif NewSeqNum < expected_seq_num:
            # If NewSeqNum is less than what we're expecting, Duplicate ACK
            # continue on and stop it's timer if it's running
            if timer_window[NewSeqNum % (N * MSS)].running():
                timer_window[NewSeqNum % (N * MSS)].stop()
                print_lock.acquire()
                print("Timer #", NewSeqNum % (N * MSS), "closed")
                print_lock.release()
            print_lock.acquire()
            print("Duplicate ACK", NewSeqNum, "received")
            print_lock.release()
            if dup_counter == 0:
                dup_counter += 1
                temp_seq_num = NewSeqNum
            elif dup_counter == 2 and NewSeqNum == temp_seq_num:
                print_lock.acquire()
                print("Fast Retransmit, resending", NewSeqNum + MSS)
                print_lock.release()
                clientSocket.sendto(packet_Queue[NewSeqNum + MSS], (serverName, serverPort))
                if timer_window[(NewSeqNum + MSS) % (N * MSS)].running():
                    timer_window[(NewSeqNum + MSS) % (N * MSS)].stop()
                timer_window[(NewSeqNum + MSS) % (N * MSS)].start()
            elif dup_counter == 1 and temp_seq_num == NewSeqNum:
                dup_counter += 1
            else:
                dup_counter = 0
        elif NewSeqNum == expected_seq_num and serverChecksum == bitsum:
            # Everything checks out, update base and expected, add ACK to dictionary, stop the timer
            if timer_window[NewSeqNum % (N * MSS)].running():
                timer_window[NewSeqNum % (N * MSS)].stop()
                print_lock.acquire()
                print("Timer #", NewSeqNum % (N * MSS), "closed")
                print_lock.release()
            print_lock.acquire()
            print("Proper ACK", NewSeqNum, "received")
            print_lock.release()
            base_lock.acquire()
            base += len(segment_size)
            base_lock.release()
            expected_seq_num = base
            print_lock.acquire()
            print("base =", base)
            print_lock.release()

        if base > (N * MSS):
            packet_Queue_lock.acquire()
            packet_Queue.pop((base - (N * MSS)), None)
            packet_Queue_lock.release()

        if base >= (file_size + initialSeqNum):
            # Close the file and the thread if the last ACK is received
            final_flag = True
            image.close()
            _thread.exit()


# Initial handshake set up
# *************************************************************
# take our old way of communicating and replace with a handshake set up
dest_port = b'\x00\x00'
Ack_num = b'\x00\x00\x00\x00'
message, packet = make_header(MSS, image, initialSeqNum, dest_port, Ack_num)
clientSocket.sendto(message, (serverName, serverPort))

modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
# Packet's data arrives inside of variable modifiedMessage and packet's source address is inside serverAddress variable
# serverAddress contains both the server's IP and server's port number
# recvfrom takes the buffer size of 2048 as an input and this size is suitable for most purposes

Rec_Sequ_Num, dest_port, Ack_num, SYN, FIN = parser(modifiedMessage)
Rec_Sequ_Num = int.from_bytes(Rec_Sequ_Num, byteorder='little')
Ack_num = Rec_Sequ_Num + 1
Ack_num = Ack_num.to_bytes(4, byteorder='little')
if SYN == 1:
    SYN = 0
else:
    print('Ya done goooofed!!!')

message, packet = make_header(MSS, image, initialSeqNum, dest_port, Ack_num)
send_mss = MSS.to_bytes(2, byteorder='little')
for z in send_mss:
    message.append(z)
clientSocket.sendto(message, (serverName, serverPort))
# *************************************************************


start2 = time.time()

if __name__ == "__main__":
    # Buffer the packets

    # Start the ACK packet_cather thread
    _thread.start_new_thread(packet_catcher, (clientSocket,))

    for x in range(0, N + 1):
        # Initialize a timer for each potential packet in the window
        timer_window[x * MSS] = Timer(0.05)
        print_lock.acquire()
        print("Timer #:", x * MSS, "made")
        print_lock.release()

    while 1:
        while (base + ((N + 20) * MSS)) not in packet_Queue and SeqNum < (file_size + initialSeqNum):
            # Make and buffer in new packets up to 20 packets above the current window max
            sendPacket, data_length = make_packet(MSS, image, SeqNum)
            packet_Queue_lock.acquire()
            packet_Queue[SeqNum] = sendPacket
            packet_Queue_lock.release()

            print_lock.acquire()
            print("Segment #:", SeqNum, "made")
            print_lock.release()

            if len(packet_Queue[SeqNum]) < (24 + MSS):
                print_lock.acquire()
                print("Length of packet_Queue", len(packet_Queue))
                print_lock.release()

            SeqNum += data_length

        if nextSeqNum >= (base + (N * MSS)):
            # If the window is stuck waiting for an ACK, sleep the program for 1ms
            # to keep from looping thousands of times unnecessarily
            time.sleep(0.001)

        for x in range(base, base + (N * MSS), MSS):
            if x < (file_size + initialSeqNum) and timer_window[x % (N * MSS)].timeout():
                print_lock.acquire()
                print("x =", x)
                # For each timer, check if it has timed out
                print("x mod =", x % (N * MSS))
                print_lock.release()
                # If a timer has timed out, stop the timer (if it's still running) and resend the packet
                print_lock.acquire()
                print("Packet #", x, "timed out!")
                print("Timer #", x % (N * MSS))
                print_lock.release()
                if x not in packet_Queue:
                    print_lock.acquire()
                    print("Something's wrong here!")
                    print_lock.release()
                if timer_window[x % (N * MSS)].running():
                    timer_window[x % (N * MSS)].stop()
                    data_loss_test = data_loss(data_loss_rate)
                    if not data_loss_test and x < (file_size + initialSeqNum):
                        # Run the data loss function before sending
                        clientSocket.sendto(packet_Queue[x], (serverName, serverPort))
                        print_lock.acquire()
                        print("Packet #", x, "resent")
                        print_lock.release()
                        timer_window[x % (N * MSS)].start()
                    elif data_loss_test:
                        # If data is lost start the timer anyway, we don't know if it's been sent or not
                        print_lock.acquire()
                        print("Packet #", x, "lost again! Ya done goofed!")
                        print_lock.release()
                        timer_window[x % (N * MSS)].start()

        if nextSeqNum < (base + (N * MSS)) and base < (file_size + initialSeqNum):
            data_loss_test = data_loss(data_loss_rate)
            if not data_loss_test and nextSeqNum < (file_size + initialSeqNum):
                # If data_loss is false, packet is not lost. Start the timer and send the packet
                # Also check to see if nextSeqNum has not been ACKed, and if it's within the total packets in the file
                clientSocket.sendto(packet_Queue[nextSeqNum], (serverName, serverPort))
                print_lock.acquire()
                print("Packet #", nextSeqNum, "sent")
                print_lock.release()
            elif data_loss_test is True:
                # Else if data_loss is True, the packet is "lost" en route to the server.
                # Simulate by not sending the packet but starting the timer anyway
                print_lock.acquire()
                print(base, "Data was lost!")
                print_lock.release()
                pass
            if nextSeqNum < (file_size + initialSeqNum):
                # Update nextSeqNum so that the next packet can be sent on the next loop
                timer_window[nextSeqNum % (N * MSS)].start()
                length_of_packet = packet_Queue[nextSeqNum]
                length_of_packet = len(length_of_packet[24:])
                nextSeqNum += length_of_packet
        # We will need to change this to base >= (file_size + initial SeqNum)
        elif base >= (file_size + initialSeqNum):
            # At the end of the file, start the final handshake process
            final_packet, data_packet = make_header(MSS, image, SeqNum)
            clientSocket.sendto(final_packet, (serverName, serverPort))
            print_lock.acquire()
            print("Final packet sent")
            print_lock.release()
            break



end2 = start2
print("Total time for completion was %s" % (time.time() - start2))

# RRRRREEEEEEEEEEEeeeeeeeeEEEEEEEEeeeeeeEEEEEeeeEeEEeEEEEEEEEEEEEEEEEE
