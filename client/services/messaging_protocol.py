"""This module implements the client side of the messaging protocol for Chatter."""

import json
from typing import Any
from ...protocol.rudp import Client

# from protocol.rudp import Client


class Request:
    def __init__(self, method: str, data: dict[str, Any]) -> None:
        self.method = method
        self.data = data
        pass

    def toString(self) -> str:
        dataLine = ""
        if self.data != None:
            dump = json.dumps(self.data)
            dataLine = "Data: " + dump + ""

        return f"Method: {self.method}\n{dataLine}"


class Response:
    def __init__(self, statusName: str, statusMessage: str, data: Any) -> None:
        self.statusName = statusName
        self.statusMessage = statusMessage
        self.data = data


def _parseResponse(responseString: str) -> Response:
    lines = responseString.split("\n")
    print(lines)
    statusName = lines[0][lines[0].index(":") + 1 :].strip()
    statusMessage = lines[1][lines[1].index(":") + 1 :].strip()
    print(lines[2])
    dataStr = lines[2][lines[2].index(":") + 1 :].strip()
    print("data", dataStr)
    print("data", type(dataStr))

    return Response(statusName, statusMessage, json.loads(dataStr))


def _throwIfResponseIsError(response: Response) -> None:
    if response.statusName != "SUCCESS":
        raise response.statusMessage


client = Client()

SERVER_NAME = "127.0.0.1"
# SERVER_NAME = "172.20.10.3"
SERVER_PORT = 8000


async def send(method: str, data: dict[str, Any]) -> Any:
    request = Request(method, data)
    requestId = client.send(request.toString().encode(), SERVER_NAME, SERVER_PORT)
    print("request string", request.toString())
    responseString = (await client.response(requestId)).decode()
    response = _parseResponse(responseString)
    _throwIfResponseIsError(response)

    return response.data
