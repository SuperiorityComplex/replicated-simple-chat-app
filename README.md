# replicated-simple-chat-app

## Instructions for deploying

These instructions are AWS-specific but similar requirements will apply to other cloud providers.

1. Spin up three EC2 instance.
2. Ensure that the vpc has an internet gateway attached to it so that it can be publicly accessed.
3. Ensure that the security group allows inbound traffic on port 3000 (for server) and 22 (for ssh access).
4. Download the replicated-simple-chat-app repository to the EC2 instance.
5. Install the required dependencies by running `pip install -r requirements.txt`.
6. Edit the server.py file to change the `replica_addresses` list entries to the public IPs of the EC2 instances.
7. Run the servers by running `python server.py --server_id <0/1/2>`.
8. Edit the client.py file to change the `server_list` list entries to the public IPs of the EC2 instances.
9. Run the client by running `python client.py`.

### Generating grpc stubs (Not Required)

If you want to generate the grpc stubs yourself, you can do so by running the following commands:
`./generate_grpc_stubs.sh`

### Server

`python server.py --server_id <0, 1, 2>`, in order to start the three different server instances.

### Client

`python client.py`

#### Client Usage

The UI will ask for your username. You will not be able to log into a username if that username is already logged in elsewhere.

After entering your username, pending messages will be displayed.

Into the prompt `> ` you can perform the following actions:

- `list` will list all users.
- `send <user>` will initiate a send to a recipient user. Enter the message to be sent in the following prompt `>>>`.
- `delete <user>` will delete a user. You cannot delete yourself and you cannot delete a user who is logged in elsewhere.
- `quit` will quit the client, shutting down the connection.
