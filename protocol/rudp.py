"""This module implments an RUDP client and server.

   RUDP, or Reliable UDP, is a protocol that adds reliability
   on top of UDP.
"""

from time import time

from requests import delete
from .udp import makeUDPSocket, readIncomingPacket, send as udpSend, serverListen
from socket import socket
from typing import Callable
from asyncio import sleep as ftSleep
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import threading
from .hashing import *


class _Package:
    def __init__(self, message: bytes, uuid: str) -> None:
        """Inits a package object.

        uuid should be at least 36 characters long and only the first 36 characters should make the package unique"""
        self.message = message
        self.uuid = uuid
        pass


class MalformedPackageError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "The hash value of the received package did not match the computed value. The package is corrupted."
        )


def _packageToBytes(package: _Package) -> bytes:
    """Serialises the package to bytes to be sent over the protocol."""
    dataSection = bytearray(package.uuid[0:36].encode())
    dataSection += package.message
    checksum = hash(bytes(dataSection))

    packageBytes = bytearray(checksum)
    packageBytes += dataSection
    return bytes(packageBytes)


def _packageFromBytes(data: bytes) -> _Package:
    """Constructs a package object from the given bytes.

    Throws MalformedPackageError if the package is corrupted.
    """
    incomingChecksum = data[:2]
    dataSection = data[2:]
    computedChecksum = hash(dataSection)

    incomingChecksumAsInt = int.from_bytes(incomingChecksum, "big")
    computedChecksumAsInt = int.from_bytes(computedChecksum, "big")

    if incomingChecksumAsInt != computedChecksumAsInt:
        raise MalformedPackageError()

    uuidStr = dataSection[:36].decode()
    return _Package(dataSection[36:], uuidStr)


class _PackageSendRequest:
    """A struct of the parameters required to send packages to a server."""

    def __init__(self, packageInBytes: bytes, toHostname: str, toPort: int) -> None:
        self.packageInBytes = packageInBytes
        self.toHostname = toHostname
        self.toPort = toPort
        pass


class Client:
    def __init__(self) -> None:
        self.buffer: dict[str, _PackageSendRequest] = {}
        self.responses: dict[str, bytes] = {}

        self.pushTimer: threading.Timer = None
        self.channel: socket = makeUDPSocket()

        # with ThreadPoolExecutor() as executor:
        ThreadPoolExecutor().submit(self._pollResponses)

    def send(self, message: bytes, toHostname: str, toPort: int) -> str:
        """Sends the given message to the server with the given hostname and port.

        The hostname can be an IP address.

        The return value is the id of the request, which can be used to get its
        response.
        """
        package = _Package(message, str(uuid4()))
        self.buffer[package.uuid] = _PackageSendRequest(
            _packageToBytes(package), toHostname, toPort
        )

        if self.pushTimer == None:
            self.pushTimer = threading.Timer(0.5, self._pushPackagesToServer).start()

        return package.uuid

    async def response(self, requestId: str) -> bytes:
        """Gets the response for the request with the given id."""
        return await self._response(requestId, time())

    async def _response(self, requestId: str, pollStartTime) -> bytes:
        """Gets the response for the request with the given id."""
        if time() - pollStartTime > 6:
            raise TimeoutError()

        if self.responses.get(requestId) != None:
            responseData = self.responses[requestId]
            del self.responses[requestId]
            return responseData

        await ftSleep(0.5)
        return await self._response(requestId, pollStartTime)

    def _pushPackagesToServer(self):
        """Runs through all the packages in the buffer and sends them all to their destination servers."""
        for _, request in self.buffer.items():
            udpSend(
                request.packageInBytes, request.toHostname, request.toPort, self.channel
            )

    def _pollResponses(self):
        while True:
            packageBytes, (_, __) = readIncomingPacket(self.channel)
            try:
                package = _packageFromBytes(packageBytes)
            except MalformedPackageError:
                continue

            del self.buffer[package.uuid]  # request has been fulfilled
            self.responses[package.uuid] = package.message


class _RequestBufferItem:
    def __init__(
        self, request: _Package, response: _Package, createdAt: float = time()
    ) -> None:
        self.request = request
        self.createdAt = createdAt
        self.response = response


class Server:
    def __init__(self, port: int) -> None:
        self.port = port
        self.onMessageCallback = None
        self.shouldClose = False
        self.requestBuffer: dict[str, _RequestBufferItem] = {}
        pass

    def listen(self) -> None:
        serverListen(self.port, self._serverListenCallback)
        pass

    def close(self) -> None:
        self.shouldClose = True

    def onMessage(self, callback: Callable[[bytes], bytes]):
        self.onMessageCallback = callback

    def _serverListenCallback(
        self, args: tuple[bytes, tuple[str, int]], channel: socket
    ) -> bool:
        self._sanitiseRequestBuffer()

        packageBytes, (clientName, clientPort) = args
        try:
            request = _packageFromBytes(packageBytes)
            response = self._makeResponse(request)
            udpSend(_packageToBytes(response), clientName, clientPort, channel)

            if self.requestBuffer.get(request.uuid) == None:
                self.requestBuffer[request.uuid] = _RequestBufferItem(request, response)

        except MalformedPackageError:
            # Ignoring corrupted package
            pass

        return self.shouldClose

    def _makeResponse(self, request: _Package) -> _Package:
        if not self._isRequestDuplicate(request):
            responseMessage = self.onMessageCallback(request.message)
            return _Package(responseMessage, request.uuid)
        else:
            return self.requestBuffer[request.uuid].response

    def _isRequestDuplicate(self, request: _Package) -> bool:
        return self.requestBuffer.get(request.uuid) != None

    def _sanitiseRequestBuffer(self) -> None:
        """Deletes all RequestBufferItems older than 30 seconds."""

        keysToRemove: list[str] = []
        for requestId, item in self.requestBuffer.items():
            if time() - item.createdAt >= 30:
                keysToRemove.append(requestId)

        for key in keysToRemove:
            del self.requestBuffer[key]
