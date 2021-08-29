import argparse
import logging
import sys
import time
from kazoo.client import KazooClient
from lib.daemonize.daemon import Daemon

DEFAULT_TICK = 5
DEFAULT_TIMEOUT = 200
DEFAULT_INPUT = "/dev/null"
DEFAULT_OUTPUT = "/dev/null"
DEFAULT_ERR = "/dev/null"
DEFAULT_SERVER_LIST = ""
DEFAULT_PASSWORD = ""
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
LOG_LEVEL = logging.DEBUG


class DaemonClient(Daemon):

    def __init__(self, pid_file, stdin=DEFAULT_INPUT, stdout=DEFAULT_OUTPUT, stderr=DEFAULT_ERR,
                 server_list=DEFAULT_SERVER_LIST, password=DEFAULT_PASSWORD):

        super().__init__(pid_file, std_in=stdin, std_out=stdout, std_err=stderr)

        self.password_super_user = password
        self.zookeeper_client = None
        self.zookeeper_server_list = server_list
        self.id_client = None

    def initialize_client_server(self):

        logging.info("Starting Zookeeper client")
        self.zookeeper_client = KazooClient(hosts=self.zookeeper_server_list, read_only=True)
        self.zookeeper_client.start()
        logging.info("Started Zookeeper client")

    def register_client(self):

        logging.info("Registering client")
        data, status = self.zookeeper_client.get("/number_clients")
        logging.info("Get id client")
        self.id_client = data.encode("utf-8")+1
        logging.info("Client ID: "+self.id_client)
        client_name = "/client"+str(self.id_client)
        self.zookeeper_client.create(client_name, b"True")
        self.zookeeper_client.set("/number_clients", str(self.id_client).encode("utf-8"))

    def get_zookeeper_signal_sync(self):

        logging.info("Checking signal sync")
        signal_sync, _ = self.zookeeper_client.get("/signal_sync")

        if signal_sync == b'True':

            logging.info("signal sync received")
            return True

        else:

            logging.info("signal sync not received")
            return False

    def refresh_register(self):

        logging.info("Refresh register")
        client_name = "/client" + str(self.id_client-1)
        logging.info(client_name)
        self.zookeeper_client.set(client_name, b"True")

    def background_monitor(self):

        logging.info("Starting monitor station")

        while True:

            logging.info("Checking signal sync")

            if self.get_zookeeper_signal_sync():

                logging.info("Refresh register")
                self.refresh_register()

            time.sleep(DEFAULT_TICK)

    def run(self):

        self.initialize_client_server()
        self.register_client()
        self.background_monitor()


def main():

    parser = argparse.ArgumentParser(description='Daemon Server')

    help_msg = "Refresh rate [2, 100]"
    parser.add_argument("--tick", "-t", help=help_msg, default=DEFAULT_TICK, type=int)

    help_msg = "Timeout connection"
    parser.add_argument('--timeout', help=help_msg, default=DEFAULT_TIMEOUT)

    help_msg = "List servers"
    parser.add_argument('--hosts', help=help_msg, default=DEFAULT_SERVER_LIST)

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

    pid_file = "/tmp/daemon_client%s.pid" % args.id
    stdout = "/tmp/daemon_client%s.stdout" % args.id
    stderr = "/tmp/daemon_client%s.stderr" % args.id
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
        daemon_client = DaemonClient(pid_file=pid_file, stdin="input_daemon.txt",
                                     server_list=args.hosts, password=args.password)
        daemon_client.start()

    elif sys.argv[1] == '--stop':

        logging.info("\t Stop daemon server")
        daemon_server = DaemonClient(pid_file=pid_file, stdin="input_daemon.txt", stdout=stdout,
                                     server_list=args.hosts, password=args.password)
        daemon_server.stop()

    elif sys.argv[1] == '--restart':

        logging.info("\t Restart daemon server")
        daemon_server = DaemonClient(pid_file=pid_file, stdin="input_daemon.txt", stdout=stdout,
                                     server_list=args.hosts, password=args.password)
        daemon_server.restart()

    else:

        return -1


if __name__ == '__main__':

    main()