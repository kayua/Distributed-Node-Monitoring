from lib.clients.client_communication import ClientCommunication


DEFAULT_LOG_FILE = "log.out"


class Client:

    id_client = None
    communication = None
    log_file = None

    def __init__(self, list_servers):

        self.communication = ClientCommunication(list_servers)

        if self.communication.connect():

            self.communication.register_node()
            self.id_client = self.communication.get_client_id()

        else:

            self.id_client = -1

    def create_log_file(self):

        self.log_file = open(DEFAULT_LOG_FILE, "w")

    def write_results_monitoring(self, list_results, time_sync):

        self.log_file.write(str(time_sync) + ": " + " | ".join(list_results))

    def monitoring(self):

        while True:

            if self.communication.get_state_connection() and self.communication.sync_signal():

                status_nodes = self.communication.ge

