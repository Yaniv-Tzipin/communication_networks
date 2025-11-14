#!/usr/bin/python3
import socket
import sys

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 1337


def parse_args():
    """
    Parse command-line arguments.
    Valid:
      ex1_client.py
      ex1_client.py hostname
      ex1_client.py hostname port
    """
    argc = len(sys.argv)

    if argc == 1:
        return DEFAULT_HOST, DEFAULT_PORT

    if argc == 2:
        return sys.argv[1], DEFAULT_PORT

    if argc == 3:
        try:
            return sys.argv[1], int(sys.argv[2])
        #TODO: should we handle it this way?
        except ValueError:
            print("Error: port must be an integer.")
            sys.exit(1)

    print("Usage: ex1_client.py [hostname [port]]")
    sys.exit(1)


def recv_line(sock):
    """
    Receive a single line (ending with '\n') from the socket.
    Returns the line as a string without the trailing '\n'.
    Returns '' if the connection is closed.
    """
    #TODO: is there an ellegant way to do this?
    chunks = []
    while True:
        data = sock.recv(1)
        if not data:
            # Connection closed
            return ""
        ch = data.decode()
        if ch == "\n":
            break
        chunks.append(ch)
    return "".join(chunks)


def connect_to_server(hostname, port):
    """
    Create a TCP socket and connect to the server.
    Returns the connected socket, or None on failure.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((hostname, port))
        return sock
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return None


def handle_login(sock):
    """
    Perform the login phase.
    - Receive welcome line
    - Loop asking for username/password
    - Send to server and process response
    Returns True if login succeeded, False otherwise.
    """

    welcome = recv_line(sock)
    if not welcome:
        #TODO: check if this should be the print
        print("Server closed the connection.")
        return False
    print(welcome)

    while True:
        username = input("User: ")
        password = input("Password: ")

        # Send in protocol format
        try:
            sock.sendall(f"User: {username}\n".encode())
            sock.sendall(f"Password: {password}\n".encode())
        except Exception as e:
            print(f"Error sending login data: {e}")
            return False

        # Receive login response
        response = recv_line(sock)
        if not response:
            #TODO : check if this should be the print
            print("Server closed the connection.")
            return False

        print(response)

        if response.startswith("Hi "):
            # Login success
            return True
        elif response.startswith("Failed to login."):
            # Login failed, try again
            continue
        else:
            #TODO: check if this should be the print
            print("Protocol error during login. Closing.")
            return False

def is_valid_command(cmd):
    """
    Validate the basic format of a command according to the assignment.
    Returns True if the format is valid, False otherwise.
    """
    line = cmd.strip()

    if line == "quit":
        return True

    if line.startswith("parentheses:"):
        # Expect at least one space and something after it (the X string)
        parts = line.split(" ", 1)
        return len(parts) == 2 and parts[1] != ""

    if line.startswith("lcm:"):
        # Expect: lcm: X Y   where X and Y are ints
        parts = line.split()
        # parts should be: ["lcm:", "X", "Y"]
        if len(parts) != 3:
            return False
        try:
            int(parts[1])
            int(parts[2])
            return True
        except ValueError:
            return False

    if line.startswith("caesar:"):
        # Expect: caesar: plaintext X
        # plaintext may contain spaces, X is the last token and must be int
        after_prefix = line[len("caesar:"):].strip()
        # Need at least "something X"
        if " " not in after_prefix:
            return False
        plaintext, shift_str = after_prefix.rsplit(" ", 1)
        if not plaintext:
            return False
        try:
            int(shift_str)
            return True
        except ValueError:
            return False

    # Any other command is invalid
    return False


def command_loop(sock):
    """
    After successful login, handle the commands loop:
    - Read user input
    - Validate format
    - If invalid: print error and disconnect
    - If valid: send to server, print server response
    - Stop on 'quit' or disconnect
    """
    while True:
        try:
            user_input = input()
        except EOFError:
            #TODO: is this the way we should handle it?
            # e.g. Ctrl+D
            break

        if not is_valid_command(user_input):
            print("Error: invalid command format. Closing connection.")
            break

        if user_input.strip() == "quit":
            try:
                sock.sendall((user_input + "\n").encode())
            except Exception as e:
                print(f"Error sending data: {e}")
            break

        try:
            sock.sendall((user_input + "\n").encode())
        except Exception as e:
            print(f"Error sending data: {e}")
            break

        # For 'quit', we still expect the server to possibly respond,
        # but if it just closes, recv_line will return ''.
        response = recv_line(sock)
        if not response:
            print("Server closed the connection.")
            break

        print(response)





def main():
    hostname, port = parse_args() #TODO: host can be name (localhost) or IP

    sock = connect_to_server(hostname, port)
    if sock is None:
        # TODO: decide what to do if connection fails
        return
    # Use 'with' so socket is closed automatically
    with sock:
        try:
            logged_in = handle_login(sock)
            if not logged_in:
                return

            command_loop(sock)

        except Exception as e:
            print(f"Client error: {e}")


if __name__ == "__main__":
    main()
