from shutil import ExecError
import socket
import sys
import asyncio
import time
import datetime
import json
from typing import Tuple
import threading
import aioredis
import traceback
from .handlers import RequestHandlers, MESSAGES, USERS, RESPONSE_STATUS_NAMES
from ..protocol.rudp import Server

# Used to keep track of time for when the messaging clean up needs to be done
CURRENT_TIME = datetime.datetime.now()

# how often the clean up function should be run in seconds
INTERVAL_TIME = 5

# Connect to redis server
try:
    redisClient = aioredis.from_url("redis://localhost", decode_responses=True)
except:
    print(
        "Error connecting to redis server! Please ensure an instance of the redis server is running."
    )
    sys.exit(1)


# Setting up event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


async def cleanupMessages() -> None:
    """Removes messages that have been received by all active clients"""
    activeUsers = await redisClient.hgetall(USERS)
    messages = await redisClient.lrange(MESSAGES, start=0, end=1000)
    messagesToRemove = []
    now = datetime.datetime.now()
    lowestDate = now

    if len(activeUsers) == 0:
        return

    # Find lowest date
    for key in activeUsers:
        user = json.loads(activeUsers[key])
        date = datetime.datetime.fromtimestamp(user["lastMessageFetchTimestamp"])
        if date < lowestDate:
            lowestDate = date

    # Get messages to remove
    for item in messages:
        item = json.loads(item)
        date = datetime.datetime.fromtimestamp(item["timestamp"])

        if date < lowestDate:
            messagesToRemove.append(json.dumps(item))

    # Remove messages
    if lowestDate != now and len(messagesToRemove) > 0:
        for message in messagesToRemove:
            await redisClient.lrem(name=MESSAGES, count=1, value=message)


async def handleRequest(message: bytes) -> str:
    """Delegates the responsibility of handling request to the appropriate method depending on request method header

    Args:
        - message: request message
    """
    print("REceived request")
    difference = datetime.datetime.now() - CURRENT_TIME
    if difference.total_seconds() > INTERVAL_TIME:
        await cleanupMessages()
        pass

    handlers = RequestHandlers(message, redisClient)
    (error, parsedMessage) = handlers.parseMessage()

    # If there was a FORMAT-ERROR
    if error:
        return parsedMessage

    if "Method" not in parsedMessage:
        return handlers.setResponseMessage(
            RESPONSE_STATUS_NAMES["unsupportedMethod"],
            "Ensure that the method is specified in the request",
        )

    method = parsedMessage["Method"]

    if method == "FETCH":
        try:
            print("Fetch called")
            data = json.loads(parsedMessage["Data"])
            print("Fetch called", data)
            return await handlers.fetchMessages(data["timestamp"], data["username"])
        except:
            return handlers.setResponseMessage(
                RESPONSE_STATUS_NAMES["dataRequired"],
                "Ensure that timestamp exists within the data body line",
            )

    elif method == "MESSAGE":
        try:
            data = json.loads(parsedMessage["Data"])
            return await handlers.storeMessage(data["message"], data["username"])
        except:
            return handlers.setResponseMessage(
                RESPONSE_STATUS_NAMES["dataRequired"],
                "Ensure that message exists within the data body line",
            )

    elif method == "EXIT":
        try:
            data = json.loads(parsedMessage["Data"])
            print("exit data", data, type(data))
            return await handlers.removeUser(data["username"])
        except:
            return handlers.setResponseMessage(
                RESPONSE_STATUS_NAMES["dataRequired"],
                "Ensure that username exists within the data body line",
            )

    elif method == "LOGIN":
        try:
            print(parsedMessage)
            data = json.loads(parsedMessage["Data"])
            return await handlers.loginUser(data["username"])
        except:
            return handlers.setResponseMessage(
                RESPONSE_STATUS_NAMES["dataRequired"],
                "Ensure that username exists within the data body line",
            )

    else:
        return handlers.setResponseMessage(
            RESPONSE_STATUS_NAMES["unsupportedMethod"], "Provided method is unsupported"
        )

def requestMessageWrapper(message: bytes) -> bytes:
    """Used to launch the response in the event loop

    Args:
        - message: request message bytes

    Returns:
        - response message
    """
    return (loop.run_until_complete(handleRequest(message))).encode()

# Create socket and binding used for testing
try:
    port = 8000
    server = Server(port)
    server.onMessage(requestMessageWrapper)
    print("Server is listening...")
    server.listen()

    # serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # serverSocket.bind(("", port))
    # print("Server is running...")
    # print("Port:", port)
except Exception as error:
    print(traceback.extract_stack())
    print(error)
    print("Error creating socket and binding to the address")
    sys.exit(1)



# while True:
#     message, address = serverSocket.recvfrom(1024)
#     test = requestMessageWrapper(message)
#     serverSocket.sendto(test, address)
