# Network-Design
Network Design code
Team Members:
-----------------
Amadeusz Piwowarczyk
Johnathan Saniuk
Vishal Patel

_________________________________________________________________________________________
Environment:
--------------
Windows 10
Python 3.8
The programs are written and run using PyCharm
_________________________________________________________________________________________

List of Included files and their purpose:
----------------------------------------
1)  Design Document - Contains updated information and detail pertaining to phase 3 for the RDT2.2 program

2)  RST2.2_UDPClient.py and RDT2.2_UDPServer.py - The code for the sender (client) and receiver (server) that was used to send a file. The client would send the transfer file to the server which would be downloaded to the server's directory folder using RDT 2.2 rather than RDT 1.0 like phase 2 used. 

3)  picture.bmp - This was the file used to test the code and was sent from the client to the server.

4)  RDT2_2_Client_Server.txt - This contains the sender and receiver code but it is copied into a text file if someone wanted to copy-paste the code in for themselves or look at it without using a special program.

_________________________________________________________________________________________
Setting up different scenarios:
------------------------------

1) For no loss/ error --> When prompted: On both the client side and server side, type in "0" for chance of error percentage.

2) For ACK bit error --> When prompted: On the client side, type in the desired percentage of ACK error you want to have. On the server side, type in "0" for data error percentage.

3) For Data Packet Error --> When Prompted: On the client side type in "0" for ACK error percentage. On the server side, type in the percentage you want for data error.

_________________________________________________________________________________________
How to set up and execute the program:
------------------------------------------

Step  1: Download and install python on "python.org" and check the environment above to make sure what version to download on the client and server computer(s).

Step  2: Download pyCharm which will be used as the code editor for writing the programs.

Step  3: Move the UDPClient.py and UDPServer.py programs respectively to the client's computer and server's computer or onto a single computer. If this is run on a single computer, open the two files in a separate window to run each one individually to see both terminals and make it easier to work with.

Step  4: Either start a new project using pyCharm and copy and paste the code in for each program to have an automatic directory path or add the program to a directory so that pyCharm has a path to the program. Include the desired transfer file in the folder containing the code for the client RDT 2.2 program.

Step  5: Open RDT2.2_UDPServer.py and start the program on the server's computer. Then open the RDT2.2_UDPClient.py program on the client's computer, start the program, and make sure to enter the correct information that is in the console window when prompted (such as IP, file name you want to send and if you want an error or not). Also type in the correct information when prompted on the server side. Each side will be prompted to input information one after another till the file is ready to be transfered.

Step 6: Once the file is transfered, open the PyCharm folder that contains the server code and open the transfered file.

Step 7: If you want to rerun the program, run both programs again repeating the end of step 4, then step 5 and step 6.
__________________________________________________________________________________________________

References:
------------

1) The textbook we used as a guide to get my code is called: "Computer Networking: A Top-Down Approach  7th Edition". The section I looked in was 3.4.1.

2) For our checksum, attempted to modify a code we found but after many errors and debugging, we used a small piece from:
	- https://stackoverflow.com/questions/34244726/computing-16-bit-checksum-of-icmpv6-header

3) In addition to using python, we needed to convert the strings into bytes and we searched many sites and found this site that helped guide us in coding the strings into bytes:
	- https://stackoverflow.com/questions/10411085/converting-integer-to-binary-in-python

4) For finding the total time to finish the program we used the code example on this site to implement it into our code:
	- https://stackoverflow.com/questions/1557571/how-do-i-get-time-of-a-python-programs-execution
