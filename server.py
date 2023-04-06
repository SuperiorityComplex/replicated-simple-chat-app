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

# Stores all the threads that are running. (Used for graceful shutdown)
running_threads = []

# Event that is set when threads are running and cleared when you want threads to stop
run_event = threading.Event()

# The current server
server = None

# Map from index to replicas host
replicas = ["127.0.0.1:3000", "127.0.0.1:3001", "127.0.0.1:3002"]

# The server id of the current leader
leader = None

# Live servers. None if initial check server alive call has not been made. True if alive and False if dead.
live_servers = [None, None, None]

# Database of pending messages
database = {"ivan": []}
# dict of active users
active_users = []

class ChatterServicer(main_pb2_grpc.ChatterServicer):
    def Heartbeat(self, request, context):
        return main_pb2.HeartbeatResponse(leader=leader)
    
    def UpdateDatabase(self, request, context):
        global database
        database = json.loads(request.database)
        return main_pb2.UpdateResponse()
    
    def ServerChat(self, request, context): 
        return handle_server_response(request.action, request.username, request.recipient, request.message)
    
    def ClientChat(self, username, context):
        username = username.username
        
        if username not in active_users:
            active_users.append(username)

        while username in active_users:
            if username in database and len(database[username]) != 0:
                msg = "\n".join(database[username])
                database[username] = []
                yield main_pb2.Message(message = msg)

    def LeaderCheck(self, request, context):
        return main_pb2.LeaderResponse(leader = leader)



def gracefully_shutdown():
    """
    Gracefully shuts down the server.
    @Parameter: None.
    @Returns: None.
    """
    print("Shutting down.") # UI message
    run_event.clear()
    server.stop(0)
    try:
        for thread in running_threads:
            thread.join()
    except (OSError):
        # This occurs when the socket is already closed.
        pass
    print("threads successfully closed.")
    sys.exit(0)


def get_sys_args():
    """
    Gets the arguments from the flags
    @Parameter: None.
    @Returns: 
    - server_id: id for the server (0, 1, 2).
    """
    p = optparse.OptionParser()
    # normal execution flags
    p.add_option('--server_id', '-s', default="0")

    options, _ = p.parse_args()
    server_id = int(options.server_id)

    return server_id

def start_server():
    """
    Starts a server
    @Parameter:
    - server_id: The id of the server (0, 1, 2).
    @Returns: None.
    """
    global server
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    main_pb2_grpc.add_ChatterServicer_to_server(ChatterServicer(), server)
    server.add_insecure_port(replicas[server_id])
    print("Started server on", replicas[server_id])
    server.start()
    server.wait_for_termination()

def valdiate_leader():
    """
    Checks if the leader is alive
    @Parameter: None.
    @Returns: None.
    """
    global leader
    if leader is None:
        for index, isAlive in enumerate(live_servers):
            if isAlive:
                leader = index
                return
        print("No servers found.")
        gracefully_shutdown()
    else:
        if not live_servers[leader]:
            for index, isAlive in enumerate(live_servers):
                if isAlive:
                    leader = index
                    return
            print("No servers found.")
            gracefully_shutdown()


def send_database():
    """
    Sends the database to other servers
    @Parameter: None.
    @Returns: None.
    """
    global server_id
    if(leader != server_id):
        return
    for index, isAlive in enumerate(live_servers):
        if isAlive and index != leader and index != server_id:
            channel = grpc.insecure_channel(replicas[index])
            stub = main_pb2_grpc.ChatterStub(channel)
            try:
                stub.UpdateDatabase(main_pb2.UpdateRequest(database=json.dumps(database)))
            except:
                print("Server {} is down".format(index))
                live_servers[index] = False

def send_heartbeat(stub, ext_server_id):
    """
    Sends a heartbeat to the server
    @Parameter:
    - stub: The stub to the server.
    - ext_server_id: The id of the server (0, 1, 2).
    @Returns: None.
    """
    
    try: 
        response = stub.Heartbeat(main_pb2.HeartbeatRequest())
        live_servers[ext_server_id] = True
        global leader
        leader = response.leader
    except:
        print("Server {} is down".format(ext_server_id))
        live_servers[ext_server_id] = False


def start_heartbeat(ext_server_id):
    """
    Starts the heartbeat connection
    @Parameter:
    - ext_server_id: The id of the server (0, 1, 2).
    @Returns: None.
    """
    channel = grpc.insecure_channel(replicas[ext_server_id])
    stub = main_pb2_grpc.ChatterStub(channel)
    send_heartbeat(stub, ext_server_id)
    while None in live_servers:
        continue
    heartbeat_interval = random.randint(1, 5)
    while run_event.is_set():
        time.sleep(heartbeat_interval)
        send_heartbeat(stub, ext_server_id)
        valdiate_leader()

# def test_database_sync():
#     count = 0
#     global server_id
#     while run_event.is_set():
#         if(leader is None):
#             continue
#         if(leader != server_id):
#             continue
#         time.sleep(2)
#         database["ivan"].append("HI{}".format(count))
#         print(database)
#         send_database()
#         count += 1


def handle_server_response(action, username, recipient, message):
    print("Received action:", action)

    if(action == "list"):
        msg = ", ".join(list(database.keys()))
        return main_pb2.Message(message = msg)
    
    elif(action == "delete"):
        if(username in active_users):
            return main_pb2.Message(message = "Cannot delete logged in user.")

        if(username in list(database.keys())):
            del database[username]
            return main_pb2.Message(message = "User deleted successfully.")

        else:
            return main_pb2.Message(message = "User does not exist.")
    
    elif(action == "send"):
        chat = f"{username} says: {message}"
        if(recipient not in database.keys()):
            response =  "The recipient does not exist."
        else:
            # TODO: here should send the databases out to replicas? or maybe should do it on heartbeats?
            database[recipient].append(chat)
            response = "Message sent successfully."
        return main_pb2.Message(message = response)
    
    elif(action == "join"):
        if (username in active_users): # already logged in, refuse client
            return main_pb2.Message(message = "Already logged in elsewhere.")

        active_users.append(username)

        if(username not in database.keys()):
            response = "User created. Welcome!"
            database[username] = []
        else:
            response = "Welcome back!"

        return main_pb2.Message(message = response)
    
    elif(action == "quit"):
        active_users.remove(username)
        return main_pb2.Message(message = "")

def init_server():
    """
    Initializes a server
    @Parameter:
    - server_id: The id of the server (0, 1, 2).
    @Returns: None.
    """
    for i in range(3):
        if (i != server_id):
            heartbeat_thread = threading.Thread(
                target=start_heartbeat, args=(i,)
            )
            heartbeat_thread.start()
            running_threads.append(heartbeat_thread)
    # test_thread = threading.Thread(
    #     target=test_database_sync, args=()
    # )
    # test_thread.start()
    # running_threads.append(test_thread)
    start_server()


def main():
    global server_id
    server_id = get_sys_args()
    
    if server_id not in [0, 1, 2]:
        print("server_id must be 0, 1, 2")
        return
    
    live_servers[server_id] = True
    run_event.set()
    try:
        init_server()
    except KeyboardInterrupt:
        gracefully_shutdown()

if __name__ == '__main__':
    main()