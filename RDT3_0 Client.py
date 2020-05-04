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
# '192.168.1.239'
# '192.168.1.105'
serverPort = 12000
clientPort = 12000

# Create the client socket. First parameter indicates IPv4, second param indicates UDP
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(0.05)

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
# Globals
receivedSeqNum = 0
expectedSeqNum = 0
receivedAckNumber = b'\x00\x00\x00\x00'
expectedAckNumber = 0

# Global Flags
SYN = 1
FIN = 0
ACK_valid = 1
handshake_flag = True


# Mutexes
base_lock = _thread.allocate_lock()
packet_Queue_lock = _thread.allocate_lock()
print_lock = _thread.allocate_lock()
ACK_valid_lock = _thread.allocate_lock()

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



def flag_gen(flag):
    global ACK_valid
    global SYN
    global FIN

    if ACK_valid == 1:
        flag = flag | 0b00010000
    else:
        flag = flag & 0b11101111
    if SYN == 1:
        flag = flag | 0b00000010
    else:
        flag = flag & 0b11111101
    if FIN == 1:
        flag = flag | 0b00000001
    else:
        flag = flag & 0b11111110

    return flag


def make_header(csize, file_name, seq_num, client_port, server_port, ack_num):
    global handshake_flag
    global FIN
    global SYN
    packet = 0
    bit_sum = b'\x00\x00'
    if not handshake_flag:
        if SYN != 1 and FIN != 1:
            packet = file_name.read(csize)

            # Make the checksum and convert it to bytes so it can be appended to the packet
            if len(packet) % 2 != 0:
                packet += b'\0'

            res = sum(array.array("H", packet))
            res = (res >> 16) + (res & 0xffff)
            res += res >> 16

            checksum = (~res) & 0xffff
            bit_sum = checksum.to_bytes(2, byteorder='little')

    seq_num = seq_num.to_bytes(4, byteorder='big')
    # print("Seq Num of packet is:", seq_num)
    client_port = client_port.to_bytes(2, byteorder='little')
    server_port = server_port.to_bytes(2, byteorder='little')
    ACK_Number = ack_num.to_bytes(4, byteorder='big')
    head_len = b'\x00'
    flag_byte = 0x00
    flag_byte = flag_gen(flag_byte)
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
    for a in client_port:
        header_packet.append(a)
    for b in server_port:
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

    # print("header_packet =", header_packet)
    return header_packet, packet


# Define a make packet function that outputs a packet and an index number
def make_packet(csize, file_name, seq_num, ack_numb):
    global clientPort
    global serverPort
    send_packet, data_packet = make_header(csize, file_name, seq_num, clientPort, serverPort, ack_numb)
    if data_packet != 0:
        for k in data_packet:
            send_packet.append(k)
    else:
        data_packet = b'\x00'

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
    global SYN
    global FIN
    global ACK_valid
    # Parse data from TCP Segment
    server_port = rec_pack[:2]
    client_port = rec_pack[2:4]
    seq_num = rec_pack[4:8]
    Header_N_unused = rec_pack[12:13]
    Header_Bit_setting = rec_pack[13:14]
    Header_Bit_setting = int.from_bytes(Header_Bit_setting, byteorder='little')
    CWR = (Header_Bit_setting >> 7) & 0x01
    ECE = (Header_Bit_setting >> 6) & 0x01
    Urgent = (Header_Bit_setting >> 5) & 0x01
    ACK_valid = (Header_Bit_setting >> 4) & 0x01
    #print("ACK_valid =", ACK_valid)
    Push_data = (Header_Bit_setting >> 3) & 0x01
    RST = (Header_Bit_setting >> 2) & 0x01
    SYN = (Header_Bit_setting >> 1) & 0x01
    #print("SYN =", SYN)
    FIN = (Header_Bit_setting >> 0) & 0x01
    Rec_Window = rec_pack[14:16]
    server_checksum = rec_pack[16:18]
    Urgent_data = rec_pack[18:20]
    Options = rec_pack[20:24]
    data_packet = rec_pack[24:]

    if ACK_valid == 1:
        ack_number = rec_pack[8:12]
    else:
        ack_number = b'\x00\x00\x00\x00'

    server_port = int.from_bytes(server_port, byteorder='little')
    client_port = int.from_bytes(client_port, byteorder='little')

    return seq_num, ack_number, data_packet, server_checksum, client_port, server_port


def packet_catcher(client_socket):
    global base
    global handshake_flag
    global receivedSeqNum
    global receivedAckNumber
    # Variable to track the expected Sequence Number we receive from the Server
    expected_seq_num = receivedSeqNum
    expected_ack_num = initialSeqNum + MSS
    dup_counter = 0
    temp_ack_num = 0
    while 1:
        # Try to receive the ACK packet from server. If not received in 50ms, timeout and resend the packet
        # trasdata is the address sent with the ACK. We don't need it
        ackPacket, trashdata = client_socket.recvfrom(2048)

        # Parse the data
        NewSeqNum, NewAckNum, data_packet, serverChecksum, client_port, server_port = parser(ackPacket)
        NewSeqNum = int.from_bytes(NewSeqNum, byteorder='big')
        NewAckNum = int.from_bytes(NewAckNum, byteorder='big')

        selected_packet = packet_Queue[NewAckNum - MSS]
        segment_size = selected_packet[24:]
        bitsum = selected_packet[16:18]

        print_lock.acquire()
        print("NewSeqNum =", NewAckNum, "serverChecksum =", serverChecksum, "bitsum =", bitsum)
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
            print("Corrupt ACK", NewAckNum)
            print_lock.release()
            pass
        elif NewSeqNum > expected_seq_num and NewAckNum > expected_ack_num and serverChecksum == bitsum:
            # If NewSeqNum is greater than what we expect, ACKs were lost but the data was received by the Server
            # Stop the timer for this all previous ACKs if they're still running
            print_lock.acquire()
            print("base =", base, "NewSeqNum =", NewSeqNum, "NewAckNum =", NewAckNum)
            print_lock.release()
            for close_timer in range((base - initialSeqNum) % (N * MSS), (NewAckNum - initialSeqNum) % (N * MSS), MSS):
                print("close_timer =", close_timer)
                if timer_window[close_timer].running():
                    timer_window[close_timer].stop()
                    print_lock.acquire()
                    print("Timer #", close_timer, "closed!!!!!")
                    print_lock.release()
            else:
                if timer_window[(NewAckNum - initialSeqNum) % (N * MSS)].running():
                    timer_window[(NewAckNum - initialSeqNum) % (N * MSS)].stop()
                    print_lock.acquire()
                    print("Timer #", (NewAckNum - initialSeqNum) % (N * MSS), "closedAAAAA")
                    print_lock.release()
            base_lock.acquire()
            base = (NewAckNum + len(segment_size))
            base_lock.release()
            expected_ack_num = base
            expected_seq_num = (NewSeqNum + len(segment_size))
            print_lock.acquire()
            print("base =", base)
            print("Cumulative ACK", NewAckNum, "received")
            print_lock.release()
        elif NewAckNum < expected_ack_num:
            # If NewSeqNum is less than what we're expecting, Duplicate ACK
            # continue on and stop it's timer if it's running
            if timer_window[(NewAckNum - initialSeqNum) % (N * MSS)].running():
                timer_window[(NewAckNum - initialSeqNum) % (N * MSS)].stop()
                print_lock.acquire()
                print("Timer #", (NewAckNum - initialSeqNum) % (N * MSS), "closed")
                print_lock.release()
            print_lock.acquire()
            print("Duplicate ACK", NewSeqNum, "received")
            print_lock.release()
            if dup_counter == 0:
                dup_counter += 1
                temp_ack_num = NewAckNum
            elif dup_counter == 2 and NewAckNum == temp_ack_num:
                print_lock.acquire()
                print("Fast Retransmit, resending", NewAckNum + MSS)
                print_lock.release()
                clientSocket.sendto(packet_Queue[NewAckNum + MSS], (serverName, server_port))
                if timer_window[(NewAckNum - initialSeqNum + MSS) % (N * MSS)].running():
                    timer_window[(NewAckNum - initialSeqNum + MSS) % (N * MSS)].stop()
                timer_window[(NewAckNum - initialSeqNum + MSS) % (N * MSS)].start()
            elif dup_counter == 1 and temp_ack_num == NewAckNum:
                dup_counter += 1
            else:
                dup_counter = 0
        elif NewSeqNum == expected_seq_num and NewAckNum == expected_ack_num and serverChecksum == bitsum:
            # Everything checks out, update base and expected, add ACK to dictionary, stop the timer
            if timer_window[(NewAckNum - initialSeqNum) % (N * MSS)].running():
                timer_window[(NewAckNum - initialSeqNum) % (N * MSS)].stop()
                print_lock.acquire()
                print("Timer #", (NewAckNum - initialSeqNum) % (N * MSS), "closed")
                print_lock.release()
            print_lock.acquire()
            print("Proper ACK", NewAckNum, "received")
            print_lock.release()
            base_lock.acquire()
            base += len(segment_size)
            base_lock.release()
            expected_ack_num = base
            expected_seq_num = (NewSeqNum + len(segment_size))
            print_lock.acquire()
            print("base =", base)
            print_lock.release()

        if (base - initialSeqNum) > (N * MSS):
            packet_Queue_lock.acquire()
            packet_Queue.pop((base - (N * MSS)), None)
            packet_Queue_lock.release()

        if base >= (file_size + initialSeqNum):
            # Close the file and the thread if the last ACK is received
            handshake_flag = True
            receivedAckNumber = expected_ack_num
            image.close()
            _thread.exit()


# Initial handshake set up
# *************************************************************
# take our old way of communicating and replace with a handshake set up
dest_port = 0
receivedAckNumber = int.from_bytes(receivedAckNumber, byteorder='big')
message, packet = make_header(MSS, image, initialSeqNum, clientPort, serverPort, receivedAckNumber)
clientSocket.sendto(message, (serverName, serverPort))

while True:
    modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
    # Packet's data arrives inside of variable modifiedMessage and packet's source address is inside serverAddress variable
    # serverAddress contains both the server's IP and server's port number
    # recvfrom takes the buffer size of 2048 as an input and this size is suitable for most purposes

    receivedSeqNum, receivedAckNumber, data_packet, serverChecksum, clientPort, serverPort = parser(modifiedMessage)
    receivedAckNumber = int.from_bytes(receivedAckNumber, byteorder='big')
    receivedSeqNum = int.from_bytes(receivedSeqNum, byteorder='big')
    receivedSeqNum += 1
    initialSeqNum += 1
    if receivedAckNumber == initialSeqNum and SYN == 1:
        SYN = 0
        break
    else:
        print('Ya done goooofed!!!')

message, packet = make_header(MSS, image, receivedAckNumber, clientPort, serverPort, receivedSeqNum)
send_mss = MSS.to_bytes(2, byteorder='little')
for z in send_mss:
    message.append(z)
clientSocket.sendto(message, (serverName, serverPort))
handshake_flag = False
# *************************************************************

# Beginning of the window
base = initialSeqNum
nextSeqNum = initialSeqNum

start2 = time.time()

if __name__ == "__main__":
    # Buffer the packets

    for x in range(0, N + 1):
        # Initialize a timer for each potential packet in the window
        timer_window[x * MSS] = Timer(0.05)
        print_lock.acquire()
        print("Timer #:", x * MSS, "made")
        print_lock.release()

    SeqNum = initialSeqNum
    ACKNum = receivedSeqNum

    # Start the ACK packet_cather thread
    _thread.start_new_thread(packet_catcher, (clientSocket,))

    while 1:
        while (base + ((N + 20) * MSS)) not in packet_Queue and SeqNum < (file_size + initialSeqNum):
            # Make and buffer in new packets up to 20 packets above the current window max
            sendPacket, data_length = make_packet(MSS, image, SeqNum, ACKNum)
            packet_Queue_lock.acquire()
            packet_Queue[SeqNum] = sendPacket
            packet_Queue_lock.release()

            print_lock.acquire()
            print("Segment #:", SeqNum, "made")
            print_lock.release()

            SeqNum += data_length
            ACKNum += data_length

        if nextSeqNum >= (base + (N * MSS)):
            # If the window is stuck waiting for an ACK, sleep the program for 1ms
            # to keep from looping thousands of times unnecessarily
            time.sleep(0.001)

        for x in range(base - initialSeqNum, (base - initialSeqNum) + (N * MSS), MSS):
            if x < (file_size + initialSeqNum) and timer_window[x % (N * MSS)].timeout():
                # If a timer has timed out, stop the timer (if it's still running) and resend the packet
                print_lock.acquire()
                print("Packet #", x, "timed out!")
                print("Timer #", x % (N * MSS))
                print_lock.release()
                if (x + initialSeqNum) not in packet_Queue:
                    print_lock.acquire()
                    print("Something's wrong here!")
                    print_lock.release()
                if timer_window[x % (N * MSS)].running():
                    timer_window[x % (N * MSS)].stop()
                    data_loss_test = data_loss(data_loss_rate)
                    if not data_loss_test and x < (file_size + initialSeqNum):
                        # Run the data loss function before sending
                        clientSocket.sendto(packet_Queue[x + initialSeqNum], (serverName, serverPort))
                        print_lock.acquire()
                        print("Packet #", x, "resent")
                        print("Timer #", x % (N * MSS), "started")
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
                timer_window[(nextSeqNum - initialSeqNum) % (N * MSS)].start()
                print_lock.acquire()
                print("Timer #", (nextSeqNum - initialSeqNum) % (N * MSS), "started")
                print_lock.release()
                length_of_packet = packet_Queue[nextSeqNum]
                length_of_packet = len(length_of_packet[24:])
                nextSeqNum += length_of_packet
        # We will need to change this to base >= (file_size + initial SeqNum)
        elif base >= (file_size + initialSeqNum):
            FIN = 1
            timeout_counter = 0
            final_packet, data_packet = make_header(MSS, image, SeqNum, clientPort, serverPort, receivedAckNumber)
            clientSocket.sendto(final_packet, (serverName, serverPort))
            print_lock.acquire()
            print("Final segment sent")
            print_lock.release()
            while True:
                try:
                    ackPacket, trashdata = clientSocket.recvfrom(2048)
                    print("final ack received")
                    finalSeqNum, finalAckNum, data_packet, serverChecksum, client_port, server_port = parser(ackPacket)
                    finalSeqNum = int.from_bytes(finalSeqNum, byteorder='big')
                    finalAckNum = int.from_bytes(finalAckNum, byteorder='big')
                    if finalSeqNum == receivedAckNumber:
                        # Final ACK must have been lost
                        break
                    if finalAckNum == SeqNum + 1:
                        break
                except timeout:
                    clientSocket.sendto(final_packet, (serverName, serverPort))
            while True:
                try:
                    ackPacket, trashdata = clientSocket.recvfrom(2048)
                    print("sending last ack")
                    finalSegSeqNum, finalSegAckNum, data_packet, serverChecksum, client_port, server_port = parser(ackPacket)
                    finalSegSeqNum = int.from_bytes(finalSegSeqNum, byteorder='big')
                    finalSegAckNum = int.from_bytes(finalSegAckNum, byteorder='big')
                    if finalSegSeqNum == receivedAckNumber:
                        finalSegSeqNum += 1
                        final_packet, data_packet = make_header(MSS, image, SeqNum, clientPort, serverPort, finalSegSeqNum)
                        clientSocket.sendto(final_packet, (serverName, serverPort))
                        break
                except timeout:
                    timeout_counter += 1
                    if timeout_counter == 2:
                        break
            break



end2 = start2
print("Total time for completion was %s" % (time.time() - start2))

# RRRRREEEEEEEEEEEeeeeeeeeEEEEEEEEeeeeeeEEEEEeeeEeEEeEEEEEEEEEEEEEEEEE
