import threading
import grpc
import sys
import time
sys.path.append('./grpc_stubs')
import main_pb2
import main_pb2_grpc

# addresses of the three possible servers
# server_list = ["127.0.0.1:3000", "127.0.0.1:3001", "127.0.0.1:3002"]
server_list = ["ec2-3-94-255-24.compute-1.amazonaws.com:3000", "ec2-54-157-22-244.compute-1.amazonaws.com:3000", "ec2-18-212-128-246.compute-1.amazonaws.com:3000"]

class UnavailableReplica(Exception):
    "Raised when the replica is unavailable and the client should retry."
    pass

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

def find_leader():
    """
    Finds which server is the leader.
    """
    channel = None
    stub = None
    connected_to_leader = False
    while not connected_to_leader:
        for i, addr in enumerate(server_list):
            try:
                channel = grpc.insecure_channel(addr)
                stub = main_pb2_grpc.ChatterStub(channel)

                # ask server who leader is
                resp = stub.LeaderCheck(main_pb2.LeaderRequest())
                return resp.leader
        
            # server was not live, try next server
            except grpc._channel._InactiveRpcError:
                 continue
        time.sleep(3)

def check_response(response):
    """
    Checks if the server sent a response, and raises an error if so.
    """
    if response.message == "ERR: NOT LEADER":
        raise UnavailableReplica

def main():
    listen_thread = None

    leader = find_leader()
    channel = grpc.insecure_channel(server_list[leader])
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
    check_response(response)
    print(response.message, flush = True)

    # user logged in elsewhere, end client
    if ('Already logged in' in response.message):
        return

    listen_thread = threading.Thread(target=(listen_client_messages), args=(stub, username))
    listen_thread.start()

    print("Actions: list, send <user>, delete <user>, quit", flush = True)

    # client ui loop, cannot pass stub as function argument so it all goes here
    while True:
        try:
            action = input("> ")
            
            action_list = action.split()

            if (len(action_list) == 0):
                continue
            
            elif (action_list[0] == "list"):
                response = stub.ServerChat(
                    main_pb2.UserRequest(action=action_list[0], username=username, recipient='', message="")
                )
                check_response(response)

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
                check_response(response)

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
                check_response(response)

            elif (action_list[0] == "quit"):
                response = stub.ServerChat(
                    main_pb2.UserRequest(action=action_list[0], username=username, recipient='', message="")
                )
                check_response(response)
                return

            else:
                print("Unrecognized action.", flush = True)
                continue

            print(response.message, flush = True)
    
        # the server we connected to went down during the user action
        # this assumes that the client was connected to the leader server, then that went down, and another server has been already determined
        #           to be the leader. the client will connect to that new leader.
        except (grpc._channel._InactiveRpcError, UnavailableReplica):
            # stop the listening thread
            listen_thread.join()

            # find the new leader
            leader = find_leader()
            channel = grpc.insecure_channel(server_list[leader])
            stub = main_pb2_grpc.ChatterStub(channel) 

            # restart the listening thread
            listen_thread = threading.Thread(target=(listen_client_messages), args=(stub, username))
            listen_thread.start()

            print("You were reconnected to the server. Please try again.")
            pass

        except KeyboardInterrupt:
            # send quit to server
            try:
                response = stub.ServerChat(
                    main_pb2.UserRequest(action="quit", username=username, recipient='', message="")
                )
                check_response(response)

            except grpc._channel._InactiveRpcError:
                pass
            listen_thread.join()
            break

    listen_thread.join()
    
    print("Shutting down.")
    return

if __name__ == '__main__':
    main()