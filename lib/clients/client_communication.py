from kazoo.client import KazooClient

DEFAULT_TIMEOUT = 1000
DEFAULT_TIME_SYNC_SIGNAL = 100
DEFAULT_MAX_CLIENTS = 10


class ClientCommunication:

    zookeeper_server_list = None
    zookeeper_client = None
    client_id = None

    def __init__(self, server_list):

        self.zookeeper_server_list = server_list

    def connect(self):

        self.zookeeper_client = KazooClient(hosts=self.zookeeper_server_list, timeout=DEFAULT_TIMEOUT)

        try:

            self.zookeeper_client.start()

            if self.zookeeper_client.state() != "CONNECTED":

                return 0

            else:

                return 1

        except ChildProcessError:

            return 0

    def register_node(self):

        if self.zookeeper_client.state() != "CONNECTED":

            print("Error: Error contacting server")
            return 0

        else:

            for i in range(0, DEFAULT_MAX_CLIENTS):

                if not self.zookeeper_client.exists("/node" + str(i)):
                    self.zookeeper_client.create("/node" + str(i), b"Registered")
                    self.client_id = i

    def get_client_id(self):

        return self.client_id

    def get_state_connection(self):

        if self.zookeeper_client.state() != "CONNECTED":

            return False

        else:

            return True

    def get_state_connection_servers(self):

        if self.zookeeper_client.state() != "CONNECTED":

            return 0

        else:

            return 1

    def refresh_session(self):

        if self.get_state_connection_servers():

            self.zookeeper_client.set("/node" + str(self.client_id), b"Connected")

    def get_sync_signal(self):

        signal_sync, state = self.zookeeper_client.get("/sync_clients")

        if signal_sync == b"True":

            return True

        else:

            return False

