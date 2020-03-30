# Phase 4
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
OldSeqNum = b'\x00'
SeqNum = 0
file = open(FileName, 'wb')
print("Ready to download file ...")
ackPacket = bytearray()
recvPacket = bytearray()

dat_error = 0
ack_loss_rate = 0


def make_checksum(packet):
    if len(packet) % 2 != 0:
        packet += b'\0'

    res = sum(array.array("H", packet))
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
        # indicates loss
         test_Num = 1
    elif randNum > test_Num:
        # indicates no loss
        test_Num = 0
    return test_Num


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


state = 0

while 1:
    if state == 0:
        ackPacket = bytearray()
        recvPacket, clientAddress = serverSocket.recvfrom(2048)
        # When the packet arrives at the server's socket, it gets stored in the variable message.
        # The message set up is like in the Client code. But the UDPServer will make use of this since
        # it includes the return address and information from the client and now server knows where it should reply to

        SeqNum = recvPacket[:1]
        SeqNum = convert_bytes(SeqNum)
        clientChecksum = recvPacket[1:3]
        dataPacket = recvPacket[3:]

        # Simulate possible data corruption
        dataPacket = data_error(dataPacket)
        # Make a checksum out of received data (post corruption simulation)
        serverChecksum = make_checksum(dataPacket)
        # Convert Server-side checksum into bytes
        sbitsum = serverChecksum.to_bytes(2, byteorder='little')

        # If checksums different, there was data error
        if sbitsum != clientChecksum or SeqNum != 0:
            # Resend the same sequence number back to the Client. This signals a NACK
            ackPacket.append(1)
            for i in sbitsum:
                ackPacket.append(i)
            serverSocket.sendto(ackPacket, clientAddress)
            state = 0
        elif sbitsum == clientChecksum and SeqNum == 0:
            ackPacket.append(0)
            for i in sbitsum:
                ackPacket.append(i)
            if Timeout(ack_loss_rate) == 0:
                serverSocket.sendto(ackPacket, clientAddress)
                if indexNumber > 0:
                    file.write(writeDataPacket)
                    print("Packet #", indexNumber, "Downloaded")

                state = 1
                writeDataPacket = dataPacket
                indexNumber += 1

                if len(dataPacket) < 1024:
                    file.write(dataPacket)
                    print("Packet #", indexNumber, "Downloaded")
                    # Close the file
                    file.close()
                    break
            elif Timeout(ack_loss_rate) == 1:
                print("ACK lost")
                state = 0

    if state == 1:
        ackPacket = bytearray()
        recvPacket, clientAddress = serverSocket.recvfrom(2048)
        # When the packet arrives at the server's socket, it gets stored in the variable message.
        # The message set up is like in the Client code. But the UDPServer will make use of this since
        # it includes the return address and information from the client and now server knows where it should reply to

        SeqNum = recvPacket[:1]
        SeqNum = convert_bytes(SeqNum)
        clientChecksum = recvPacket[1:3]
        dataPacket = recvPacket[3:]

        # Simulate possible data corruption
        dataPacket = data_error(dataPacket)
        # Make a checksum out of received data (post corruption simulation)
        serverChecksum = make_checksum(dataPacket)
        # Convert Server-side checksum into bytes
        sbitsum = serverChecksum.to_bytes(2, byteorder='little')

        # If checksums different, there was data error
        if sbitsum != clientChecksum or SeqNum != 1:
            # Resend the same sequence number back to the Client. This signals a NACK
            ackPacket.append(0)
            for i in clientChecksum:
                ackPacket.append(i)
            serverSocket.sendto(ackPacket, clientAddress)
            state = 1
        elif sbitsum == clientChecksum and SeqNum == 1:
            ackPacket.append(1)
            for i in sbitsum:
                ackPacket.append(i)
            serverSocket.sendto(ackPacket, clientAddress)

            if indexNumber > 0:
                file.write(writeDataPacket)
                print("Packet #", indexNumber, "Downloaded")

            state = 0
            writeDataPacket = dataPacket
            indexNumber += 1

            if len(dataPacket) < 1024:
                file.write(dataPacket)
                print("Packet #", indexNumber, "Downloaded")
                # Close the file
                file.close()
                break

end_time = start_time
print("Total time for completion was %s" % (time.time() - start_time))
