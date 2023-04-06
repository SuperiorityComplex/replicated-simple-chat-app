import threading
import optparse
import grpc
import sys
import concurrent.futures
import time
import random
import json
sys.path.append('./grpc_stubs')
import main_pb2
import main_pb2_grpc

def listen_client_messages(stub, username):
    """
    Receives async messages from other clients.
    """
    messages = stub.ClientChat(main_pb2.Username(username=username))

    try:
        while True:
            m = next(messages)
            print(m.message)
    except:
        return

def main():
    listen_thread = None
    
    # TODO: need to write some kind of function which connects to the leader
    # while loop, wait 5 sec then try connecting in round robin
    # --> if server down, connection fails
    # --> if not leader, server will refuse the connection
    # --> keep going until you are connected to the leader server
    host = "127.0.0.1"
    port = "3000"

    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = main_pb2_grpc.ChatterStub(channel)

    print("Enter username (will be created if it doesn't exist): ", flush = True)
    while True:
        username = input()
        if (not username):
            continue
        break

    response = stub.ServerChat(
        main_pb2.UserRequest(action="join", username=username, recipient="", message="")
    )
    print(response.message, flush = True)

    # user logged in elsewhere, end client
    if ('Already logged in' in response.message):
        return

    listen_thread = threading.Thread(target=(listen_client_messages), args=(stub, username))
    listen_thread.start()

    print("Actions: list, send <user>, delete <user>, quit", flush = True)

    try:
        # client ui loop, cannot pass stub as function argument so it all goes here
        while True:
            action = input("> ")
            
            action_list = action.split()

            if (len(action_list) == 0):
                continue
            
            elif (action_list[0] == "list"):
                response = stub.ServerChat(
                    main_pb2.UserRequest(action=action_list[0], username=username, recipient='', message="")
                )

            elif (action_list[0] == "send"):
                if (len(action_list) < 2):
                    print("Must specify valid user to send to. Try again.", flush = True)
                    continue
                print("Message to send to {user}?".format(user=' '.join(action_list[1:])))

                while True:
                    message = input(">>> ")
                    if (not message):
                        continue
                    break

                response = stub.ServerChat(
                    main_pb2.UserRequest(action=action_list[0], username=username, recipient=' '.join(action_list[1:]), message=message)
                )

            elif (action_list[0] == "delete"):
                if (len(action_list) != 2):
                    print("Must specify valid user to delete. Try again.", flush = True)
                    continue
                if (username == ' '.join(action_list[1:])):
                    print("Cannot delete self user.", flush = True)
                    continue
                response = stub.ServerChat(
                    main_pb2.UserRequest(action=action_list[0], username=' '.join(action_list[1:]), recipient='', message="")
                )

            elif (action_list[0] == "quit"):
                response = stub.ServerChat(
                    main_pb2.UserRequest(action=action_list[0], username=username, recipient='', message="")
                )
                return

            else:
                print("Unrecognized action.", flush = True)
                continue

            print(response.message, flush = True)
    
    # TODO: the server we were connected to has gone down, we need to connect to another server
    # except:
    #     pass

    # TODO: the server we were connected to is no longer the leader, we need to connect to another server


    except KeyboardInterrupt:
        # send quit to server
        response = stub.ServerChat(
            main_pb2.UserRequest(action="quit", username=username, recipient='', message="")
        )
        listen_thread.join()

    listen_thread.join()
    
    print("Shutting down.")
    return

if __name__ == '__main__':
    main()