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
from Timer_Class import Timer

# Define server name (or IP) and Port#
from typing import Any, Tuple

# start_time = time.time()
serverName = '192.168.1.239'  # input('Please write your IPv4 IP here: ')
'''   '192.168.1.239'   '''
'''   '192.168.1.105'   '''
serverPort = 12000

# Create the client socket. First parameter indicates IPv4, second param indicates UDP
clientSocket = socket(AF_INET, SOCK_DGRAM)
print("clientSocket:", clientSocket)

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
FileName = '06 Cry For Eternity.mp3'  # input('Write the file name you wish to send: ')
image = open(FileName, 'rb')

# Set the packet size and create an index to count packets
packet_size = 1024
packetIndex = 0
print("packet size is: ", packet_size)

# Mutexes
base_lock = _thread.allocate_lock()
nextSeqNum_lock = _thread.allocate_lock()
expected_lock = _thread.allocate_lock()

# Variable to add the Sequence Number to each packet
SeqNum = b'\x00\x00'
sendPacket = bytearray()
initialPacket = bytearray()
bitsum = 0
# Variable to track which packet in the queue we're on
nextSeqNum = 0
# Create an empty dictionary to store the sent but unacked packets
packet_Queue = {}
# Define Window Size (0 to N)
N = 19
# Beginning of the window
base = 0
# Instantiate Timer
ack_timer = Timer(0.05)

ack_error = 10
data_loss_rate = 10


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


def data_loss(test_num):
    # Select a random int btwn 0 and 100
    # random.seed()
    rand_num = random.randrange(0, 100)
    # if randNum is less than the specified error rate, don't send packet
    if rand_num < test_num:
        return True
    else:
        return False


def ack_corrupt():
    # Select a random int btwn 0 and 100
    rand_num = random.randrange(0, 100)
    # if randNum is less than the specified error rate, flip the bit
    if rand_num < ack_error:
        return True
    else:
        return False


def final_handshake(da_base):
    da_base = da_base.to_bytes(2, byteorder='big')
    final_packet = bytearray()
    for i in da_base:
        final_packet.append(i)
    clientSocket.sendto(final_packet, (serverName, serverPort))


def packet_catcher(client_socket):
    global base
    global nextSeqNum
    # Variable to track the expected Sequence Number we receive from the Server
    expected_seq_num = 0
    while 1:
        # Try to receive the ACK packet from server. If not received in 50ms, timeout and resend the packet

        if ack_timer.timeout():
            expected_seq_num = base + N

        # trasdata is the address sent with the ACK. We don't need it
        ackPacket, trashdata = client_socket.recvfrom(2048)

        # Parse the data
        NewSeqNum = ackPacket[:2]
        NewSeqNum = int.from_bytes(NewSeqNum, byteorder='big')
        serverChecksum = ackPacket[2:]

        bitsum = packet_Queue[NewSeqNum]
        bitsum = bitsum[2:4]

        if NewSeqNum > expected_seq_num:
            # Cumulative ACK, set base to NewSeqNum + 1 and update expected_seq_num
            base_lock.acquire()
            base = NewSeqNum + 1
            base_lock.release()
            expected_seq_num = base
        elif serverChecksum != bitsum or ack_corrupt():
            # Timeout to resend window
            pass
        elif NewSeqNum < expected_seq_num:
            # Duplicate ACK, continue on
            pass
        elif NewSeqNum == expected_seq_num and serverChecksum == bitsum:
            base_lock.acquire()
            base = NewSeqNum + 1
            base_lock.release()
            expected_seq_num = base

            if ack_timer.running:
                ack_timer.stop()
        else:
            print("I done goofed")

        if (base / len(packet_Queue)) >= 1:
            image.close()
            _thread.exit()


start2 = time.time()

if __name__ == "__main__":
    # Buffer the packets
    x = 0
    while True:
        sendPacket, SeqNum = make_packet(packet_size, image, SeqNum)
        packet_Queue[x] = sendPacket
        x += 1
        if len(sendPacket) < 1028:
            break

    _thread.start_new_thread(packet_catcher, (clientSocket,))

    while 1:
        if nextSeqNum == (base + N):
            time.sleep(0.001)
        if nextSeqNum > 0 and ack_timer.running() is False:
            ack_timer.start()
        if ack_timer.timeout():
            if ack_timer.running():
                ack_timer.stop()
            nextSeqNum = base
        if nextSeqNum <= (base + N):
            # Implement random data loss
            if not data_loss(data_loss_rate):
                # If data_loss is false, packet is not lost. Send the packet
                if nextSeqNum < len(packet_Queue):
                    if nextSeqNum == base:
                        ack_timer.start()
                    clientSocket.sendto(packet_Queue[nextSeqNum], (serverName, serverPort))
                if (base / len(packet_Queue)) >= 1:
                    final_handshake(base)
                    ack_timer.stop()
                    break
            elif data_loss(data_loss_rate):
                # Else if data_loss is True, the packet is "lost" en route to the server.
                # Simulate by not sending the packet
                pass

            nextSeqNum_lock.acquire()
            nextSeqNum += 1
            nextSeqNum_lock.release()

end2 = start2
print("Total time for completion was %s" % (time.time() - start2))

# RRRRREEEEEEEEEEEeeeeeeeeEEEEEEEEeeeeeeEEEEEeeeEeEEeEEEEEEEEEEEEEEEEE
