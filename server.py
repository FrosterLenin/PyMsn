import socket
import struct
import zlib
from constants import PacketType, PacketLenghts, BaseConstants

HOST = 'localhost'
PORT = 12345

clients = {}  # client addresses and client ID
next_client_id = 1

def build_packet(packet_type, client_id, counter, body=b''):
    # HEADER STUFF
    crc = zlib.crc32(body)
    packet_length = PacketLenghts.client_base_send_messsage + len(body)
    header = struct.pack(">BBIII", packet_type, packet_length, client_id, counter, crc)
    return header + body

def handle_request_id(server_socket, client_address):
    global next_client_id
    if next_client_id == BaseConstants.MAX_CLIENTS + 1:
         print(f"Numero massimo di client raggiunto: {BaseConstants.MAX_CLIENTS}")
         return
    assigned_id = next_client_id
    next_client_id += 1
    clients[client_address] = assigned_id
    print(f"Assegnato ID {assigned_id} a {client_address}")
    packet = build_packet(PacketType.CONNECT, assigned_id, 1) 
    server_socket.sendto(packet, client_address)

def handle_send_message(server_socket, client_address, client_id_in_header, counter, body):
    message = body.decode("utf-8")
    print(f"[{client_id_in_header} | {counter}] {message}")
    for addr in clients.keys():
        if addr != client_address:
            server_socket.sendto(build_packet(PacketType.SEND_MESSAGE, client_id_in_header, counter, body), addr)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))
    print("Server started...")

    while True:
        try:
            data, client_address = server_socket.recvfrom(1024)
            if len(data) < PacketLenghts.header:
                print(f"Pacchetto troppo corto da {client_address}")
                continue

            packet_type, packet_length, client_id_in_header, counter, crc = struct.unpack(">BBIII", data[:PacketLenghts.header])
            body = data[PacketLenghts.header:]

            # Controllo CRC
            if zlib.crc32(body) != crc:
                print(f"[{client_address}] Pacchetto corrotto")
                continue

            if packet_type == PacketType.REQUEST_ID:
                handle_request_id(server_socket, client_address)
            elif packet_type == PacketType.SEND_MESSAGE:
                handle_send_message(server_socket, client_address, client_id_in_header, counter, body)
            else:
                print(f"Pacchetto sconosciuto: {packet_type}")

        except Exception as e:
            print(f"Server error: {e}")

if __name__ == "__main__":
    start_server()
