import time

from lib.clients.client_communication import ClientCommunication


DEFAULT_TIME = 1000


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

    def client_processing(self):

        while True:

            if not self.communication.get_state_connection():

                self.communication.connect()

            if self.communication.get_state_connection():

                if self.communication.get_sync_signal():

                    self.communication.refresh_session()

            time.sleep(DEFAULT_TIME)


