# communication_networks

changes:

Server -
1. Handle "port already in use" case (if the given port is already in use, print it and exit)
2. 

Client -
1. I checked about the IP/string 'hostname' parameter ('connect' function handles the hostname parameter "as is" - 
if it's an IP address: it just connects to it, if it's a string: it tries to get the IP address through DNS resolver
and connects to it, if there's an error: it raises an exception and we catch it)
2. I checked parse_args() and fixed our logic and prints
3. I Changed the way we read from the socket - now we use 'makefile' function (read about it if you want, it's pretty cool)
4. I checked handle_login() and fixed our logic and prints
5. I checked command_loop() and fixed our logic and prints
