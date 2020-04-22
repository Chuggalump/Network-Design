# Phase 5
# Johnathan Saniuk, Amadeusz Piwowarczyk, Vishal Patel
# Purpose: Receive an image packet by packet and put it into a new file called Picture.bmp
# References: [1] J. Kurose and K. Ross, Computer Networking. Harlow, United Kingdom: Pearson Education Limited, 2017, pp. 159-164.


# Enable the creation of sockets
from socket import *
import array
import sys
import random
import time

# Wait for server to define server Port#
serverPort = 12000

# Create the client socket. First parameter indicates IPv4, second param indicates UDP
serverSocket = socket(AF_INET, SOCK_DGRAM)

# Bind the server's socket to the port# 12000
serverSocket.bind(("", serverPort))
# UDPServer assigns port number. When a packet is sent to the server, the packet will be directed to this socket
# UDPServer then enters a loop to receive packets indefinitely from the clients and process the packets from clients
# In the loop, the server waits for packets to arrive


# ************** Receive starter message that tells client when server is accepting file transfer
message, clientAddress = serverSocket.recvfrom(2048)
# Receive packet from client just to have the return info to reply to the client

modifiedMessage = message.decode().upper()
# Takes message from client after converting it to a string and uses upper() to capitalize it

print(modifiedMessage)  # Print received message to server's command line

# PauseInput = input('Press Enter to Continue:')
FileName = 'Pic.bmp'#input('File followed by ".filetype": ')

message2 = "Ready to receive file"  # tell server that you are ready to receive file transfer
serverSocket.sendto(message2.encode(), clientAddress)
start_time = time.time()

# ***********************

x = False
indexNumber = 0
writeDataPacket = 0
SNumber = b'\x00\x00'
oldSeqNum = SNumber
file = open(FileName, 'wb')
print("Ready to download file ...")
ackPacket = bytearray()
recvPacket = bytearray()
final_handshake = False

dat_error = 10
ack_loss_rate = 10


def make_checksum(packet):
    if len(packet) % 2 != 0:
        packet += b'\0'

    res = sum(array.array("H", packet))
    res = (res >> 16) + (res & 0xffff)
    res += res >> 16

    return (~res) & 0xffff


def ack_loss(test_num):
    # Select a random int btwn 0 and 100
    rand_num = random.randrange(0, 100)
    # if randNum is less than the specified error rate, flip the bit
    if rand_num < test_num:
        # indicates loss
        test_num = True
    elif rand_num > test_num:
        # indicates no loss
        test_num = False
    return test_num


def data_error(data):
    # Select a random int btwn 0 and 100
    randNum = random.randrange(0, 100)
    # if randNum is less than the specified error rate,
    if randNum < dat_error:
        corrupted_data = bytearray()
        #Throw some simple corruptor bits in here. Any 0's in the data will become 1's where there is a 1
        corruption = data[1022:]
        not_corrupt = data[:1022]
        corrupt = int.from_bytes(corruption, byteorder='little', signed=False)
        corrupt = corrupt | 0b1111111111111111
        corrupt = corrupt.to_bytes(2, byteorder='little')
        for i in not_corrupt:
            corrupted_data.append(i)
        for j in corrupt:
            corrupted_data.append(j)
        print("corrupted_data length", len(corrupted_data))
        return corrupted_data
    else:
        return data


while 1:

    if not final_handshake:
        # Wait for the packet to come from the client
        recvPacket, clientAddress = serverSocket.recvfrom(2048)

        # Parse data
        SeqNum = recvPacket[:2]
        print('Packet received. Received SeqNum is: ', SeqNum)
        clientChecksum = recvPacket[2:4]
        dataPacket = recvPacket[4:]

        # Simulate possible data corruption
        dataPacket = data_error(dataPacket)
        # Make a checksum out of received data (post corruption simulation)
        serverChecksum = make_checksum(dataPacket)
        # Convert Server-side checksum into bytes
        sbitsum = serverChecksum.to_bytes(2, byteorder='little')

        # If checksums the same and SeqNum = 0, everything is right with the world
        if sbitsum == clientChecksum and SeqNum == SNumber:
            ackPacket = bytearray()
            # Append the ACK to the packet
            ackPacket.extend(SNumber)
            print("Send packet after Seq Num =", ackPacket)

            for i in sbitsum:
                ackPacket.append(i)

            # Implement random ACK Packet loss
            if not ack_loss(ack_loss_rate):
                # If ack_loss is False, ACK packet isn't lost
                serverSocket.sendto(ackPacket, clientAddress)
                print("ACK Sent")
            else:
                # If ack_loss is True, packet is "lost". Simulate by not sending the ACK back to the client
                print("ACK lost")

            # Write the dataPacket received to the file
            file.write(dataPacket)
            print("Packet #", indexNumber, "Downloaded")

            SNumber = int.from_bytes(SNumber, byteorder='big')
            print("Previous SeqNum was:", SNumber)
            SNumber += 1
            SNumber = SNumber.to_bytes(2, byteorder='big')
            print('Updated SeqNum is: ', SNumber)
            indexNumber += 1

            # If last packet, close the file
            if len(dataPacket) < 1024:
                final_handshake = True

        # If checksums different, there was data error, if SeqNum is 1 then there's ACK error
        else:
            serverSocket.sendto(ackPacket, clientAddress)
    else:
        recvPacket, clientAddress = serverSocket.recvfrom(2048)
        SeqNum = recvPacket[:2]
        if SeqNum == SNumber:
            file.close()
            break
        else:
            serverSocket.sendto(ackPacket, clientAddress)

end_time = start_time
print("Total time for completion was %s" % (time.time() - start_time))
