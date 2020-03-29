# Phase 4
# Johnathan Saniuk, Amadeusz Piwowarczyk, Vishal Patel
# Purpose: Send a file from client to server using checksum to find errors and resend the packet if an error has occurred
# References: [1] J. Kurose and K. Ross, Computer Networking. Harlow, United Kingdom: Pearson Education Limited, 2017, pp. 159-164.
#             [2] https://stackoverflow.com/questions/10411085/converting-integer-to-binary-in-python


# Enable the creation of sockets
from socket import *
import array
import sys
import random
import time


# Define server name (or IP) and Port#
from typing import Any, Tuple

# start_time = time.time()
serverName = input('Please write your IPv4 IP here: ')
serverPort = 12000

# Create the client socket. First parameter indicates IPv4, second param indicates UDP
clientSocket = socket(AF_INET, SOCK_DGRAM)

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
SeqNum = 0b0

test_Num = 0
timeout_trig = 0
ack_error = 60

# Define a make packet function that outputs a packet and an index number
def make_packet(csize, file_name, packet_index):
    packet = file_name.read(csize)
    packet_index = packet_index + 1
    return packet, packet_index


def make_checksum(initialPacket):
    if len(initialPacket) % 2 != 0:
        initialPacket += b'\0'

    res = sum(array.array("H", initialPacket))
    res = (res >> 16) + (res & 0xffff)
    res += res >> 16

    return (~res) & 0xffff


def convert_bytes(data):
    if data == b'\x00\x00' or data == b'\x00' or data == 0:
        data = 0b0
    elif data == b'\x01\x00' or data == b'\x01' or data == b'\x00\x01' or data == 1:
        data = 0b1
    return data


def Timeout(test_Num):
    # Select a random int btwn 0 and 100
    randNum = random.randrange(0, 100)
    # if randNum is less than the specified error rate, flip the bit
    if randNum < test_Num:
         test_Num = 0
    elif randNum > test_Num:
        test_Num = 1
    return test_Num


def ack_corrupt(sequence):
    # Select a random int btwn 0 and 100
    randNum = random.randrange(0, 100)
    # if randNum is less than the specified error rate, flip the bit
    if randNum < ack_error:
        if sequence == 0:
            sequence = 0b1
        elif sequence == 1:
            sequence = 0b0
    return sequence


def drop_ack(drop_ACK):
    # Select a random int btwn 0 and 100
    randdrop = random.randrange(0, 100)
    if randdrop < drop_ACK:
        drop_ACK = 0
        pass
    elif randdrop >= drop_ACK:
        drop_ACK = 1
    return drop_ACK


while 1:
    sendPacket = bytearray()
    # sendPacket = sendPacket.to_bytes(2, byteorder='little')
    # create a packet and save it to the initialPacket variable, along with an index# to track it
    initialPacket, packetIndex = make_packet(packet_size, image, packetIndex)
    # print("initialPacket:", initialPacket)
    # print("initialPacket length:", len(initialPacket))

    checksum = make_checksum(initialPacket)
    bitsum = checksum.to_bytes(2, byteorder='little')

    SeqNum = convert_bytes(SeqNum)
    sendPacket.append(SeqNum)
    for i in bitsum:
        sendPacket.append(i)
    for j in initialPacket:
        sendPacket.append(j)

    if len(initialPacket) < 1024:

        clientSocket.sendto(sendPacket, (serverName, serverPort))
        print("Packet #", packetIndex, "sent")

        start = time.time()

        while 1:
            Timeout = Timeout(test_Num)
            if Timeout == 1:
                pass
            elif Timeout == 0:
                time.sleep(0.07)

            if time.time() <= (start + 0.05):
                end = start
                print('Packet sent without timeout................')
                # wait for server to respond with the sequence number (ACK)
                NewSeqNum, trashData = clientSocket.recvfrom(2048)
            elif time.time() > (start + 0.05):
                end = start
                print('Packet was timed out!!!!!!!!!!!!!!!!!!!!!!!!')
                # wait for server to respond with the sequence number (ACK)
                NewSeqNum, trashData = clientSocket.recvfrom(2048)

            NewSeqNum = convert_bytes(NewSeqNum)
            SeqNum = convert_bytes(SeqNum)

            print("NewSeqNum:", NewSeqNum)
            NewSeqNum = ack_corrupt(NewSeqNum)
            print("NewSeqNum Post Error:", NewSeqNum)
            # if the same sequence number is received, we have the wrong ACK
            if NewSeqNum == SeqNum:
                # Resend the packet
                clientSocket.sendto(sendPacket, (serverName, serverPort))
                print("Packet #", packetIndex, "resent")
            # if a different sequence number is received, we have the right ACK
            elif NewSeqNum != SeqNum:
                # Since it's the last packet, close the file and break
                SeqNum = NewSeqNum
                image.close()
                break
            else:
                # do nothing
                pass
        break
    # If the packet is 1024 bytes in length, send the packet to the server and print a confirmation message
    elif len(initialPacket) == 1024:
        clientSocket.sendto(sendPacket, (serverName, serverPort))
        print("Packet #", packetIndex, "sent")

        start = time.time()

        while 1:
            Timeout2 = Timeout(test_Num)
            if Timeout2 == 1:
                pass
            elif Timeout2 == 0:
                time.sleep(0.07)

            if time.time() <= (start + 0.05):
                end = start
                print('Packet sent without timeout................')
                # wait for server to respond with the sequence number (ACK)
                NewSeqNum, trashData = clientSocket.recvfrom(2048)
            elif time.time() > (start + 0.05):
                end = start
                print('Packet was timed out!!!!!!!!!!!!!!!!!!!!!!!!')
                # wait for server to respond with the sequence number (ACK)
                NewSeqNum, trashData = clientSocket.recvfrom(2048)

            NewSeqNum = convert_bytes(NewSeqNum)
            SeqNum = convert_bytes(SeqNum)

            print("NewSeqNum:", NewSeqNum)
            NewSeqNum = ack_corrupt(NewSeqNum)
            print("NewSeqNum Post Error:", NewSeqNum)
            print("Old SeqNum:", SeqNum)
            if NewSeqNum == SeqNum:
                # if the same sequence number is received, resend the packet
                clientSocket.sendto(sendPacket, (serverName, serverPort))
                print("Packet #", packetIndex, "resent")
            elif NewSeqNum != SeqNum:
                # if a different sequence number is received, move on to the next packet
                SeqNum = NewSeqNum
                break
            else:
                # do nothing
                pass
    # If the initial packet length is 0, the last packet was exactly 1024 bits. Close the image and break the loop
    elif len(initialPacket) == 0:
        image.close()
        break
