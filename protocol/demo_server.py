
"""An example RUDP server.

   The server accepts bytes, decodes them into a string, makes uppercase the
   string and sends back the upper case string in bytes.
"""

from .rudp import Server


def messageHandler(message: bytes) -> bytes:
    string = message.decode()
    print("Server received: "+string)
    return string.upper().encode()


server = Server(8000)
server.onMessage(messageHandler)
server.listen()
