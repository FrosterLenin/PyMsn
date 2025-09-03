import socket
import select
import struct
import sys
import threading
import zlib
from constants import PacketType, PacketLenghts

class Client:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = ('localhost', 12345)
        self.client_id = None
        self.counter = 1 # conteggio di request id...
        self.client_socket.setblocking(False)
        self.last_counter = {} # per controllare il counter dei pacchetti ricevuti

    def build_packet(self, packet_type, body=b''):
        # HEADER STUFF
        self.counter += 1
        crc = zlib.crc32(body)
        packet_length = PacketLenghts.client_base_send_messsage + len(body)
        header = struct.pack(">BBIII", packet_type, packet_length, self.client_id or 0, self.counter, crc)
        return header + body 
    
    def send_request_id(self):
        packet = self.build_packet(PacketType.REQUEST_ID)
        self.client_socket.sendto(packet, self.server_address)

    def send_message(self, text):
        if self.client_id is None:
            print("Connessione al server fallita: Assegnare un ID prima di inviare un messaggio")
            return
        encoded = text.encode("utf-8")  # ENCODE DI QUELLO CHE SCRIVO IN CONSOLE
        packet = self.build_packet(PacketType.SEND_MESSAGE, encoded)
        self.client_socket.sendto(packet, self.server_address)

    def handle_packet(self, data):
        if len(data) < PacketLenghts.header:
            print("Pacchetto troppo corto")
            return
        packet_type, packet_length, sender_id, counter, crc = struct.unpack(">BBIII", data[:PacketLenghts.header])
        body = data[PacketLenghts.header:]
        calc_crc = zlib.crc32(body)
        if calc_crc != crc:
            print(f"CRC ERRATO")
            return

        # Controllo counter per pacchetti fuori ordine
        if sender_id in self.last_counter:
            last = self.last_counter.get(sender_id)
            if packet_type != PacketType.CONNECT and counter != last + 1:
                print(f"pacchetto fuori ordine {sender_id} (counter {counter}, ultimo {last})")
        self.last_counter[sender_id] = counter

        if packet_type == PacketType.CONNECT:
            self.client_id = sender_id
            print(f"Connesso con ID {self.client_id}")
        elif packet_type == PacketType.SEND_MESSAGE:
            message = body.decode("utf-8")
            print(f"[USER_{sender_id} | {counter}] {message}")

    def run(self):
        self.send_request_id()

        def console_input():
            while True:
                msg = sys.stdin.readline().strip()
                if msg:
                    self.send_message(msg)

        # LEGGERE DA CONSOLE BLOCCA TUTTO QUINDI HO DOVUTO CREARE UN THREAD
        # PERCHE SE FACCIO QUESTO select.select([self.client_socket, sys.stdin] VEDE CHE IL MESSAGGIO DI CONSOLE NON E' UN SOCKET
        threading.Thread(target=console_input, daemon=True).start()

        while True:
            read_sockets, _, _ = select.select([self.client_socket], [], [])
            for socket in read_sockets:
                try:
                    data, _ = self.client_socket.recvfrom(1024)
                except:
                    print(f"Server offline")
                    return
                self.handle_packet(data)


if __name__ == "__main__":
    client = Client()
    client.run()
