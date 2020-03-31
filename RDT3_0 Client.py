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
import select


# Define server name (or IP) and Port#
from typing import Any, Tuple

# start_time = time.time()
serverName = input('Please write your IPv4 IP here: ')
serverPort = 12000

# Create the client socket. First parameter indicates IPv4, second param indicates UDP
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(0.05)

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
SeqNum0 = 0b0
SeqNum1 = 0b1
sendPacket = bytearray()
initialPacket = bytearray()

ack_error = 0
data_loss_rate = 15


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
    #random.seed()
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
        if sequence == 0:
            sequence = 0b1
        elif sequence == 1:
            sequence = 0b0
    return sequence


state = 0

start2 = time.time()

while 1:
    if state == 0:
        # State: wait for call 0 from above
        sendPacket = bytearray()
        # create a packet and save it to the initialPacket variable, along with an index# to track it
        initialPacket, packetIndex = make_packet(packet_size, image, packetIndex)

        # Make the checksum and convert it to bytes so it can be appended to the packet
        checksum = make_checksum(initialPacket)
        bitsum = checksum.to_bytes(2, byteorder='little')

        # Create the sendPacket by appending sequence number, checksum, and data
        sendPacket.append(SeqNum0)
        for i in bitsum:
            sendPacket.append(i)
        for j in initialPacket:
            sendPacket.append(j)

        if_loss0 = Timeout(data_loss_rate)
        # Implement random data loss
        if if_loss0 == 1:
            # If if_loss0 is 1, the packet is "lost" en route to the server. Simulate by not sending the packet
            print(packetIndex, "Data was lostAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
            state = 1
        else:
            # Else, no data loss. Send the packet
            clientSocket.sendto(sendPacket, (serverName, serverPort))
            print("Packet #", packetIndex, "sent")
            state = 1

    elif state == 1:
        # State: wait for ACK 0
        # Try to receive the ACK packet from server. If not received in 50ms, timeout and resend the packet
        try:
            # Start a timer to track how long it took to receive the ACK packet
            startTime = time.time()
            ackPacket, trashdata = clientSocket.recvfrom(2048)      #trasdata is the address sent with the ACK. We don't need it
            recvTime = time.time()
            # Parse the data
            NewSeqNum = ackPacket[:1]
            serverChecksum = ackPacket[1:]

            # Ensure the NewSeqNum is in int form so it can be properly compared below
            NewSeqNum = convert_bytes(NewSeqNum)

            NewSeqNum = ack_corrupt(NewSeqNum)

            # if a different sequence number is received or checksum is bad resend the packet
            if NewSeqNum != SeqNum0 or serverChecksum != bitsum:
                # Sleep for the remaining time till timeout to ensure client and server are still in sync
                remain = 0.05 - (recvTime - startTime)
                time.sleep(remain)
                # Resend the packet
                clientSocket.sendto(sendPacket, (serverName, serverPort))
                print("Packet #", packetIndex, "resent")
                # Loop back to beginning of state to wait for the proper ACK
                state = 1
            # if the same sequence number is received, we have the right ACK
            elif NewSeqNum == SeqNum0 and serverChecksum == bitsum:
                # set next state
                state = 2
                if len(initialPacket) < 1024:
                    # If the dat is less than 1024 bytes we're on the last packet. Close the file and break
                    image.close()
                    break
        except timeout:
            # If timeout occurs, print a statement and resend the same packet
            print("Packet Timed Out!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            if_loss1 = Timeout(data_loss_rate)
            # Implement random data loss
            if if_loss1 == 1:
                # If if_loss1 is 1, the packet is "lost" en route to the server. Simulate by not sending the packet
                print(packetIndex, "Data was lostBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB")
                state = 1
            else:
                # Else, no data loss. Send the packet
                clientSocket.sendto(sendPacket, (serverName, serverPort))
                print("Packet #", packetIndex, "sent")
                state = 1

    elif state == 2:
        # State: wait for call 1 from above
        sendPacket = bytearray()
        # create a packet and save it to the initialPacket variable, along with an index# to track it
        initialPacket, packetIndex = make_packet(packet_size, image, packetIndex)

        # Make the checksum and convert it to bytes so it can be appended to the packet
        checksum = make_checksum(initialPacket)
        bitsum = checksum.to_bytes(2, byteorder='little')

        # Create the sendPacket by appending sequence number, checksum, and data
        sendPacket.append(SeqNum1)
        for i in bitsum:
            sendPacket.append(i)
        for j in initialPacket:
            sendPacket.append(j)

        # Implement random data loss
        if_loss2 = Timeout(data_loss_rate)
        if if_loss2 == 1:
            # If if_loss2 is 1, the packet is "lost" en route to the server. Simulate by not sending the packet
            print(packetIndex, "Data was lostCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC")
            state = 3
        else:
            # Else, no data loss. Send the packet
            clientSocket.sendto(sendPacket, (serverName, serverPort))
            print("Packet #", packetIndex, "sent")
            state = 3

    elif state == 3:
        # State: wait for ACK 1
        # Try to receive the ACK packet from server. If not received in 50ms, timeout and resend the packet
        try:
            # Start a timer to track how long it took to receive the ACK packet
            startTime = time.time()
            ackPacket, trashdata = clientSocket.recvfrom(2048)
            recvTime = time.time()
            # Parse the data
            NewSeqNum = ackPacket[:1]
            serverChecksum = ackPacket[1:]

            # Ensure the NewSeqNum is in int form so it can be properly compared below
            NewSeqNum = convert_bytes(NewSeqNum)

            NewSeqNum = ack_corrupt(NewSeqNum)

            # if a different sequence number is received, we have the wrong ACK
            if NewSeqNum != SeqNum1 or serverChecksum != bitsum:
                # Sleep for the remaining time till timeout to ensure client and server are still in sync
                remain = 0.05 - (recvTime - startTime)
                time.sleep(remain)
                # Resend the packet
                clientSocket.sendto(sendPacket, (serverName, serverPort))
                print("Packet #", packetIndex, "resent")
                # Loop back to beginning of state to wait for the proper ACK
                state = 3
            # if the same sequence number is received, we have the right ACK
            elif NewSeqNum == SeqNum1 and serverChecksum == bitsum:
                # set next state
                state = 0
                if len(initialPacket) < 1024:
                    # If the dat is less than 1024 bytes we're on the last packet. Close the file and break
                    image.close()
                    break
        except timeout:
            # If timeout occurs, print a statement and resend the same packet
            print("Packet Timed Out!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            # Implement random data loss
            if_loss3 = Timeout(data_loss_rate)
            if if_loss3 == 1:
                # If if_loss3 is 1, the packet is "lost" en route to the server. Simulate by not sending the packet
                print(packetIndex, "Data was lostDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD")
                state = 3
            else:
                # Else, no data loss. Send the packet
                clientSocket.sendto(sendPacket, (serverName, serverPort))
                print("Packet #", packetIndex, "sent")
                state = 3

end2 = start2
print("Total time for completion was %s" % (time.time() - start2))
