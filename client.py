import random
import socket
import os
import csv
import sys
import threading


def connect_to_central():
    # create connection socket for central server
    central_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # attempt to connect
    print("All files in the clientContent folder will be available for download by peers!\n")
    command = input("Please connect to the central server by typing: CONNECT <server name/IP address> <server port>\n")
    command = command.split(' ')

    if len(command) < 3 or command[0] != 'CONNECT':
        connect_to_central()

    # if right format, try to connect
    try:
        central_server_socket.connect((command[1], int(command[2])))
    # if unable to connect, try again
    except:
        print('Could not connect.')
        connect_to_central()

    # begin sending commands
    connected(central_server_socket)


def connected(central_server_socket):
    # create command socket to handle metadata transfer
    central_server_socket.send(str(command_port).encode('ascii'))
    command_socket, addr = welcome_socket2.accept()

    # get username, hostname, connection speed
    username = input("Please enter your username: ")
    connection_speed = input("Please enter your connection speed: ")

    # iterate through files in clientContent and make user add description for each
    # create an array of file names
    files = os.listdir('./clientContent')
    files = [f for f in files if os.path.isfile('./clientContent/' + f)]
    files = [f for f in files if not f.startswith('.')]
    # create an array of keywords
    keywords = []
    for f in files:
        keyword = input("Please enter keywords (seperated by space) for " + f + ":")
        keywords.append(keyword)
    # write initial info, ip(localhost), filename, keywords to csv file
    with open('myFiles.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        # hostname = socket.gethostname()
        # IPAddr = socket.gethostbyname(hostname)
        for f in files:
            writer.writerow([username, 'localhost', new_port, connection_speed, f, keywords[files.index(f)]])
    # send csv of our initial info, files, and keywords to central server
    with open('myFiles.csv', 'rb') as f:
        chunk = f.read(buffer_size)
        while chunk:  # chunk == '' indicates EOF from file
            command_socket.send(chunk)
            chunk = f.read(buffer_size)
    # CSV FORMAT (name = myFiles):
    # username, hostname, port, speed, filename, keywords

    # at this point, our client has sent all its metadata to server
    command_socket.close()
    send_command(central_server_socket)


def send_command(central_server_socket):
    # send the central server a port for our command(metadata) socket
    central_server_socket.send(str(command_port).encode('ascii'))
    command_socket, addr = welcome_socket2.accept()

    # COMMANDS
    command = input(
        "Connected to server. Please enter a command (SEARCH <keyword,keyword,...> GET <filename> or QUIT\n")
    commandParsed = command.split(' ')
    while len(commandParsed) > 2:
        command = input("Please enter a valid command\n")
        commandParsed = command.split(' ')
    if len(commandParsed) == 1:
        while commandParsed[0] not in oneCommands:
            command = input("Please enter a valid command\n")
            commandParsed = command.split(' ')
            if len(commandParsed) == 2 and commandParsed[0] in twoCommands:
                break
    if len(commandParsed) == 2:
        while commandParsed[0] not in twoCommands:
            command = input("Please enter a valid command\n")
            commandParsed = command.split(' ')
            if len(commandParsed) == 1 and commandParsed[0] in oneCommands:
                break

    # QUIT
    if len(commandParsed) == 1:
        if command == 'QUIT':
            central_server_socket.send(command.encode('ascii'))
            central_server_socket.close()
            command_socket.close()
            sys.exit()

    # SEARCH and GET
    else:
        if commandParsed[0] == 'SEARCH':
            central_server_socket.send(command.encode('ascii'))
            files = command_socket.recv(buffer_size).decode('ascii')
            files = files.split('/')
            for f in files:
                print(f)
        elif commandParsed[0] == 'GET':
            # Let the central server know we are getting
            central_server_socket.send(command.encode('ascii'))
            # create a control socket for sending filename to host
            control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # enter location to connect to
            dest = input("Please specify <host port file>:")
            while len(dest.split(' ')) != 3:
                print("Invalid input.")
                dest = input("Please specify <host port file>:")

            dest = dest.split(' ')

            # connect to host
            try:
                control_socket.connect((dest[0], int(dest[1])))
            except:
                print("Could not connect.")
                command_socket.close()
                control_socket.close()
                send_command(central_server_socket)

            # send the host our data port (for sending/receiving file)
            control_socket.send(str(data_port).encode('ascii'))
            data_socket, addr = welcome_socket3.accept()
            # send file name over control socket
            control_socket.send(dest[2].encode('ascii'))

            # receive and write the file
            with open('clientContent/' + commandParsed[1], 'wb') as f:
                chunk = data_socket.recv(buffer_size)
                try:
                    if chunk.decode('ascii') == 'File not found.':
                        print("File not found.")
                    else:
                        while chunk:
                            f.write(chunk)
                            chunk = data_socket.recv(buffer_size)
                        print("Downloaded.\n")
                except UnicodeDecodeError:
                    while chunk:
                        f.write(chunk)
                        chunk = data_socket.recv(buffer_size)
                    print("Downloaded.\n")
            data_socket.close()
            control_socket.close()

    command_socket.close()
    send_command(central_server_socket)


def send_file(control_socket):
    # receive the data port and connect ot hosts data socket
    data_port = int(control_socket.recv(buffer_size).decode('ascii'))
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((server_ip, data_port))
    # accept file name
    command = control_socket.recv(buffer_size).decode('ascii')
    # open file and send to host
    try:
        with open('clientContent/' + command, 'rb') as f:
            chunk = f.read(buffer_size)
            while chunk:  # chunk == '' indicates EOF from file
                data_socket.send(chunk)
                chunk = f.read(buffer_size)
    except FileNotFoundError:
        response = 'File not found.'
        data_socket.send(response.encode('ascii'))

    data_socket.close()
    control_socket.close()


# only valid commands
oneCommands = ['QUIT']
twoCommands = ['SEARCH', 'GET']

# info for server
server_ip = 'localhost'
new_port = random.randrange(1000, 8000)
buffer_size = 1024
welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
welcome_socket.bind((server_ip, new_port))
welcome_socket.listen()

# info for command socket
command_port = random.randrange(1000, 8000)
welcome_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
welcome_socket2.bind((server_ip, command_port))
welcome_socket2.listen()

# info for data socket
data_port = random.randrange(1000, 8000)
welcome_socket3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
welcome_socket3.bind((server_ip, data_port))
welcome_socket3.listen()

# start client thread
threading.Thread(target=connect_to_central).start()
# start server thread
while True:
    control_socket, addr = welcome_socket.accept()
    threading.Thread(target=send_file, args=(control_socket,)).start()
