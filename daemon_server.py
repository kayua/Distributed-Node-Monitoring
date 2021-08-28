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
DEFAULT_SERVER_LIST = ""
DEFAULT_PASSWORD = ""
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
LOG_LEVEL = logging.DEBUG


class DaemonServer(Daemon):

    def __init__(self, pid_file, stdin=DEFAULT_INPUT, stdout=DEFAULT_OUTPUT, stderr=DEFAULT_ERR,
                 server_list=DEFAULT_SERVER_LIST, password=DEFAULT_PASSWORD):

        super().__init__(pid_file, std_in=stdin, std_out=stdout, std_err=stderr)

        self.password_super_user = password
        self.zookeeper_client = None
        self.zookeeper_server_list = server_list

    @staticmethod
    def zookeeper_is_running():

        logging.info("Cheking if Zookeeper is running")
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

        logging.info("Starting Zookeeper Server")
        command = 'chmod +x apache-zookeeper-3.6.1/bin/./*'
        os.system('echo %s|sudo -S %s' % (self.password_super_user, command))
        cmd = "apache-zookeeper-3.6.1/bin/./zkServer.sh start"
        subprocess.call(cmd, shell=True)
        logging.info("Started Zookeeper Server")

    @staticmethod
    def zookeeper_token_leader():

        logging.info("Checking token leader")
        cmd = 'apache-zookeeper-3.6.1/bin/./zkServer.sh status'
        status = os.popen(cmd).read()

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

    def stop_zookeeper(self):

        logging.info("Stopping Zookeeper Server")
        command = 'apache-zookeeper-3.6.1/bin/./zkServer.sh stop'
        os.system('echo %s|sudo -S %s' % (self.password_super_user, command))
        logging.info("Stopped Zookeeper Server")

    def wait_setting_system(self):

        while True:

            logging.info("waiting command for start")

            if self.zookeeper_client.exists("/server_hour"):
                logging.info("waiting command for start")
                time_now, _ = self.zookeeper_client.get("/server_hour")
                self.write_database("Monitoring started at:" + time_now.decode('utf-8'))
                break

            time.sleep(1)

    def get_zookeeper_signal_sync(self):

        logging.info("Checking signal sync")
        signal_sync, _ = self.zookeeper_client.get("/signal_sync")

        if signal_sync == b'True':

            logging.info("signal sync received")
            return True

        else:

            logging.info("signal sync not received")
            return False

    def set_zookeeper_signal_sync(self):

        logging.info("Send signal sync")
        self.zookeeper_client.set("/signal_sync", b"True")
        self.zookeeper_client.set("/server_hour", self.get_date_hour().encode('utf-8'))
        time.sleep(int(DEFAULT_TICK / 2))
        self.zookeeper_client.set("/signal_sync", b"False")

    @staticmethod
    def get_date_hour():

        return str(datetime.today())

    @staticmethod
    def write_database(text):

        logging.info("Write database of monitoring")
        a = open("tex.txt", "+a")
        a.write(text)
        a.close()
        pass

    def background_leader(self):

        logging.info("State change to leader state")

        while True:

            if self.zookeeper_is_running():

                if self.zookeeper_token_leader():

                    self.show_data_server()

                    if self.set_zookeeper_signal_sync():
                        self.write_database("Test")

                else:

                    break

            else:

                self.start_zookeeper()

            time.sleep(DEFAULT_TICK)

    def show_data_server(self):

        logging.info("\n\n Show meta data")

        signal_sync, _ = self.zookeeper_client.get("/signal_sync")
        signal = str(signal_sync.decode('utf-8'))
        logging.info("Received signal: " + signal)

        signal_hour, _ = self.zookeeper_client.get("/server_hour")
        hour = str(signal_hour.decode('utf-8'))
        logging.info("Hour: " + hour)

        num_server, _ = self.zookeeper_client.get("/number_servers")
        number_servers = str(num_server.decode('utf-8'))
        logging.info("NumberServers:" + number_servers)

        num_clients, _ = self.zookeeper_client.get("/number_servers")
        number_clients = str(num_clients.decode('utf-8'))
        logging.info("NumberClients: " + number_clients)
        logging.info("\nServerList:")

        for i in range(int(number_servers)):

            server_name = "/server" + str(i)
            num_clients, _ = self.zookeeper_client.get(server_name)
            logging.info(server_name+": " + str(num_clients.decode('utf-8')))

        logging.info("\nClientList:")

        for i in range(int(number_clients)):

            client_name = "/client" + str(i)
            num_clients, _ = self.zookeeper_client.get(client_name)
            logging.info(client_name + ": ", str(num_clients.decode('utf-8')))

    def background_follower(self):

        self.wait_setting_system()
        logging.info("State change to follower state")

        while True:

            if self.zookeeper_is_running():

                if self.zookeeper_token_leader():

                    self.show_data_server()

                    logging.info("State change to leader state")
                    self.background_leader()

                else:

                    if self.get_zookeeper_signal_sync():
                        self.write_database("test")

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
                                     server_list=args.hosts, password=args.password)
        daemon_server.start()

    elif sys.argv[1] == '--stop':

        logging.info("\t Stop daemon server")
        daemon_server = DaemonServer(pid_file=pid_file, stdin="input_daemon.txt", stdout=stdout,
                                     server_list=args.hosts, password=args.password)
        daemon_server.stop()

    elif sys.argv[1] == '--restart':

        logging.info("\t Restart daemon server")
        daemon_server = DaemonServer(pid_file=pid_file, stdin="input_daemon.txt", stdout=stdout,
                                     server_list=args.hosts, password=args.password)
        daemon_server.restart()

    else:

        return -1


if __name__ == '__main__':
    main()
