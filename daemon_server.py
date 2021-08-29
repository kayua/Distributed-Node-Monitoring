import argparse
import logging
import os
import subprocess
import sys
import time
import psutil

from datetime import datetime
from kazoo.client import KazooClient
from lib.daemonize.daemon import Daemon

DEFAULT_TICK = 10
DEFAULT_TIMEOUT = 200
DEFAULT_INPUT = "/dev/null"
DEFAULT_OUTPUT = "/dev/null"
DEFAULT_ERR = "/dev/null"
DEFAULT_FILE_OUTPUT = "database.csv"
DEFAULT_ZOOKEEPER_PATH = "monitor/apache-zookeeper-3.6.1/bin/"
DEFAULT_SERVER_LIST = ""
DEFAULT_PASSWORD = ""

DEFAULT_PATH_NUM_CLIENTS = "/number_clients"
DEFAULT_PATH_NUM_SERVERS = "/number_servers"
DEFAULT_SIGNAL_SYNC = "/signal_sync"
DEFAULT_SIGNAL_HOUR = "/server_hour"
DEFAULT_CODIFICATION_FILE = "utf-8"

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
LOG_LEVEL = logging.DEBUG


class DaemonServer(Daemon):

    def __init__(self, pid_file, stdin=DEFAULT_INPUT, stdout=DEFAULT_OUTPUT, stderr=DEFAULT_ERR,
                 server_list=DEFAULT_SERVER_LIST, password=DEFAULT_PASSWORD, id_server="0"):

        super().__init__(pid_file, std_in=stdin, std_out=stdout, std_err=stderr)

        self.password_super_user = password
        self.zookeeper_client = None
        self.zookeeper_server_list = server_list
        self.file_results = None
        self.server_id = id_server

    @staticmethod
    def zookeeper_is_running():

        logging.info("Checking if Zookeeper is running")
        process_status = [proc for proc in psutil.process_iter() if proc.name() == 'zkServer.sh']

        if process_status:

            logging.info("Zookeeper running")
            return True

        else:

            logging.info("Zookeeper not running")
            return True

    def initialize_client_server(self):

        logging.info("Starting Zookeeper client")
        self.start_zookeeper()
        self.zookeeper_client = KazooClient(hosts=self.zookeeper_server_list, read_only=True)
        self.zookeeper_client.start()
        logging.info("Started Zookeeper client")

    def start_zookeeper(self):

        logging.info('Starting Zookeeper Server')
        command_permission = 'chmod +x'
        command_start = 'start'
        command = "{} {}*".format(command_permission, DEFAULT_ZOOKEEPER_PATH)
        os.system('echo %s|sudo -S %s' % (self.password_super_user, command))
        command = '{}./zkServer.sh {}'.format(DEFAULT_ZOOKEEPER_PATH, command_start)
        subprocess.call(command, shell=True)
        logging.info("Started Zookeeper Server")

    @staticmethod
    def zookeeper_token_leader():

        logging.info("Checking token leader")
        command_state = "status"
        command = '{}./zkServer.sh {}'.format(DEFAULT_ZOOKEEPER_PATH, command_state)
        status = os.popen(command).read()

        try:

            if status.index('leader'):

                logging.info("Leader token detected")
                return True

            else:

                logging.info("Leader token not detected")
                return False

        except:

            logging.info("Leader token not detected")
            return False

    @staticmethod
    def stop_zookeeper():

        logging.info("Stopping Zookeeper Server")
        command_stop = 'stop'
        command = '{}./zkServer.sh {}'.format(DEFAULT_ZOOKEEPER_PATH, command_stop)
        subprocess.call(command, shell=True)
        logging.info("Stopped Zookeeper Server")

    def wait_setting_system(self):

        while True:

            logging.info("waiting command for start")

            if self.zookeeper_client.exists(DEFAULT_SIGNAL_HOUR):

                logging.info("waiting command for start")
                time_now, _ = self.zookeeper_client.get(DEFAULT_SIGNAL_HOUR)
                break

            time.sleep(1)

        self.create_database_file(time_now.decode(DEFAULT_CODIFICATION_FILE))

    def get_zookeeper_signal_sync(self):

        logging.info("Checking signal sync")
        signal_sync, _ = self.zookeeper_client.get(DEFAULT_SIGNAL_SYNC)

        if signal_sync == b'True':

            logging.info("signal sync received")
            return True

        else:

            logging.info("signal sync not received")
            return False

    def set_zookeeper_signal_sync(self):

        logging.info("Send signal sync")
        self.zookeeper_client.set(DEFAULT_SIGNAL_SYNC, b"True")
        self.zookeeper_client.set(DEFAULT_SIGNAL_HOUR, self.get_date_hour().encode(DEFAULT_CODIFICATION_FILE))
        time.sleep(int(DEFAULT_TICK / 2))
        self.zookeeper_client.set(DEFAULT_SIGNAL_SYNC, b"False")

    def refresh_state_server(self):

        logging.info("Refresh state local server")
        server_name = "/server{}".format(str(self.server_id))
        logging.info(server_name)
        self.zookeeper_client.set(server_name, b"True")
        logging.info("Refresh state local server")

    @staticmethod
    def get_date_hour():

        return str(datetime.today())

    def create_database_file(self, datetime_now):

        logging.info("Creating data file")

        self.file_results = open(DEFAULT_FILE_OUTPUT, '+a')
        self.file_results.write('Start monitor: Hour: {}'.format(datetime_now))
        self.file_results.close()

    def write_database(self, datetime_now, list_servers, list_clients):

        logging.info("Write database of monitoring")
        self.file_results = open(DEFAULT_FILE_OUTPUT, '+a')
        self.file_results.write('Snapshot Monitor: Hour: {}\n'.format(datetime_now))
        self.file_results.write('  Servers: \n')

        for i in list_servers:

            self.file_results.write('    - {}\n'.format(str(i)))

        self.file_results.write('  Clients: \n')

        for i in list_clients:

            self.file_results.write('    - {}\n'.format(str(i)))

        self.file_results.write('\n')
        self.file_results.close()
        pass

    def get_state_monitor(self):

        list_registered_servers = []
        list_registered_clients = []

        logging.info("\n\n Show meta data")

        signal_sync, _ = self.zookeeper_client.get(DEFAULT_SIGNAL_SYNC)
        signal = str(signal_sync.decode(DEFAULT_CODIFICATION_FILE))
        logging.info("Received signal: {}".format(signal))

        signal_hour, _ = self.zookeeper_client.get(DEFAULT_SIGNAL_HOUR)
        datetime_now = str(signal_hour.decode(DEFAULT_CODIFICATION_FILE))
        logging.info("Hour: {}".format(datetime_now))

        num_server, _ = self.zookeeper_client.get(DEFAULT_PATH_NUM_SERVERS)
        number_servers = str(num_server.decode(DEFAULT_CODIFICATION_FILE))
        logging.info("NumberServers: {}".format(number_servers))
        client_id, _ = self.zookeeper_client.get(DEFAULT_PATH_NUM_CLIENTS)
        number_clients = str(client_id.decode(DEFAULT_CODIFICATION_FILE))
        logging.info("NumberClients: " + number_clients)
        logging.info("\nServerList:")

        for i in range(int(number_servers)):

            server_name = "/server" + str(i+1)
            server_id, _ = self.zookeeper_client.get(server_name)
            logging.info(server_name+": " + str(server_id.decode(DEFAULT_CODIFICATION_FILE)))
            list_registered_servers.append(str(server_id.decode(DEFAULT_CODIFICATION_FILE)))

        logging.info("\nClientList:")

        for i in range(int(number_clients)):

            client_name = "/client" + str(i+1)
            client_id, _ = self.zookeeper_client.get(client_name)
            logging.info(client_name + ": ", str(client_id.decode(DEFAULT_CODIFICATION_FILE)))
            list_registered_clients.append(str(client_id.decode(DEFAULT_CODIFICATION_FILE)))

        return datetime_now, list_registered_servers, list_registered_clients

    def background_leader(self):

        logging.info("State change to leader state")

        while True:

            if self.zookeeper_is_running():

                if self.zookeeper_token_leader():

                    self.clear_state_monitor()
                    self.set_zookeeper_signal_sync()
                    self.refresh_state_server()
                    time.sleep(5)
                    datetime_now, list_registered_servers, list_registered_clients = self.get_state_monitor()
                    self.write_database(datetime_now, list_registered_servers, list_registered_clients)

                else:

                    break

            else:

                self.start_zookeeper()

            time.sleep(DEFAULT_TICK)

    def clear_state_monitor(self):

        logging.info("Clean state buffer")

        num_server, _ = self.zookeeper_client.get(DEFAULT_PATH_NUM_SERVERS)
        number_servers = str(num_server.decode(DEFAULT_CODIFICATION_FILE))
        num_clients, _ = self.zookeeper_client.get(DEFAULT_PATH_NUM_CLIENTS)
        number_clients = str(num_clients.decode(DEFAULT_CODIFICATION_FILE))

        for i in range(int(number_servers)):

            server_name = "/server" + str(i+1)
            self.zookeeper_client.set(server_name, b"False")

        for i in range(int(number_clients)):

            client_name = "/client" + str(i+1)
            self.zookeeper_client.set(client_name, b"False")

    def background_follower(self):

        self.wait_setting_system()
        logging.info("State change to follower state")

        while True:

            if self.zookeeper_is_running():

                if self.zookeeper_token_leader():

                    self.get_state_monitor()

                    logging.info("State change to leader state")
                    self.background_leader()

                else:

                    if self.get_zookeeper_signal_sync():

                        self.refresh_state_server()

                        datetime_now, list_registered_servers, list_registered_clients = self.get_state_monitor()
                        self.write_database(datetime_now, list_registered_servers, list_registered_clients)

            else:

                self.start_zookeeper()

            time.sleep(DEFAULT_TICK)

    def run(self):

        self.initialize_client_server()
        self.wait_setting_system()
        self.background_follower()


def main():

    parser = argparse.ArgumentParser(description='Daemon Server')

    help_msg = "Process identification"
    parser.add_argument("--id", "-i", help=help_msg, default="default", type=str)

    help_msg = "Refresh rate [2, 100]"
    parser.add_argument("--tick", "-t", help=help_msg, default=DEFAULT_TICK, type=int)

    help_msg = "Timeout connection"
    parser.add_argument('--timeout', help=help_msg, default=DEFAULT_TIMEOUT)

    help_msg = "List servers"
    parser.add_argument('--hosts', help=help_msg, default=DEFAULT_SERVER_LIST)

    help_msg = "SuperUser Password"
    parser.add_argument('--password', help=help_msg, default=DEFAULT_PASSWORD)

    help_msg = "Start server in background"
    parser.add_argument('--start', help=help_msg, required=False)

    help_msg = "Stop server in background"
    parser.add_argument('--stop', help=help_msg, required=False)

    help_msg = "Restart server"
    parser.add_argument('--restart', help=help_msg, required=False)

    parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

    args = parser.parse_args()

    if args.log == logging.DEBUG:

        logging.basicConfig(filename="logfile.log", filemode='+a',
                            format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                            datefmt=TIME_FORMAT, level=args.log)

    else:

        logging.basicConfig(filename="logfile.log", filemode='+a',
                            format='%(asctime)s %(message)s',
                            datefmt=TIME_FORMAT, level=args.log)

    logging.info("")
    logging.info("INPUT")
    logging.info("---------------------")
    logging.info("\t logging level : %s" % args.log)
    logging.info("\t unique id     : %s" % args.id)
    logging.info("\t sleep secs    : %s" % args.tick)
    logging.info("")

    pid_file = "/tmp/daemon_server%s.pid" % args.id
    stdout = "/tmp/daemon_server%s.stdout" % args.id
    stderr = "/tmp/daemon_daemon_%s.stderr" % args.id
    stdin = open('input_daemon.txt', 'w')
    stdin.close()

    logging.info("FILES")
    logging.info("---------------------")
    logging.info("\t pid_file      : %s" % pid_file)
    logging.info("\t stdout        : %s" % stdout)
    logging.info("\t stderr        : %s" % stderr)
    logging.info("\t stdin       : %s" % "input_daemon.txt")
    logging.info("")

    if sys.argv[1] == '--start':

        logging.info("\t Starting daemon server")
        daemon_server = DaemonServer(pid_file=pid_file, stdin="input_daemon.txt",
                                     server_list=args.hosts, password=args.password, id_server=str(args.id))
        daemon_server.start()

    elif sys.argv[1] == '--stop':

        logging.info("\t Stop daemon server")
        daemon_server = DaemonServer(pid_file=pid_file, stdin="input_daemon.txt", stdout=stdout,
                                     server_list=args.hosts, password=args.password, id_server=str(args.id))
        daemon_server.stop()

    elif sys.argv[1] == '--restart':

        logging.info("\t Restart daemon server")
        daemon_server = DaemonServer(pid_file=pid_file, stdin="input_daemon.txt", stdout=stdout,
                                     server_list=args.hosts, password=args.password, id_server=str(args.id))
        daemon_server.restart()

    else:

        return -1


if __name__ == '__main__':
    main()
