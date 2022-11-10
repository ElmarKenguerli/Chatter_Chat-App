"""
This is the Chatter Client that users will interact with to send and receive messages.
GUI interface.
"""
import asyncio
import tkinter as tk
import PySimpleGUI as sg
from threading import Thread
from .services.chats import send as chatSend, getAllUnreadMessages
from .services.authentication import *
from random import randint
from tkinter import font
from PySimpleGUI.PySimpleGUI import Multiline

usrName = ""
chatPage = sg.Window("dummy")


async def main():
    #Runs the GUI main thread    
    await gui()


async def gui():
    #The main GUI thread. Responsible for creating, displaying and showing updates to the GUI.
    
    async def recieveMessages():
        #Displays all unread messages by the user
        while True:
            unreadChats = await getAllUnreadMessages()
            for chat in unreadChats:
                print(chat.toString())
                chatPage['textbox'].update(
                    chatPage['textbox'].get() + "\n" + chat.toString())
                chatPage.refresh()

    def receiveMessagesBridge():
        asyncio.run(recieveMessages())

    sg.theme('LightPurple')
    fontMain = ("Arial, 35")
    fontUsr = ("Arial, 18")
    
    #Creating layouts for Main and Chat screens
    layout = [
        [sg.Text('Welcome to Chatter', justification='center',
                 font=fontMain, pad=(180, 80))],
        [sg.Text('Enter Username', justification='center',
                 font=fontUsr, pad=(300, 0))],
        [sg.Input(justification='center', size=(60, 2), pad=(245, 10))],
        [sg.Button('Login', size=(40, 4), pad=(
            225, 30), bind_return_key=True)],
        [sg.Button('Exit', size=(15, 2), pad=(330, 15))]
    ]
    welcomePage = sg.Window(
        "Chatter", layout, size=(800, 500), grab_anywhere=True)

    layoutChat = [
        [sg.Text('Chat Room', justification='center',
                 font=fontMain, pad=(260, 30))],
        [[sg.Button('Connect To Room', size=(30, 3),
                    key=('connect'), enable_events=True)]],
        [sg.Multiline(size=(160, 15), key='textbox')],
        [sg.Text('Send Message', size=(15, 1)), sg.InputText(
            size=(80, 0), pad=(0, 25), key='msgInput', do_not_clear=False)],
        [sg.Button('Send', size=(30, 2), pad=(250, 0), bind_return_key=True)]

    ]
    
    global chatPage
    chatPage = sg.Window("Chatter", layoutChat,
                         size=(800, 550), grab_anywhere=True)
    #Reading events or changes to the GUI
    while True:
        event, values = welcomePage.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        if event == "Login":
            usrName = values[0]
            if usrName == "":
                usrName = "Guest" + str(randint(100, 999))
                sg.popup("Your username will be: " + usrName)

            # Login and setup communication with server
            loggedIn = await login(usrName)

            break
    welcomePage.close()

    count = 0
    if loggedIn == True:
        #Reading events or changes to the GUI
        while True:
            event, values = chatPage.read()

            if count == 0:
                #New background thread for receiving messages 
                t1 = Thread(target=receiveMessagesBridge)
                t1.daemon = True
                t1.start()
                count = 1

            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            #Send Messages
            if event == "Send":
                chatMsg = values['msgInput']

                print(usrName + chatMsg)
                await chatSend(chatMsg)


        chatPage.close()

    else:
        Multiline.update(
            "Could not establish link with Server. Please restart.")
    exit()

# run client
if __name__ == '__main__':
    asyncio.run(main())
