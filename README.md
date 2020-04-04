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
1)  Design Document - Contains updated information and detail pertaining to phase 4 for the RDT 3.0 program

2)  RDT3.0_UDPClient.py and RDT3.0_UDPServer.py - These files are an addition to RDT 2.2 from phase 3. The addition being that there is an option to have ACK being dropped and another option to drop the Data. There is also an implementation to fix each option independently if one of them does occur.

3)  picture.bmp - This was the file used to test the code and was sent from the client to the server.

4)  RDT3_0_Client_Server.txt - This contains the sender and receiver code but it is copied into a text file if someone wanted to copy-paste the code in for themselves or look at it without using a special program.

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

Step  3: Move the UDPClient.py and UDPServer.py programs respectively to the client's computer and server's computer or onto a single computer. If this is run on a single computer, open the two files in a separate window to run each one individually to see both terminals and make it easier to work with.

Step  4: Either start a new project using pyCharm and copy and paste the code in for each program to have an automatic directory path or add the program to a directory so that pyCharm has a path to the program. Include the desired transfer file in the folder containing the code for the client RDT 3.0 program.

Step  5: Open RDT3.0_UDPServer.py and start the program on the server's computer. Then open the RDT3.0_UDPClient.py program on the client's computer, start the program, and make sure to enter the correct information that is in the console window when prompted (such as IP, file name you want to send and the amount of error or loss you want to have during the transfer). Also type in the correct information when prompted on the server side. Each side will be prompted to input information one after another till the file is ready to be transfered.

Step 6: Once the file is transfered, open the PyCharm folder that contains the server code and open the transfered file.

Step 7: If you want to rerun the program, run both programs again repeating the end of step 4, then step 5 and step 6.
__________________________________________________________________________________________________

References:
------------

1) The textbook we used as a guide to get my code is called: "Computer Networking: A Top-Down Approach  7th Edition". We used the section pertaining to programming RDT 3.0 client and server files as a guideline for where to go.

2) For the timeout section, we tried various methods but ended up finding a good way to have a timeout. Our code is built up from the basic skeleton code: https://kite.com/python/docs/socket.socket.settimeout






