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

        print("  Verificando se o Zookeeper está rodando:")
        process_status = [proc for proc in psutil.process_iter() if proc.name() == 'zkServer.sh']

        if process_status:

            print("    - Zookeper está rodando")
            return True

        else:

            print("    - Zookeper não está rodando:")
            return True

    def initialize_client_server(self):

        print("  Inicializando client Zookeeper")
        self.start_zookeeper()
        self.zookeeper_client = KazooClient(hosts=self.zookeeper_server_list, read_only=True)
        self.zookeeper_client.start()
        print("    - Cliente Zookeeper iniciado")

    def start_zookeeper(self):

        print("  Inicializando Servidor Zookeeper")
        command = 'chmod +x apache-zookeeper-3.6.1/bin/./*'
        os.system('echo %s|sudo -S %s' % (self.password_super_user, command))
        cmd = "apache-zookeeper-3.6.1/bin/./zkServer.sh start"
        subprocess.call(cmd, shell=True)
        print("    - Servidor Inicializado")

    @staticmethod
    def zookeeper_token_leader():

        print("  Verificando condicao de liderança")
        cmd = 'apache-zookeeper-3.6.1/bin/./zkServer.sh status'
        status = os.popen(cmd).read()

        try:

            if status.index('leader'):

                print("    - Condicao de lideranca detectada")
                return True

            else:

                print("    - Condicao de lideranca não detectada")
                return False
        except:
            print("    - Condicao de lideranca não detectada")
            return False

    def stop_zookeeper(self):

        print("  Parando servidor Zookeeper")
        command = 'apache-zookeeper-3.6.1/bin/./zkServer.sh stop'
        os.system('echo %s|sudo -S %s' % (self.password_super_user, command))
        print("    - Servidor Zookeeper parado")

    def wait_setting_system(self):

        while True:

            print("Aguardando ordem de inicio")

            if self.zookeeper_client.exists("/server_hour"):

                time_now, _ = self.zookeeper_client.get("/server_hour")
                self.write_database("Monitoring started at:" + time_now.decode('utf-8'))
                break

    def get_zookeeper_signal_sync(self):

        print("  Verificando sinal de sicronizacao")
        signal_sync, _ = self.zookeeper_client.get("/signal_sync")

        if signal_sync == b'True':

            print("    - Sinal positivo")
            return True

        else:

            print("    - Sinal negativo")
            return False

    def set_zookeeper_signal_sync(self):

        print("  Ativando sinal de sincronizacao")
        self.zookeeper_client.set("/signal_sync", b"True")
        self.zookeeper_client.set("/server_hour", self.get_date_hour().encode('utf-8'))
        time.sleep(int(DEFAULT_TICK / 2))
        self.zookeeper_client.set("/signal_sync", b"False")

    @staticmethod
    def get_date_hour():

        return str(datetime.today())

    @staticmethod
    def write_database(text):

        print("  Gravando dados no banco")
        a = open("tex.txt", "+a")
        a.write("test\n")
        a.close()
        pass

    def background_leader(self):

        print("        MODO LIDER ATIVADO")

        while True:

            if self.zookeeper_is_running():

                if self.zookeeper_token_leader():

                    if self.set_zookeeper_signal_sync():
                        self.write_database("Test")

                else:

                    break

            else:

                self.start_zookeeper()

            time.sleep(DEFAULT_TICK)

    def background_follower(self):

        print("        MODO SEGUIDOR ATIVADO")
        self.wait_setting_system()

        while True:

            if self.zookeeper_is_running():

                print("Iniciado e verificando")

                if self.zookeeper_token_leader():

                    self.background_leader()

                else:

                    print("Não sou lider")

                    if self.get_zookeeper_signal_sync():
                        print("Estado de sincronização")
                        self.write_database("test")

                    print("Não sincronização")
            else:

                self.start_zookeeper()

            print("aguardando relógio")
            time.sleep(DEFAULT_TICK)
            print("aguardando relógio")

    def run(self):

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

    parser.add_argument('--start', required=False)

    parser.add_argument('--stop', required=False)

    parser.add_argument('--restart', required=False)

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

        print("Iniciando daemon")
        daemon_server = DaemonServer(pid_file=pid_file, stdin="input_daemon.txt", stdout=stdout,
                                     server_list=args.hosts, password=args.password)

        daemon_server.start()

    elif sys.argv[1] == '--stop':

        daemon_server = DaemonServer(pid_file=pid_file, stdin="input_daemon.txt", stdout=stdout,
                                     server_list=args.hosts, password=args.password)

        daemon_server.stop()

    elif sys.argv[1] == '--restart':

        daemon_server = DaemonServer(pid_file=pid_file, stdin="input_daemon.txt", stdout=stdout,
                                     server_list=args.hosts, password=args.password)

        daemon_server.restart()

    else:
        return -1


if __name__ == '__main__':
    main()
