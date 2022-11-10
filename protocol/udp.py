"""This module implements a UDP routines for sending and receving bytes via UDP.

   It provides both client and server implementations.
"""

from typing import Callable
from socket import *

# The size of the buffer to hold incoming messages.
# This should be big enough to receive the biggest reasonable package
# the application can receive.
RECEIVE_BUFFER_SIZE = 2048


def makeUDPSocket():
    return socket(AF_INET, SOCK_DGRAM)


def send(package: bytes, hostname: str, port: int, viaSocket: socket) -> None:
    """Sends the given bytes to the server with the given hostname and port.

    hostname can be a domain name or an IP address.
    """
    viaSocket.sendto(package, (hostname, port))


def readIncomingPacket(fromSocket: socket) -> tuple[bytes, tuple[str, int]]:
    """Listens for incoming packages on the socket and returns them to the caller.

    This is a blocking call.

    The return value tuple has the form: (package, (sender_ip, sender_port))
    """
    return fromSocket.recvfrom(RECEIVE_BUFFER_SIZE)


def serverListen(toPort: int, callback: Callable[[tuple[bytes, tuple[str, int]], socket], bool]) -> None:
    """Listens for incoming UDP packages on the given port and forwards them to the passed callback.

    This is a blocking call.

    The callback should return True to terminate the listening loop.

    The arguments to the callback function have the form (package, (sender_ip, sender_port))
    """
    serverSocket = makeUDPSocket()
    serverSocket.bind(("", toPort))
    quit = False
    while not quit:
        quit = callback(readIncomingPacket(serverSocket), serverSocket)

    serverSocket.close()
