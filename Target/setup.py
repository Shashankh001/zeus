# BASIC SETUP CODE
# Make another setup code to automatically setup the target
# This is MANUAL only.

import json
import socket
from requests import get

with open('settings.json', 'r') as f:
    data = json.load(f)

ip = str(input("Enter server IP: "))
port = int(input("Enter server port: "))
name = str(input("Enter the name of the Computer/User: "))

myip = get('https://api.ipify.org').text

print("Registering computer with the server.")

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
try:
    s.connect((ip,port))
except:
    print("Server is offline. Try again later.")
    while True:
        pass

s.send(bytes(f'SETUP|{name}|{myip}','utf-8'))

confirmation = s.recv(50).decode('utf-8')
confSplit = confirmation.split('|')

if confSplit[0] == 'Y':
    print(f"Successfully registered target with server.\nAssigned ID: {confSplit[1]}")

else:
    print("There was an error registering the client with server.")

with open('settings.json', 'w') as f:
    dataObj = {"IP":ip,"PORT":port,"NAME":name,"ID":confSplit[1]}
    data.append(dataObj)

    json.dump(data, f, indent=4)