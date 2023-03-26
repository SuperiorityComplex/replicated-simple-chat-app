import threading
import optparse
import grpc
import sys
import concurrent.futures
import time
import random
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

class ChatterServicer(main_pb2_grpc.ChatterServicer):
    def Heartbeat(self, request, context):
        return main_pb2.HeartbeatResponse(leader=leader)

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
        print("Leader is {}".format(leader))

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
    start_server()


def main():
    global server_id
    server_id = get_sys_args()
    live_servers[server_id] = True
    run_event.set()
    try:
        init_server()
    except KeyboardInterrupt:
        gracefully_shutdown()

if __name__ == '__main__':
    main()