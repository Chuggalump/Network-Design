# Phase 6
# Johnathan Saniuk, Amadeusz Piwowarczyk, Vishal Patel
# Purpose: Receive an image packet by packet and put it into a new file called Picture.bmp
# References: [1] J. Kurose and K. Ross, Computer Networking. Harlow, United Kingdom: Pearson Education Limited, 2017, pp. 159-164.


# Enable the creation of sockets
from socket import *
import array
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
FileName = input('File name followed by ".filetype": ')

print("\nEnter Error/Loss below. If no Error/Loss, enter a '0' ")

# Ask user to input Eror/Loss simulation for packet transfer
dat_error = int(input('Enter Data Error percent for packet transfer: '))
ack_loss_rate = int(input('Enter ACK Loss percent for packet transfer: '))

print("\nReady to download file ...")

print("\nWaiting for client to send packets . . . .\n")

message2 = "Sender is ready to receive packets . . ."  # tell server that you are ready to receive file transfer
serverSocket.sendto(message2.encode(), clientAddress)

# ***********************

SNumber = 0
file = open(FileName, 'wb')
ackPacket = bytearray()
recvPacket = bytearray()
final_handshake = False
# Base of the buffering Dictionary
base = 0

final_packet = 0

received_Queue = {}


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
    if rand_num < test_num:
        # Packet is "lost". Simulate by not sending the ACK back to the client
        #print("ACK lost")
        pass
    else:
        # ACK packet isn't lost, send the ACK
        serverSocket.sendto(ackPacket, clientAddress)
        #print("ACK Sent")


def data_error(data):
    # Select a random int btwn 0 and 100
    randNum = random.randrange(0, 100)
    # if randNum is less than the specified error rate,
    if randNum < dat_error:
        corrupted_data = bytearray()
        # Throw some simple corruptor bits in here. Any 0's in the data will become 1's where there is a 1
        corruption = data[1022:]
        not_corrupt = data[:1022]
        corrupt = int.from_bytes(corruption, byteorder='little', signed=False)
        corrupt = corrupt | 0b1111111111111111
        corrupt = corrupt.to_bytes(2, byteorder='little')
        for i in not_corrupt:
            corrupted_data.append(i)
        for j in corrupt:
            corrupted_data.append(j)
        return corrupted_data
    else:
        return data


def parser(rec_pack):
    # Parse data
    seq_num = rec_pack[:2]
    client_checksum = rec_pack[2:4]
    data_packet = rec_pack[4:]

    # Simulate possible data corruption
    data_packet = data_error(data_packet)
    # Make a checksum out of received data (post corruption simulation)
    server_checksum = make_checksum(data_packet)
    # Convert Server-side checksum into bytes
    sbit_sum = server_checksum.to_bytes(2, byteorder='little')

    # Clear the ack_packet
    ack_packet = bytearray()
    # Append the ACK to the packet
    ack_packet.extend(seq_num)
    seq_num = int.from_bytes(seq_num, byteorder='big')
    #print('Packet received. Received SeqNum is:', seq_num)
    for i in sbit_sum:
        ack_packet.append(i)

    return seq_num, client_checksum, data_packet, sbit_sum, ack_packet


start_time = time.time()

while 1:
    if not final_handshake:
        # Wait for the packet to come from the client
        recvPacket, clientAddress = serverSocket.recvfrom(2048)

        SeqNum, clientChecksum, dataPacket, sbitsum, ackPacket = parser(recvPacket)

        # If checksums the same and SeqNum is what we expect, everything is right with the world
        if sbitsum == clientChecksum and SeqNum == SNumber:
            # Send the ACK packet back to sender, calculating if there's loss or not
            ack_loss(ack_loss_rate)

            # SeqNum is correct, buffer data to the Queue
            received_Queue[SeqNum] = dataPacket

            # Download the data for all in order packets
            while SNumber in received_Queue:
                file.write(received_Queue[SNumber])
                #print("Packet #", SNumber, "Downloaded")
                SNumber += 1
                #print('Updated SeqNum is: ', SNumber)
                # Clear out old unneeded data in the buffer
                received_Queue.pop((SNumber - 20), None)

            # If last packet
            if len(dataPacket) < 1024:
                final_packet = SNumber

            # If final_packet flag is = to SNumber, we're really on the final packet. Trigger the final handshake
            if final_packet == SNumber:
                final_handshake = True

        # If packet is good but out of order
        elif sbitsum == clientChecksum and SeqNum > SNumber:
            # Send the ACK packet back to sender, calculating if there's loss or not
            ack_loss(ack_loss_rate)
            # SeqNum is out of order but still good, buffer data to the Queue
            received_Queue[SeqNum] = dataPacket
            # If last packet, close the file
            if len(dataPacket) < 1024:
                final_packet = SeqNum + 1
        # If packet is a duplicate
        elif SeqNum < SNumber:
            # Send the ACK packet back to sender, calculating if there's loss or not
            ack_loss(ack_loss_rate)
        else:
            # Checksum fail, drop packet and do nothing
            pass
    else:
        # We've entered the final handshake, wait to receive the last confirmation packet from the sender.
        recvPacket, clientAddress = serverSocket.recvfrom(2048)

        SeqNum, clientChecksum, dataPacket, sbitsum, ackPacket = parser(recvPacket)
        if SeqNum == SNumber:
            # Once the proper packet is received, send back the last ACK and leave
            file.close()
            break
        else:
            # If we get back something other than the final packet, send back an ACK with that sequence number
            # until we get the packet we're looking for
            ack_loss(ack_loss_rate)


end_time = start_time
print("Total time for completion was %s" % (time.time() - start_time))
