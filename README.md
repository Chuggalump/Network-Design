Team Members:
-----------------
Amadeusz Piwowarczyk
Johnathan Saniuk
Vishal Patel
_________________________________________________________________________________________

***** This is all for Phase 6 implementing TCP *****
	However, we do not have a fully working TCP since it's missing some parts. We did however implement the TCP header segments for all the appropriate sections that TCP uses, we generate a random sequence number for each side (client and server) which we increment and keep track of. We also implemented fast retransmission as well as a 3 way handshake (including the set up and teardown).
_________________________________________________________________________________________
Environment:
--------------
Windows 10
Python 3.8
The programs are written and run using PyCharm
_________________________________________________________________________________________

List of Included files and their purpose:
----------------------------------------
1)  Design Doc.docx - Updated documentation for Phase 6 (Implementing TCP)

2)  TCP Client.py and TCP Server.py - These files are a build up of Go-Back-N and Selective Repeat. These files use parts of each side to send segments and have a recovery mechanism for bad segments.Each side now has a larger header file that includes the sequence and ack number that is used to check if we have the right segment based on the header information. Both sides also include a Handshake for setting up and also tearing down.

3)  picture.bmp - This was the file used to test the code and was sent from the client to the server.

4)  TCP_Client_Server.txt - This contains the sender and receiver code but it is copied into a text file if someone wanted to copy-paste the code in for themselves or look at it without using a special program.

5) Timer_Class.txt - This text file includes the code we used to define our timer class to implement our own timeout procedure rather than using a predefined socket timeout

6) Timer_Class.py - This is the python file that contains our timer class code used for the timeout

_________________________________________________________________________________________

Setting up different scenarios:
------------------------------

1) For no loss/ error --> When prompted: On both the client side and server side, type in "0" for chance of error percentage and loss rates.

2) For ACK bit error --> When prompted: On the client side, type in the desired percentage of ACK error you want to have and type in "0" for Data loss rate. On the server side, type in "0" for data error percentage and ACK loss rate.

3) For Data Packet Error --> When Prompted: On the client side type in "0" for ACK error percentage and type in "0" for Data loss rate. On the server side, type in the percentage you want for data error and ACK loss rate.

4) For ACK loss --> When Prompted: On the client side type in "0" for ACK error percentage and type in "0" for Data loss rate. On the server side, type in the percentage you want for data error, then type in the percentage of ACK loss you want to have.

5) For Data loss --> When Prompted: On the client side type in "0" for ACK error percentage, then type in the percentage of Data loss you want to have. On the server side, type in the percentage you want for data error and ACK loss rate.

_________________________________________________________________________________________

How to set up and execute the program:
------------------------------------------

Step  1: Download and install python on "python.org" and check the environment above to make sure what version to download on the client and server computer(s).

Step  2: Download pyCharm which will be used as the code editor for writing the programs.

Step  3: Move the TCP Client.py and TCP server.py programs respectively to the client's computer and server's computer or onto a single computer. If this is run on a single computer, open the two files in a separate window to run each one individually to see both terminals and make it easier to work with. Then add Timer_Class.py program to the client folder to be used during the execution of the program.

Step  4: Either start a new project using PyCharm and copy and paste the code in for each program to have an automatic directory path or add the program to a directory so that pyCharm has a path to the program. Include the desired transfer file in the folder containing the code for the client TCP Client.py program.

Step  5: Open TCP Server.py and start the program on the server's computer. Then open the TCP Client.py and the Timer_Class.py programs on the client's computer, start the TCP Client.py program, and make sure to enter the correct information that is in the console window when prompted (such as IP, file name you want to send, the specified window of packets you want to send, and the amount of error or loss you want to have during the transfer). The server will also be prompted to type in information. Each side will be prompted to input information one after another until all the necessary variables are set and the file is ready for transfer.

Step 6: Once the file is transfered, open the PyCharm folder that contains the server code and open the transfered file to view what you have downloaded.

Step 7: If you want to rerun the program, run both programs again repeating the end of step 4, then step 5 and step 6.
__________________________________________________________________________________________________

References:
------------

1) The textbook we used as a guide to get my code is called: "Computer Networking: A Top-Down Approach  7th Edition". We used the section pertaining to programming Selective Repeat client and server files as a guideline for where to go.

2) For the timeout section, we tried various methods but ended up finding a good way to have a timeout. Our code is built up from the basic skeleton code: https://kite.com/python/docs/socket.socket.settimeout

3) To implement multithreading, we experimented with the site below till we understood what we were doing and then built upon what we found during our tests to give us what we have now: https://www.geeksforgeeks.org/multithreading-python-set-1/



