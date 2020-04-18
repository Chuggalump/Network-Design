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

# Define server name (or IP) and Port#
from typing import Any, Tuple

# start_time = time.time()
serverName = '192.168.1.239'  # input('Please write your IPv4 IP here: ')
'''   '192.168.1.239'   '''
'''   '192.168.1.105'   '''
serverPort = 12000

# Create the client socket. First parameter indicates IPv4, second param indicates UDP
clientSocket = socket(AF_INET, SOCK_DGRAM)
print("clientSocket!!!!!", clientSocket)

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

# Mutexes
base_lock = _thread.allocate_lock()
ack_lock = _thread.allocate_lock()
nextSeqNum_lock = _thread.allocate_lock()
expected_lock = _thread.allocate_lock()

# Variable to add the Sequence Number to each packet
SeqNum = b'\x00\x00'
# Variable to track the expected Sequence Number we receive from the Server
expectedSeqNum = b'\x00\x00'
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

# Flags
packet_flag = False
# Check to see if the last packet was made
endQueue = False
ack_received = False

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


'''def ack_received(send_Packet, expect):
    while nextSeqNum <= (base + N):
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

    return expect'''


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


def packet_catcher(end_queue, client_socket):
    global base
    global expectedSeqNum
    global SeqNum
    global ack_received
    while 1:
        ack_timer = Timer(0.5, timeout)
        # Try to receive the ACK packet from server. If not received in 50ms, timeout and resend the packet
        bitsum = packet_Queue[base]
        bitsum = bitsum[2:4]

        # trasdata is the address sent with the ACK. We don't need it
        ack_timer.start()
        ackPacket, trashdata = client_socket.recvfrom(2048)
        ack_timer.cancel()

        # Parse the data
        NewSeqNum = ackPacket[:2]
        serverChecksum = ackPacket[2:]
        NewSeqNum = ack_corrupt(NewSeqNum)

        # if a different sequence number is received or checksum is bad resend the packet
        if NewSeqNum > expectedSeqNum or serverChecksum != bitsum:
            # Timeout so that the packet resends
            print("Improper ACK", NewSeqNum, "/ Checksum")
            #timeout()
            break
        # if the same sequence number is received, we have the right ACK
        elif NewSeqNum < expectedSeqNum:
            # Duplicate ACK, continue on
            print("Duplicate ACK", NewSeqNum, "received")
            pass
        elif NewSeqNum == expectedSeqNum and serverChecksum == bitsum:
            if base == 1053:
                x = 0
            if ((base - 1) / len(packet_Queue)) == 1:
                # If the dat is less than 1024 bytes we're on the last packet. Close the file and break
                end_queue = True
            if not end_queue:
                NewSeqNum = int.from_bytes(NewSeqNum, byteorder='big')
                print("Proper ACK", NewSeqNum, "received")
                base_lock.acquire()
                base += 1
                base_lock.release()

                ack_lock.acquire()
                ack_received = True
                ack_lock.release()

                expected_lock.acquire()
                expectedSeqNum = int.from_bytes(expectedSeqNum, byteorder='big')
                expectedSeqNum += 1
                expectedSeqNum = expectedSeqNum.to_bytes(2, byteorder='big')
                expected_lock.release()
            elif end_queue:
                image.close()
                _thread.exit()



def timeout():
    global nextSeqNum
    # If timeout occurs, print a statement and resend the same packet
    print("Packet Timed Out! Missed ACK", base)
    if_loss1 = data_loss(data_loss_rate)
    # Implement random data loss
    if if_loss1 == 1:
        # If if_loss1 is 1, the packet is "lost" en route to the server. Simulate by not sending the packet
        print(base, "Data was lost")
    else:
        # Else, no data loss. Send the packet
        clientSocket.sendto(packet_Queue[base], (serverName, serverPort))
        print("Packet #", base, "resent")
        nextSeqNum_lock.acquire()
        nextSeqNum += 1
        nextSeqNum_lock.release()
    #_thread.exit()
    #_thread.start_new_thread(packet_catcher, (endQueue, clientSocket))


ackTimer = Timer(0.5, timeout)

state = 0

start2 = time.time()


if __name__ == "__main__":
    # Buffer the packets
    x = 0
    while packet_flag is False:
        sendPacket, SeqNum = make_packet(packet_size, image, SeqNum)
        packet_Queue[x] = sendPacket
        x += 1
        if len(sendPacket) < 1028:
            print("Last Packet")
            packet_flag = True

    clientSocket.sendto(packet_Queue[base], (serverName, serverPort))
    _thread.start_new_thread(packet_catcher, (endQueue, clientSocket))
    print("Packet #", base, "sent")
    nextSeqNum += 1
    while 1:
        if_loss0 = data_loss(data_loss_rate)
        # Implement random data loss

        if not ack_received:
            pass
        elif ack_received:
            if if_loss0 == 1:
                # If if_loss0 is 1, the packet is "lost" en route to the server. Simulate by not sending the packet
                print(base, "Data was lost!")
            else:
                # Else, no data loss. Send the packetpacketInd
                if base == len(packet_Queue):
                    break
                clientSocket.sendto(packet_Queue[base], (serverName, serverPort))
                print("Packet #", base, "sent")
                nextSeqNum_lock.acquire()
                nextSeqNum += 1
                nextSeqNum_lock.release()

            ack_lock.acquire()
            ack_received = False
            ack_lock.release()


end2 = start2
print("Total time for completion was %s" % (time.time() - start2))

# RRRRREEEEEEEEEEEeeeeeeeeEEEEEEEEeeeeeeEEEEEeeeEeEEeEEEEEEEEEEEEEEEEE
