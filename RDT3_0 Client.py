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
import threading

# Define server name (or IP) and Port#
from typing import Any, Tuple

# start_time = time.time()
serverName = '192.168.1.105'  # input('Please write your IPv4 IP here: ')
'''   '192.168.1.239'   '''
'''   '192.168.1.105'   '''
serverPort = 12000

# Create the client socket. First parameter indicates IPv4, second param indicates UDP
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(0.5)

# *********************** Send client a question to know when files are ready to be sent over
message = ('Enter File Name to transfer file!')
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
FileName = 'picture.bmp'  # input('Write the file name you wish to send: ')
image = open(FileName, 'rb')

# Set the packet size and create an index to count packets
packet_size = 1024
packetIndex = 0
print("packet size is: ", packet_size)

# Variable to add the Sequence Number to each packet
SeqNum = b'\x00\x00'
# Variable to track the expected Sequence Number we receive from the Server
expectedSeqNum = b'\x00\x00'
global sendPacket
sendPacket = bytearray()
initialPacket = bytearray()
bitsum = 0
# Variable to track which packet in the queue we're on
nextSeqNum = 0
# Create an empty dictionary to store the sent but unacked packets
packet_Queue = {}
# Define Window Size (1 to N)
N = 9
# Beginning of the window
base = 0
# Check to see if the last packet was made
global endQueue
endQueue = False

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
    send_Packet = bytearray()
    send_Packet.extend(seq_num)
    seq_num = int.from_bytes(seq_num, byteorder='big')
    seq_num += 1
    seq_num = seq_num.to_bytes(2, byteorder='big')

    for i in bit_sum:
        send_Packet.append(i)
    for j in packet:
        send_Packet.append(j)

    return send_Packet, seq_num


def convert_bytes(data):
    if data == b'\x00\x00' or data == b'\x00' or data == 0:
        data = 0b0
    elif data == b'\x01\x00' or data == b'\x01' or data == b'\x00\x01' or data == 1:
        data = 0b1
    return data


def data_loss(test_Num):
    # Select a random int btwn 0 and 100
    # random.seed()
    randNum = random.randrange(0, 100)
    # if randNum is less than the specified error rate, flip the bit
    if randNum < test_Num:
        test_Num = 1
    elif randNum > test_Num:
        test_Num = 0
    return test_Num


def ack_corrupt(sequence):
    # Select a random int btwn 0 and 100
    randNum = random.randrange(0, 100)
    # if randNum is less than the specified error rate, flip the bit
    if randNum < ack_error:
        sequence = sequence & 0xffff
    return sequence


def ack_received(send_Packet, expect):
    for i in packet_Queue:
        if i == (len(packet_Queue) - 1):
            packet_Queue[i] = send_Packet
            expect = int.from_bytes(expect, byteorder='big')
            expect += 1
            expect = expect.to_bytes(2, byteorder='big')
            # clientSocket.sendto(packet_Queue[i], (serverName, serverPort))
            # print("packet_Queue[", i, "] sent")
            break
        packet_Queue[i] = packet_Queue[i + 1]

    return expect


def clear_queue(expect):
    for i in packet_Queue:
        if len(packet_Queue) == 0:
            image.close()
            break
        if i == (len(packet_Queue) - 1):
            del packet_Queue[i]
            expect = int.from_bytes(expect, byteorder='big')
            expect += 1
            expect = expect.to_bytes(2, byteorder='big')
            # clientSocket.sendto(packet_Queue[i], (serverName, serverPort))
            # print("packet_Queue[", i, "] sent")
            break
        packet_Queue[i] = packet_Queue[i + 1]

    return expect


def packet_shooter(packet_index, next_seq_num):
    if_loss0 = data_loss(data_loss_rate)
    # Implement random data loss
    if if_loss0 == 1:
        # If if_loss0 is 1, the packet is "lost" en route to the server. Simulate by not sending the packet
        # ackTimer.start()
        print(packet_index, "Data was lost!")
        # state = 1
    else:
        # Else, no data loss. Send the packet
        clientSocket.sendto(packet_Queue[0], (serverName, serverPort))
        # ackTimer.start()
        print("Packet #", packet_index, "sent")
        packet_index += 1
        next_seq_num += 1
        # state = 1


def packet_catcher(expected_seq_num, seq_num, next_seq_num, base, end_queue, last_packet):
    while 1:
        # Try to receive the ACK packet from server. If not received in 50ms, timeout and resend the packet
        try:
            bitsum = packet_Queue[0]
            bitsum = bitsum[2:4]

            # trasdata is the address sent with the ACK. We don't need it
            ackPacket, trashdata = clientSocket.recvfrom(2048)

            # Parse the data
            NewSeqNum = ackPacket[:2]
            serverChecksum = ackPacket[2:]

            NewSeqNum = ack_corrupt(NewSeqNum)

            print("Line 187 NewSeqNum is ", NewSeqNum)

            # if a different sequence number is received or checksum is bad resend the packet
            if NewSeqNum != expected_seq_num or serverChecksum != bitsum:
                # Resend the packet
                clientSocket.sendto(packet_Queue[packetIndex - base], (serverName, serverPort))
                print("Packet #", packetIndex, "resent")
                # Loop back to beginning of state to wait for the proper ACK
                # state = 1
            # if the same sequence number is received, we have the right ACK
            elif NewSeqNum == expected_seq_num and serverChecksum == bitsum:
                # set next state
                base += 1
                # state = 0
                if len(last_packet) < 1028:
                    # If the dat is less than 1024 bytes we're on the last packet. Close the file and break
                    end_queue = True
                if not end_queue:
                    last_packet, seq_num = make_packet(packet_size, image, seq_num)
                    expected_seq_num = ack_received(last_packet, expected_seq_num)
                elif end_queue:
                    expected_seq_num = clear_queue(expected_seq_num)

                if len(packet_Queue) == 0:
                    break

        except timeout:
            # If timeout occurs, print a statement and resend the same packet
            print("Packet Timed Out!")
            if_loss1 = data_loss(data_loss_rate)
            # Implement random data loss
            if if_loss1 == 1:
                # If if_loss1 is 1, the packet is "lost" en route to the server. Simulate by not sending the packet
                print(packetIndex, "Data was lost")
                # state = 1
            else:
                # Else, no data loss. Send the packet
                clientSocket.sendto(packet_Queue[0], (serverName, serverPort))
                print("Packet #", packetIndex, "resent")
                next_seq_num += 1
                # state = 1


def timeout():
    for i in packet_Queue:
        clientSocket.sendto(packet_Queue[i], (serverName, serverPort))


ackTimer = Timer(0.5, timeout)

state = 0

start2 = time.time()


if __name__ == "__main__":
    # Buffer the packets
    for x in range(0, 9):
        sendPacket, SeqNum = make_packet(packet_size, image, SeqNum)
        packet_Queue[x] = sendPacket

    # creating the threads needed to send and receive
    t1 = threading.Thread(target=packet_shooter(packetIndex, nextSeqNum))
    t2 = threading.Thread(target=packet_catcher(expectedSeqNum, SeqNum, nextSeqNum, base, endQueue, sendPacket))

    # starting thread 1
    t1.start()
    # starting thread 2
    t2.start()

    # wait for threads to completely execute
    t1.join()
    t2.join()


end2 = start2
print("Total time for completion was %s" % (time.time() - start2))

# RRRRREEEEEEEEEEEeeeeeeeeEEEEEEEEeeeeeeEEEEEeeeEeEEeEEEEEEEEEEEEEEEEE
