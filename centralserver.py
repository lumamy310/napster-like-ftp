import os
import socket
import threading
import csv
import random


def central_server(central_server_socket):
    # receive command port (metadata) from client and connect command socket
    command_port = int(central_server_socket.recv(buffer_size).decode('ascii'))
    command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    command_socket.connect((server_ip, command_port))

    # receive client's metadata and store in a temp csv file
    fileNumber = random.randrange(1, 9999999999999999999999)
    fileName = 'temp' + str(fileNumber) + '.csv'

    # ensure the file does not already exist
    files = os.listdir('./serverContent')
    files = [f for f in files if os.path.isfile('./serverContent/' + fileName)]
    files = [f for f in files if not f.startswith('.')]
    while fileName in files:
        fileNumber = random.randrange(1, 9999999999999999999999)
        fileName = 'temp' + str(fileNumber) + '.csv'

    # write host's metadata to a file
    with open('serverContent/' + fileName, 'wb') as f:
        chunk = command_socket.recv(buffer_size)
        while chunk:
            f.write(chunk)
            chunk = command_socket.recv(buffer_size)

    # open the file and print user connected
    with open('serverContent/' + fileName, 'r', newline='') as f:
        reader = csv.reader(f)
        user = next(reader)
        active_user = user[0]
        print(active_user + " connected")

    # at this point, our server has all the metadata from the
    # connected user.
    receive_command(central_server_socket, active_user, fileName)


def receive_command(central_server_socket, active_user, fileName):
    # create command port to handle transfer of metadata
    command_port = int(central_server_socket.recv(buffer_size).decode('ascii'))
    command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    command_socket.connect((server_ip, command_port))

    # RECEIVE COMMANDS
    command = central_server_socket.recv(buffer_size).decode('ascii')
    if len(command.split(' ')) == 1:
        # QUIT
        # Remove the host's metadata, close sockets
        os.remove('./serverContent/' + fileName)
        command_socket.close()
        central_server_socket.close()
        print(active_user + " has disconnected")
        return

    else:
        commandParsed = command.split(' ')
        # SEARCH
        if commandParsed[0] == 'SEARCH':

            files = os.listdir('./serverContent')
            files = [f for f in files if os.path.isfile('./serverContent/' + f)]
            files = [f for f in files if not f.startswith('.')]

            searched = []
            keywords = commandParsed[1].split(',')
            for f in files:
                with open('serverContent/' + f, 'r', newline='') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        terms = row[5].split(' ')
                        added = False
                        for keyword in keywords:
                            if keyword in terms:
                                searched.append(
                                    "Hostname: " + row[1] + " Port: " + row[2] + " Filename: " + row[4] + " Speed: " +
                                    row[
                                        3] + '/')
                                added = True
                        if added:
                            continue
            searched = ''.join(searched)
            command_socket.send(searched.encode('ascii'))

        else:
            # GET
            pass

    command_socket.close()
    receive_command(central_server_socket, active_user, fileName)


# server parameters
server_ip = 'localhost'
server_port = 8907
buffer_size = 1024

# create server welcome socket, bind, and listen
welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
welcome_socket.bind((server_ip, server_port))
welcome_socket.listen()

print('The server is ready to communicate')

# accept incoming connections and multithreading
while True:
    central_server_socket, addr = welcome_socket.accept()
    threading.Thread(target=central_server, args=(central_server_socket,)).start()
