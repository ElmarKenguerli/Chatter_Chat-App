import redis
import math
import json
from typing import Tuple, Dict, Union
import datetime
import socket

# Used to find/store items into redis
MESSAGES = "messages"  # for storing messages
USERS = "users"  # for storing active users

# Possibles RESPONSE_STATUS_NAMES the server can respond with
RESPONSE_STATUS_NAMES = {
    "authorizationError": "AUTHORIZATION-ERROR",
    "dataRequired": "DATA-REQUIRED",
    "unsupportedMethod": "UNSUPPORTED-METHOD",
    "formatError": "FORMAT-ERROR",
    "success": "SUCCESS",
}

""" Responsible for providing an interface to respond to a clients request

"""


class RequestHandlers:
    def __init__(self, message: bytes, redisClient: redis):
        """Constructor method

        Args:
            message: contents of request from client
            redisClient: connection to the redis client
        """
        self.message = message.decode()
        self.redisClient = redisClient

    async def loginUser(self, username: str) -> str:
        """Logs in user by labelling them as an active user

        Args:
            username: identifier used for user

        Returns:
            None
        """
        activeUsers = await self.redisClient.hgetall(USERS)

        # Ensure user is not already active
        for key in activeUsers:
            if key == username:
                return self.setResponseMessage(
                    RESPONSE_STATUS_NAMES["authorizationError"],
                    "Username is already taken",
                )

        await self.redisClient.hset(
            USERS,
            username,
            json.dumps(
                {
                    "lastMessageFetchTimestamp": datetime.datetime.now().timestamp(),
                }
            ),
        )

        test = self.setResponseMessage(
            RESPONSE_STATUS_NAMES["success"],
            "Successfully authorized",
            {"username": username},
        )
        print(test)
        return test

    async def isAuthorized(self, username: str) -> Tuple[bool, str]:
        """Checks if the client making a request has already been authenticated

        Returns:
            - tuple containing authentication bool value & potential response message: (bool, str)
        """
        activeUsers = await self.redisClient.hgetall(USERS)
        authenticated = False
        responseMessage = ""

        for key in activeUsers:
            if username == key:
                authenticated = True

        if not authenticated:
            responseMessage = self.setResponseMessage(
                RESPONSE_STATUS_NAMES["authorizationError"],
                "Please perform LOGIN request to be authorized",
            )

        return (authenticated, responseMessage)

    async def fetchMessages(self, timestamp: float, username: str) -> str:
        """Retrieves messages whose timestamp is greater than the one provided ands sends them to the client

        Args:
            timestamp: date & time timestamp

        Returns:
            - response message
        """
        (authenticated, errorMessage) = await self.isAuthorized(username)

        if not authenticated:
            return errorMessage

        messages = await self.redisClient.lrange(MESSAGES, start=0, end=1000)
        now = datetime.datetime.now().timestamp()
        newMessages = []

        # Get messages
        for item in messages:
            item = json.loads(item)
            date = datetime.datetime.fromtimestamp(item["timestamp"])

            if date > datetime.datetime.fromtimestamp(timestamp):
                newMessages.append(item)

        # Update active user details, reflecting latest fetch timestamp
        activeUser = json.loads(await self.redisClient.hget(USERS, username))
        details = {
            "lastMessageFetchTimestamp": now,
        }
        await self.redisClient.hset(name=USERS, key=username, value=json.dumps(details))

        sortedMessages = sorted(newMessages, key=lambda x: x["timestamp"])
        return self.setResponseMessage(
            RESPONSE_STATUS_NAMES["success"],
            "Successfully fetched messages",
            sortedMessages,
        )

    async def storeMessage(self, message: str, username: str) -> str:
        """Store message sent by client

        Args:
            - message to be stored

        Returns:
            - response message
        """
        (authenticated, errorMessage) = await self.isAuthorized(username)

        if not authenticated:
            return errorMessage

        messageDetails = {
            "username": username,
            "timestamp": datetime.datetime.now().timestamp(),
            "message": message,
        }

        await self.redisClient.lpush(MESSAGES, json.dumps(messageDetails))
        return self.setResponseMessage(
            RESPONSE_STATUS_NAMES["success"],
            "Successfully stored message",
            {"username": username},
        )

    async def removeUser(self, username: str) -> str:
        """Removes the user with the provided address (from constructor)

        Returns:
            - response message
        """
        (authenticated, errorMessage) = await self.isAuthorized(username)

        if not authenticated:
            return errorMessage

        await self.redisClient.hdel(USERS, username)
        return self.setResponseMessage(
            RESPONSE_STATUS_NAMES["success"], "Successfully removed user", {"username": username},
        )

    def setResponseMessage(self, name: str, message: str, data=None) -> str:
        """Setting the response message to be sent back to client

        Args:
            - name: status name
            - message: status message
            - data: response data

        Returns:
            - response message
        """
        response = ""
        response += f"Status-name: {name}\n"
        response += f"Status-message: {message}\n"

        if data is not None:
            response += f"Data: {json.dumps(data)}"

        return response

    def parseMessage(self) -> Tuple[bool, Union[str, Dict[str, str]]]:
        """Parses the request message consisting of key/value pairs and returns a Dict of these values

        Returns:
            - Tuple having an error bool value with either a dictionary or response message
        """
        message = self.message
        splitMessage = message.split("\n")
        result = {}

        try:
            for item in splitMessage:
                if len(item) > 0:
                    splitItem = item.split(":", maxsplit=1)
                    result[splitItem[0].strip()] = splitItem[1].strip()

            return (False, result)
        except:
            responseMessage = self.setResponseMessage(
                RESPONSE_STATUS_NAMES["formatError"],
                "Format of request is not parsable",
            )
            return (True, responseMessage)
