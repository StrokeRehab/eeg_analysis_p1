# coding=utf8
import asyncio
import gizmoHttpClient
import argparse
import sys
import aiohttp

# IP of this base station
# BASE_IP = '10.65.70.129'
# BASE_IP = '127.0.0.1'

# seconds between commands
COMMAND_INTERVAL = 0.5
# PORT the EEG classification program is sending to
EEG_PORT = None

# Port that Gizmo's head direction program is sending to
GIZMO_PORT = None
# IP of this base station

GIZMO_DIRECTOR_PORT = None
GIZMO_IP = None

NUM_STEPS = 100

# 1 byte messages (just receiving booleans)
MSG_SIZE = 1

# global variables used in logic for commanding gizmo
# These variables represent the latest boolean received from each TCP server
isJawClenched = False
isFacingGizmo = True


def isBoolean(msg):
    return msg.lower() in ['true', 'false', '0', '1', 't', 'f']


def toBoolean(msg):
    return msg.lower() in ['true', '1', 't']


async def getMessage(reader):
    msg = await reader.read(MSG_SIZE)

    return msg.decode().rstrip()

# Read 1 byte from the TCP socket. We expect either 1 or 0 representing true or false respectively
# If the message is correctly formatted. update the corresponding global variable


async def collect_latest_jaw_clench_data(reader, writer):
    while (True):
        msg = await getMessage(reader)

        if msg and isBoolean(msg):
            global isJawClenched
            isJawClenched = toBoolean(msg)

# Read 1 byte from the TCP socket. We expect either 1 or 0 representing true or false respectively
# If the message is correctly formatted. update the corresponding global variable


async def collect_latest_head_direction_data(reader, writer):
    while (True):
        msg = await getMessage(reader)
        if msg and isBoolean(msg):
            global isFacingGizmo
            isFacingGizmo = toBoolean(msg)


# Create the TCP server that will recieve messages from the EEG classification program
async def eeg_server():
    # For every new TCP connection to this server, a new task is created and runs the
    # input function in the start_server() call
    server = await asyncio.start_server(collect_latest_jaw_clench_data, port=EEG_PORT)
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')
    # this task never terminates unless explicitly told to
    async with server:
        await server.serve_forever()

# Create the TCP server that will recieve messages from the head direction program on Gizmo


async def gizmo_server():
    # For every new TCP connection to this server, a new task is created and runs the
    # input function in the start_server() call
    server = await asyncio.start_server(collect_latest_head_direction_data, port=GIZMO_PORT)
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')
    # this task never terminates unless explicitly told to
    async with server:
        await server.serve_forever()


async def determineCommand(isJawClenched, isFacingGizmo, gizmoClient):
    # if patient sees gizmo
    if isJawClenched and isFacingGizmo:
        await gizmoClient.goForward(NUM_STEPS)
        # move farther forward
    # else if patient is looking at gizmo but doesnt see it
    elif not isJawClenched and isFacingGizmo:
        # move backward
        await gizmoClient.goBackward(NUM_STEPS)
    # else, patient not looking at gizmo! stop gizmo until they look again
    else:
        # stop
        await gizmoClient.stop()


async def direct_gizmo(gizmoClient):
    # writer = await asyncio.open_connection(GIZMO_IP, GIZMO_PORT)
    while (True):
        await asyncio.sleep(COMMAND_INTERVAL)
        print('isJawClenched = ' + str(isJawClenched))
        print('isFacingGizmo = ' + str(isFacingGizmo))
        await determineCommand(isJawClenched, isFacingGizmo, gizmoClient)


def parseArgs():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-ga", "--gizmo_address",
                           help="gizmo IP address", required=True)
    argParser.add_argument(
        "-gp", "--gizmo_port", help="Gizmo face-pose estimation TCP server port", required=True)
    argParser.add_argument(
        "-ep", "--eeg_port", help="EEG classification TCP server port", required=True)
    argParser.add_argument("-gdp", "--gizmo_director_port",
                           help="port to server on gizmo that takes directions", required=True)
    global EEG_PORT
    global GIZMO_PORT
    global GIZMO_DIRECTOR_PORT

    args = argParser.parse_args()
    EEG_PORT = args.eeg_port
    GIZMO_PORT = args.gizmo_port
    GIZMO_DIRECTOR_PORT = args.gizmo_director_port
    global GIZMO_IP
    GIZMO_IP = args.gizmo_address


async def main():
    parseArgs()

    gizmoClient = gizmoHttpClient.GizmoHttpClient(
        GIZMO_IP, GIZMO_DIRECTOR_PORT)
    # Initially, three tasks are created. However, for each client that connects to a server
    # another task will be generated
    async with asyncio.TaskGroup() as tg:
        eeg_server_task = tg.create_task(eeg_server())
        gizmo_server_task = tg.create_task(gizmo_server())
        direct_gizmo_task = tg.create_task(direct_gizmo(gizmoClient))
        # take keyboard input tasks (to shut it down)


# I am using asyncio, because it allows me to create multiple tasks and run them concurrently

# The big idea is that there is a loop that contains all the tasks. When a task is ready to run
# it will be given control until it voluntarily gives up control through an "await" keyword.
# These keywords are used whenever calling a function labeled with "async"
# Tasks will not be chosen to run if they are sleeping or waiting for IO
if __name__ == '__main__':
    asyncio.run(main())
