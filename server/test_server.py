import unittest
import json
import datetime
import time
import threading
from typing import List
import random
from socket import *

# Number of clients to simulate
NUMBER_OF_CLIENTS = 100

def loginRequestSender(message:str, username:str):
    """Sends a login request and checks the response"""
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    t = time.time()
    serverSocket.sendto(message.encode(), ("", 8000))
    message, address = serverSocket.recvfrom(2048)
    print("login response time:", time.time() - t)
    message = message.decode()
    expectedMessage = "Status-name: SUCCESS\nStatus-message: Successfully authorized\nData: {\"username\": \"%s\"}" % username
    if(expectedMessage != message):
        serverSocket.close()
        raise ValueError("Login request: expected message not the same as actual message")
    serverSocket.close()


def messageRequestSender(message:str, username:str):
    """Sends a message request and checks the response"""
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    t = time.time()
    serverSocket.sendto(message.encode(), ("", 8000))
    message, address = serverSocket.recvfrom(2048)
    print("message response time:", time.time() - t)
    message = message.decode()
    expectedMessage = "Status-name: SUCCESS\nStatus-message: Successfully stored message\nData: {\"username\": \"%s\"}" % username
    if(expectedMessage != message):
        serverSocket.close()
        raise ValueError("Message request: Expected message not the same as actual message")
    serverSocket.close()

def fetchRequestSender(message:str, username:str):
    """Sends a fetch request and checks the response"""
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    t = time.time()
    serverSocket.sendto(message.encode(), ("", 8000))
    message, address = serverSocket.recvfrom(2048)
    print("fetch response time:", time.time() - t)
    message = message.decode()
    splitMessage = message.split("\n")
    try:
        splitMessage[0].index("SUCCESS")
    except :
        serverSocket.close()
        raise ValueError("Fetch request: Expected message not the same as actual message")

    serverSocket.close()

def exitRequestSender(message:str, username:str):
    """Sends a exit request and checks the response"""
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    t = time.time()
    serverSocket.sendto(message.encode(), ("", 8000))
    message, address = serverSocket.recvfrom(5*1024)
    print("exit response time:", time.time() - t)
    message = message.decode()
    expectedMessage = "Status-name: SUCCESS\nStatus-message: Successfully removed user\nData: {\"username\": \"%s\"}" % username
    if(expectedMessage != message):
        serverSocket.close()
        raise ValueError("Exit request: Expected message not the same as actual message")
    serverSocket.close()

def launchThreads(method:str, usernames:List[str], function):
    """Creates threads which are clients that would send the request using the function and method specified """
    threads = []
    for username in usernames:
        message = "Method: {}\nData: {}\n".format(method, json.dumps({"username":username, "message":"Hello guys", "timestamp":datetime.datetime.now().timestamp()-0.001}))
        thread = threading.Thread(target=function, args=(message,username))
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


class ServerTests(unittest.TestCase):
    
    def setUp(self):
        self.usernames = [str(random.randrange(1000000)) for i in range(NUMBER_OF_CLIENTS)]

    def test_login(self):
        launchThreads("LOGIN", self.usernames, loginRequestSender)

    def test_message(self):
        launchThreads("LOGIN", self.usernames, loginRequestSender)
        launchThreads("MESSAGE", self.usernames, messageRequestSender)

    def test_fetch(self):
        threads = []
        launchThreads("LOGIN", self.usernames, loginRequestSender)
        launchThreads("MESSAGE", self.usernames, messageRequestSender)
        launchThreads("FETCH", self.usernames, fetchRequestSender)

    def test_exit(self):
        launchThreads("LOGIN", self.usernames, loginRequestSender)
        launchThreads("EXIT", self.usernames, exitRequestSender)



if __name__ == "___main___":
    unittest.main()
