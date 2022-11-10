"""Implements a demo RUDP client"""

from .rudp import Client
import asyncio


async def main():
    client = Client()

    while True:
        text = input("Enter any string: ")
        if text == "q" or text == 'Q':
            break

        message = text.encode()

        requestId = client.send(message, "127.0.0.1", 8000)
        response = await client.response(requestId)

        print("Server returned: "+response.decode())

    client.channel.close()

asyncio.run(main())
