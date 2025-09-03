from enum import IntEnum

class PacketType(IntEnum):
    REQUEST_ID = 1
    SEND_MESSAGE = 2
    CONNECT = 3

class PacketLenghts:
    header = 14 #2B + 3I (I = 4B) = 14
    client_request_id = header
    client_base_send_messsage = 14 # 2B + 3I (I = 4B)   BBIII
    server_response_connect = header

class BaseConstants:
    MAX_CLIENTS = 3