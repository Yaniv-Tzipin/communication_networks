HW1:

1. Overview

This project implements a simple client–server protocol over TCP.
The server supports multiple concurrent clients using select() (no threads).
Communication is line-based (\n at the end of each message).

2. Usage

The server script must run *before* running clients script 

Server -

./ex1_server.py users_file [port]


users_file – a text file containing username<TAB>password pairs

port – optional, defaults to 1337

Client -

./ex1_client.py [hostname [port]]

hostname - optional, default is localhost, can be either an IP address or a string host name

port – optional, defaults to 1337

Note: A port cannot be supplied without a hostname.

3. Protocol Description

3.1 Connection

When a client connects, the server sends:

Welcome! Please log in

3.2 Login

The client must send to the server exactly:

User: \<username\>

Password: \<password\>

If the credentials match the users file, the server sends to the client:

Hi \<username\>, good to see you

Otherwise, it sends:

Failed to log in.

*If a message does not follow this sequence, or if the credentials does not match the users file
→ the server sends to the client "Failed to log in." and let it try again.*

4. Supported Commands (after successful login):

a. parentheses: X

Checks whether X is a balanced sequence of ( and ).

Server responds:

the parentheses are balanced: yes

or

the parentheses are balanced: no

Note: The server ignores non-parentheses characters, so strings like "(X)" are acceptable.

b. lcm: X Y

Computes the least common multiple of integers X and Y.

Server responds:

the lcm is: R

Note: The LCM in case X = 0 or Y = 0 is 0.

c. caesar: plaintext X

Applies a Caesar cipher shift of X to plaintext (result is lowercase).

Example response: "the ciphertext is: Y"

If plaintext contains characters other than English letters or spaces: "error: invalid input"

d. quit

Client requests to disconnect.
The server closes the connection immediately (no response).

e. For any other input at this point, the server closes the connection. 

5. Error Handling

Before login: any incorrect message → server disconnects.

After login: any malformed command → server disconnects.

Client also validates commands and disconnects on invalid input.

6. Implementation Notes

Transport: TCP via socket(AF_INET, SOCK_STREAM).

Server concurrency: handled using select() on the listening socket and all active client sockets.

Protocol is line-based and each client maintains a small login state machine.

Caesar cipher output is always lowercase.

LCM is computed using abs(a*b) // gcd(a,b).
