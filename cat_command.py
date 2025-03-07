import socket

# Thetis CAT Server Settings (adjust accordingly)
THETIS_IP = "127.0.0.1"  # Change to your Thetis CAT server IP
THETIS_PORT = 13013  # Default CAT TCP/IP port

def send_cat_command(command):
    """ Sends a CAT command to Thetis over TCP. """
    try:
        with socket.create_connection((THETIS_IP, THETIS_PORT), timeout=2) as sock:
            c = f"{command};\n"
            sock.sendall(c.encode() + b'\n')
            # print(f"✅ Sent: {command} | Response: {response}")
            return
    except Exception as e:
        print(f"❌ CAT Connection Error: {e}")

def query_cat(command):
    """ Sends a CAT command to Thetis over TCP. """
    try:
        with socket.create_connection((THETIS_IP, THETIS_PORT), timeout=2) as sock:
            c = f"{command};\n"
            sock.sendall(c.encode() + b'\n')
            response = sock.recv(1024)
            # print(f"✅ Sent: {command} | Response: {response}")
            return response.decode('utf-8').strip(';')
    except Exception as e:
        print(f"❌ CAT Connection Error: {e}")
