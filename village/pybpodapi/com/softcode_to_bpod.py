import socket

from village.settings import settings


class SoftCodeToBpod:
    def __init__(self) -> None:
        """Open the connection"""
        address = int(settings.get("BPOD_NET_PORT"))
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(1.0)
        self.address = ("127.0.0.1", address)

    def send(self, idx: int) -> None:
        """Send the softcode to the port idx"""
        str_message = "SoftCode" + str(idx)
        message = str_message.encode("utf-8")
        self.client_socket.sendto(message, self.address)
        stop_message = b"s"
        self.client_socket.sendto(stop_message, self.address)

    def kill(self) -> None:
        """Send a code to kill the current session"""
        str_message = "kill"
        message = str_message.encode("utf-8")
        self.client_socket.sendto(message, self.address)
        stop_message = b"s"
        self.client_socket.sendto(stop_message, self.address)

    def close(self) -> None:
        """Close the connection"""
        self.client_socket.close()
