"""This module allows the client to send and receive Chatter texts.

   Chatter only supports a single chat room at the moment. This is called
   the default chat room. This all messages can only be sent to that single
   chat room.

   The routines in this module are thread safe and can be called from different
   threads.
"""

from time import time
from .messaging_protocol import send as msgSend
from .authentication import clientName


class ChatMessage:
    """A ChatMessage stores the text of a message as well as the username of the user
    that sent it.

    ChatMessages should not be confused with protocol messages.
    """

    def __init__(self, sender: str, text: str) -> None:
        self.sender = sender
        self.text = text

    def toString(self) -> str:
        return self.sender + ": " + self.text


async def send(text: str) -> None:
    """Sends the given text to the default chat room.

    Throws error if authentication.login() has not been called.
    """
    print("name", clientName["name"])
    await msgSend("MESSAGE", {"message": text, "username": clientName["name"]})


_lastFetchTime = time()


async def getAllUnreadMessages() -> list[ChatMessage]:
    """Returns all the messages in the default chat room posted since the last time
    this routine was called.

    The messages are returned in the order they were sent by the other users.

    This routine should be called periodically to ensure that the user sees the messages
    as they are posted by the other users.

    Throws error if authentication.login() has not been called.
    """
    global _lastFetchTime
    messages: list[dict[str, str]] = await msgSend(
        "FETCH", {"timestamp": _lastFetchTime, "username": clientName["name"]}
    )

    if len(messages) > 0:
        _lastFetchTime = time()

    out: list[ChatMessage] = []
    for msg in messages:
        chatMessage = ChatMessage(sender=msg["username"], text=msg["message"])
        print("RECEIVED message-> ", chatMessage.toString())
        out.append(chatMessage)

    return out
