"""This module allows the client to authenticate with the server.
"""

from .messaging_protocol import *

clientName = {"name": ""}


async def login(username: str) -> bool:
    """Logs the user in with the server.

    The client should call this routing before allowing the user to send messages.

    The server uses usernames to let other users know where messages come from.
    """
    global clientName
    clientName["name"] = username
    await send("LOGIN", {"username": username})
    return True
