# Phase 6 TCP
# Johnathan Saniuk, Amadeusz Piwowarczyk, Vishal Patel
# Purpose: Receive an image packet by packet and put it into a new file called Picture.bmp
# References: [1] J. Kurose and K. Ross, Computer Networking. Harlow, United Kingdom: Pearson Education Limited, 2017, pp. 159-164.


# Enable the creation of sockets
from socket import *
import array
import random
import time
import _thread
from Timer_Class import Timer

# Wait for server to define server Port#
serverPort = 12000

# Create the client socket. First parameter indicates IPv4, second param indicates UDP
serverSocket = socket(AF_INET, SOCK_DGRAM)

# Bind the server's socket to the port# 12000
serverSocket.bind(("", serverPort))
# UDPServer assigns port number. When a packet is sent to the server, the packet will be directed to this socket
# UDPServer then enters a loop to receive packets indefinitely from the clients and process the packets from clients
# In the loop, the server waits for packets to arrive

# PauseInput = input('Press Enter to Continue:')
FileName = 'Pic.bmp'    # input('File name followed by ".filetype": ')

# print("\nEnter Error/Loss below. If no Error/Loss, enter a '0' ")

# Ask user to input Eror/Loss simulation for packet transfer
dat_error = 0    # int(input('Enter Data Error percent for packet transfer: '))
ack_loss_rate = 0    # int(input('Enter ACK Loss percent for packet transfer: '))


# print("\nReady to download file ...")

# print("\nWaiting for client to send packets . . . .\n")
'''
message2 = "Sender is ready to receive packets . . ."  # tell server that you are ready to receive file transfer
serverSocket.sendto(message2.encode(), clientAddress)
'''
# ***********************

# Globals
MSS = 1024
expectedSeqNum = 0
old_expectedAckNumber = 0
receivedSeqNum = 0
updatedSeqNum = 0
receivedAckNumber = 0
expectedAckNumber = 0
generatedACKNumber = 0
currentAckNumber = 0
SYN = 0
FIN = 0
ACK_valid = 0
final_handshake = False

receive_timer = Timer(0.5)

file = open(FileName, 'wb')
ackPacket = bytearray()
recvPacket = bytearray()

final_packet = 0

received_Queue = {}


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


def make_checksum(packet):
    if len(packet) % 2 != 0:
        packet += b'\0'

    res = sum(array.array("H", packet))
    res = (res >> 16) + (res & 0xffff)
    res += res >> 16

    return (~res) & 0xffff


def ack_loss(test_num, ack_packet):
    # Select a random int btwn 0 and 100
    rand_num = random.randrange(0, 100)
    if rand_num < test_num:
        # Packet is "lost". Simulate by not sending the ACK back to the client
        print("ACK lost")
        pass
    else:
        # ACK packet isn't lost, send the ACK
        serverSocket.sendto(ack_packet, clientAddress)
        print("ACK Sent")


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
        print("Corrupted Data")
        return corrupted_data
    else:
        return data


def parser(rec_pack):
    global SYN
    global FIN
    global ACK_valid
    # Parse data from TCP Segment
    client_port = rec_pack[:2]
    server_port = rec_pack[2:4]
    seq_num = rec_pack[4:8]
    Header_N_unused = rec_pack[12:13]
    Header_Bit_setting = rec_pack[13:14]
    Header_Bit_setting = int.from_bytes(Header_Bit_setting, byteorder='little')
    CWR = (Header_Bit_setting >> 7) & 0x01
    ECE = (Header_Bit_setting >> 6) & 0x01
    Urgent = (Header_Bit_setting >> 5) & 0x01
    ACK_valid = (Header_Bit_setting >> 4) & 0x01
    print("ACK_valid =", ACK_valid)
    Push_data = (Header_Bit_setting >> 3) & 0x01
    RST = (Header_Bit_setting >> 2) & 0x01
    SYN = (Header_Bit_setting >> 1) & 0x01
    FIN = (Header_Bit_setting >> 0) & 0x01
    Rec_Window = rec_pack[14:16]
    client_checksum = rec_pack[16:18]
    Urgent_data = rec_pack[18:20]
    Options = rec_pack[20:24]
    data_packet = rec_pack[24:]

    if ACK_valid == 1:
        ack_number = rec_pack[8:12]
    else:
        ack_number = b'\x00\x00\x00\x00'

    # Simulate possible data corruption
    data_packet = data_error(data_packet)
    # Make a checksum out of received data (post corruption simulation)
    server_checksum = make_checksum(data_packet)
    # Convert Server-side checksum into bytes
    sbit_sum = server_checksum.to_bytes(2, byteorder='little')

    seq_num = int.from_bytes(seq_num, byteorder='big')
    ack_number = int.from_bytes(ack_number, byteorder='big')
    print('Packet received. Received SeqNum is:', seq_num)
    print('Received ack_number is:', ack_number)

    return seq_num, ack_number, client_checksum, data_packet, sbit_sum, client_port, server_port


def ackpack_creator(sbit_sum, seq_num, ACK_Number, client_port, server_port):
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

    ACK_Number = ACK_Number.to_bytes(4, byteorder='big')
    seq_num = seq_num.to_bytes(4, byteorder='big')
    # Clear the ack_packet
    ack_packet = bytearray()
###****************************************************************###
    ##Will Need to change dest_port to source_port at some point##
    for a in server_port:
        ack_packet.append(a)
    for b in client_port:
        ack_packet.append(b)
    for c in seq_num:
        ack_packet.append(c)
    for d in ACK_Number:
        ack_packet.append(d)
    for e in head_len:
        ack_packet.append(e)
    ack_packet.append(flag_byte)
    for g in Rec_window:
        ack_packet.append(g)
    for h in sbit_sum:
        ack_packet.append(h)
    for i in Urg_Data:
        ack_packet.append(i)
    for j in Options:
        ack_packet.append(j)

    return ack_packet


# ************** Receive starter message that tells client when server is accepting file transfer

while True:
    message, clientAddress = serverSocket.recvfrom(2048)
    # Receive startup packet from client
    receivedSeqNum, receivedAckNumber, clientChecksum, dataPacket, sbitsum, clientPort, serverPort = parser(message)
    receivedSeqNum += 1
    generatedACKNumber = random.randrange(10, 500, 5)
    print('Binary generatedACKNumber =', generatedACKNumber)

    if SYN == 1:
        startup_confirmation = ackpack_creator(clientChecksum, generatedACKNumber, receivedSeqNum, clientPort, serverPort)
        ack_loss(ack_loss_rate, startup_confirmation)
        SYN = 0
        break

while True:
    estab_conf, clientAddress = serverSocket.recvfrom(2048)
    estab_conf = estab_conf[:24]
    receivedSeqNum, receivedAckNumber, clientChecksum, dataPacket, sbitsum, clientPort, serverPort = parser(estab_conf)
    if receivedAckNumber == generatedACKNumber + 1:
        break
    else:
        ack_loss(ack_loss_rate, startup_confirmation)

expectedSeqNum = receivedSeqNum
expectedAckNumber = receivedAckNumber

start_time = time.time()

while 1:
    if not final_handshake:
        # Wait for the packet to come from the client
        recvPacket, clientAddress = serverSocket.recvfrom(2048)
        receivedSeqNum, receivedAckNumber, clientChecksum, dataPacket, sbitsum, clientPort, serverPort = parser(recvPacket)

        # If checksums the same and SeqNum is what we expect, everything is right with the world
        if sbitsum == clientChecksum and receivedSeqNum == expectedSeqNum and receivedAckNumber == expectedAckNumber:
            # SeqNum is correct, buffer data to the Queue
            received_Queue[receivedAckNumber] = dataPacket

            # Download the data for all in order packets
            while expectedAckNumber in received_Queue:
                file.write(received_Queue[expectedAckNumber])
                print("Segment #", expectedAckNumber, "Downloaded")
    ########## Pay attention once we start changing header size ##########
                old_expectedAckNumber = expectedAckNumber
                expectedSeqNum += len(received_Queue[expectedAckNumber])
                expectedAckNumber += len(received_Queue[expectedAckNumber])
                print('Updated expectedAckNumber is: ', expectedAckNumber)
                print('Updated expectedSeqNum is: ', expectedSeqNum)
                # Clear out old unneeded data in the buffer
                #received_Queue.pop((expectedSeqNum - 20), None)

            send_bitsum = make_checksum(received_Queue[old_expectedAckNumber])
            send_bitsum = send_bitsum.to_bytes(2, byteorder='little')
            print("send_bitsum =", send_bitsum)
            # Make the ACK Segment
            ackPacket = ackpack_creator(send_bitsum, old_expectedAckNumber, expectedSeqNum, clientPort, serverPort)
            # Send the ACK Segment back to sender, calculating if there's loss or not
            ack_loss(ack_loss_rate, ackPacket)

            # If last packet
            if len(dataPacket) < MSS:
                final_packet = expectedAckNumber

            # If final_packet flag is = to expectedSeqNum, we're really on the final packet. Trigger the final handshake
            if final_packet == expectedAckNumber:
                final_handshake = True

        # If packet is good but out of order
        elif sbitsum == clientChecksum and receivedSeqNum > expectedSeqNum and receivedAckNumber > expectedAckNumber:
            # Send the ACK packet back to sender, calculating if there's loss or not
            ack_loss(ack_loss_rate, ackPacket)
            # SeqNum is out of order but still good, buffer data to the Queue
            received_Queue[receivedAckNumber] = dataPacket
            # If last packet, close the file
            if len(dataPacket) < MSS:
                final_packet = receivedAckNumber + len(dataPacket)
        else:
            # Checksum fail, drop packet and do nothing
            pass
    else:
        print("Final Countdown")
        timeout_counter = 0
        # We've entered the final handshake, wait to receive the last confirmation packet from the sender.
        while True:
            recvPacket, clientAddress = serverSocket.recvfrom(2048)

            receivedSeqNum, receivedAckNumber, clientChecksum, dataPacket, sbitsum, clientPort, serverPort = parser(recvPacket)
            if receivedSeqNum == expectedSeqNum:
                # Once the proper packet is received
                receivedSeqNum += 1
                last_bitsum = b'\x00\x00'
                ackpack_ack_num = 0
                ackPacket = ackpack_creator(last_bitsum, ackpack_ack_num, receivedSeqNum, clientPort, serverPort)
                ack_loss(ack_loss_rate, ackPacket)
                break

        finalPacket = ackpack_creator(last_bitsum, expectedAckNumber, receivedSeqNum, clientPort, serverPort)
        ack_loss(ack_loss_rate, finalPacket)
        serverSocket.settimeout(0.05)
        while True:
            try:
                recvPacket, clientAddress = serverSocket.recvfrom(2048)
                receivedSeqNum, receivedAckNumber, clientChecksum, dataPacket, sbitsum, clientPort, serverPort = parser(recvPacket)
                if receivedAckNumber == expectedAckNumber + 1:
                    break
            except timeout:
                timeout_counter += 1
                if timeout_counter == 2:
                    break
        file.close()
        break

end_time = start_time
print("Total time for completion was %s" % (time.time() - start_time))
