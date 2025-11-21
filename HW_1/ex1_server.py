#!/usr/bin/python3
import socket
import sys
import select
import math

DEFAULT_PORT = 1337
BACKLOG = 5
RECV_BUF_SIZE = 4096


def parse_args():
    """
    Usage: ex1_server.py users_file [port]
    """
    argc = len(sys.argv)
    if argc < 2 or argc > 3:
        print("Usage: ex1_server.py users_file [port]")
        sys.exit(1)

    users_file = sys.argv[1]

    if argc == 3:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("Error: port must be an integer.")
            sys.exit(1)
    else:
        port = DEFAULT_PORT

    return users_file, port


def load_users(users_file):
    """
    Load tab-delimited users file: username<TAB>password
    Returns a dict: {username: password}
    """
    users = {}
    try:
        with open(users_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 2:
                    # ignore malformed lines
                    continue
                username, password = parts
                users[username] = password
    except Exception as e:
        print(f"Error reading users file: {e}")
        sys.exit(1)

    return users


def is_parentheses_balanced(s):
    """
    Check if a parentheses string is balanced.
    Ignores non-parentheses characters.
    """
    stack = []
    for ch in s:
        if ch == "(":
            stack.append(ch)
        elif ch == ")":
            if not stack:
                return False
            stack.pop()
    return len(stack) == 0


def lcm(a, b):
    """
    Compute the least common multiple of two integers.
    For 0, we define lcm(0, x) = 0.
    """
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // math.gcd(a, b)


def caesar_cipher(plaintext, shift):
    """
    Caesar cipher: shift letters by 'shift', output lowercase letters.
    Spaces are preserved.
    If any character is not [A-Za-z ] -> return None (invalid input).
    """
    result = []
    base = ord("a")
    for ch in plaintext:
        if ch == " ":
            result.append(" ")
        elif ch.isalpha():
            offset = (ord(ch.lower()) - base + shift) % 26
            result.append(chr(base + offset))
        else:
            # invalid character
            return None
    return "".join(result)


def create_listening_socket(port):
    """
    Create, bind, and listen on a TCP socket.
    """
    srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv_sock.bind(("", port))
    except Exception:
        print(f"Error binding socket to port: {port}")
        srv_sock.close()
        sys.exit(1)
    srv_sock.listen(BACKLOG)
    return srv_sock


def main():
    users_file, port = parse_args()
    users = load_users(users_file)

    server_sock = create_listening_socket(port)
    _, port = server_sock.getsockname() # Get the actual port number
    print(f"Server listening on port {port}")

    # Sockets to monitor
    inputs = [server_sock]

    # Per-client state
    buffers = {}       # sock -> str (accumulated incoming data)
    client_state = {}  # sock -> dict: {logged_in, login_stage, username, pending_username}

    def close_client(sock):
        if sock in inputs:
            inputs.remove(sock)
        buffers.pop(sock, None)
        client_state.pop(sock, None)
        try:
            sock.close()
        except Exception:
            pass

    def handle_login_line(sock, line, state):
        """
        Handle a single line during the login phase.
        state: dict for this client.
        """
        if state["login_stage"] == "await_user":
            if not line.startswith("User: "):
                # client sent something else before User: -> close
                close_client(sock)
                return
            username = line[len("User: "):]
            state["pending_username"] = username
            state["login_stage"] = "await_password"

        elif state["login_stage"] == "await_password":
            if not line.startswith("Password: "):
                close_client(sock)
                return
            password = line[len("Password: "):]
            username = state["pending_username"]

            # Check credentials
            if username in users.keys() and users[username] == password:
                state["logged_in"] = True
                state["username"] = username
                state["login_stage"] = None
                state["pending_username"] = None
                try:
                    sock.sendall(f"Hi {username}, good to see you\n".encode())
                except Exception:
                    close_client(sock)
            else:
                # Failed login, allow retry
                state["pending_username"] = None
                state["login_stage"] = "await_user"
                try:
                    sock.sendall("Failed to login.\n".encode())
                except Exception:
                    close_client(sock)

    def handle_command_line(sock, line, state):
        """
        Handle a single command line for a logged-in client.
        """
        stripped = line.strip()

        # quit: close connection, no response required
        if stripped == "quit":
            close_client(sock)
            return
        # parentheses: X
        if line.startswith("parentheses:"):
            parts = line.split(" ", 1)
            if len(parts) != 2:
                close_client(sock)
                return
            paren_str = parts[1]
            balanced = is_parentheses_balanced(paren_str)
            resp = f"the parentheses are balanced: {'yes' if balanced else 'no'}\n"
            try:
                sock.sendall(resp.encode())
            except Exception:
                close_client(sock)
            return

        # lcm: X Y
        if line.startswith("lcm:"):
            parts = line.split()
            if len(parts) != 3:
                close_client(sock)
                return
            try:
                x = int(parts[1])
                y = int(parts[2])
            except ValueError:
                close_client(sock)
                return
            result = lcm(x, y)
            resp = f"the lcm is: {result}\n"
            try:
                sock.sendall(resp.encode())
            except Exception:
                close_client(sock)
            return

        # caesar: plaintext X
        if line.startswith("caesar:"):
            after_prefix = line[len("caesar:"):].strip()
            if " " not in after_prefix:
                close_client(sock)
                return
            plaintext, shift_str = after_prefix.rsplit(" ", 1)
            if not plaintext:
                close_client(sock)
                return
            try:
                shift = int(shift_str)
            except ValueError:
                close_client(sock)
                return

            ciphertext = caesar_cipher(plaintext, shift)
            if ciphertext is None:
                resp = "error: invalid input\n"
            else:
                resp = f"the ciphertext is: {ciphertext}\n"

            try:
                sock.sendall(resp.encode())
            except Exception:
                close_client(sock)
            return

        # Any other command -> protocol error -> close
        close_client(sock)

    while True:
        try:
            readable, _, _ = select.select(inputs, [], [])
        except Exception:
            # Simple HW server, on select error we just continue
            continue

        for s in readable:
            if s is server_sock:
                # New connection
                try:
                    client_sock, addr = server_sock.accept()
                except Exception:
                    continue

                inputs.append(client_sock)
                buffers[client_sock] = ""
                client_state[client_sock] = {
                    "logged_in": False,
                    "login_stage": "await_user",
                    "username": None,
                    "pending_username": None,
                }

                # Send welcome message exactly once
                try:
                    client_sock.sendall(b"Welcome! Please log in\n")
                except Exception:
                    close_client(client_sock)

            else:
                # Data from existing client
                try:
                    data = s.recv(RECV_BUF_SIZE)
                except Exception:
                    close_client(s)
                    continue

                if not data:
                    # Client closed connection
                    close_client(s)
                    continue

                # Append to buffer
                try:
                    buffers[s] += data.decode()
                except UnicodeDecodeError:
                    close_client(s)
                    continue

                # Process complete lines
                while "\n" in buffers[s]:
                    line, rest = buffers[s].split("\n", 1)
                    buffers[s] = rest
                    line = line.rstrip("\r")

                    state = client_state.get(s)
                    if state is None:
                        break  # client already closed

                    if not state["logged_in"]:
                        handle_login_line(s, line, state)
                        if s not in inputs:
                            break  # client closed
                    else:
                        handle_command_line(s, line, state)
                        if s not in inputs:
                            break  # client closed


if __name__ == "__main__":
    main()
