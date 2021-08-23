import os
import subprocess
import time

import psutil
from kazoo.client import KazooClient

DEFAULT_TICK = 5
DEFAULT_TIMEOUT = 200


class Server:

    def __init__(self, server_list, password):

        self.password_super_user = password
        self.zookeeper_client = None
        self.zookeeper_server_list = server_list
        pass

    @staticmethod
    def zookeeper_is_running():

        print("Verificando se o Zookeeper está rodando:")
        process_status = [proc for proc in psutil.process_iter() if proc.name() == 'zkServer.sh']

        if process_status:

            print("   - Zookeper está rodando")
            return True

        else:
            
            print("   - Zookeper não está rodando:")
            return True

    def initialize_client_server(self):

        self.start_zookeeper()
        self.zookeeper_client = KazooClient(hosts='192.168.1.102:2181,192.168.1.104:2181,192.168.1.105:2181', read_only=True)
        self.zookeeper_client.start()

    def start_zookeeper(self):

        command = 'chmod +x apache-zookeeper-3.6.1/bin/./*'
        os.system('echo %s|sudo -S %s' % (self.password_super_user, command))
        cmd = "apache-zookeeper-3.6.1/bin/./zkServer.sh start"
        subprocess.call(cmd, shell=True)
        print("Zookeeper Ativado")

    @staticmethod
    def zookeeper_token_leader():

        cmd = 'apache-zookeeper-3.6.1/bin/./zkServer.sh status'
        status = os.popen(cmd).read()
        print("Eu sou o Lider?     kkkkk")
        try:

            if status.index('leader'):
                print("Sou líder")
                return True

            else:
                print("Sou seguidor")
                return False

        except:

            return False

    def stop_zookeeper(self):

        command = 'apache-zookeeper-3.6.1/bin/./zkServer.sh stop'
        os.system('echo %s|sudo -S %s' % (self.password_super_user, command))

    def get_zookeeper_signal_sync(self):

        data, stat = self.zookeeper_client.get("/signal_sync")
        print("sincronizando")

        if data == b'True':

            print("Sinal positivo")
            return True

        else:

            print("Sinal negativo")
            return False

    def set_zookeeper_signal_sync(self):

        self.zookeeper_client.set("/signal_sync", b"True")
        time.sleep(int(DEFAULT_TICK / 2))
        self.zookeeper_client.set("/signal_sync", b"False")

    def write_database(self):
        a = open("tex.txt", "+a")
        a.write("test\n")
        a.close()
        pass

    def background_leader(self):

        while True:

            if self.zookeeper_is_running():

                if self.zookeeper_token_leader():

                    if self.set_zookeeper_signal_sync():
                        self.write_database()

                else:

                    break

            else:

                self.start_zookeeper()

            time.sleep(DEFAULT_TICK)

    def background_follower(self):

        while True:

            if self.zookeeper_is_running():

                print("Iniciado e verificando")

                if self.zookeeper_token_leader():

                    self.background_leader()

                else:

                    print("Não sou lider")

                    if self.get_zookeeper_signal_sync():

                        print("Estado de sincronização")
                        self.write_database()

                    print("Não sincronização")
            else:

                self.start_zookeeper()

            print("aguardando relógio")
            time.sleep(DEFAULT_TICK)
            print("aguardando relógio")


daemon = Server("192.168.1.102:2181", "kayua")
daemon.initialize_client_server()
daemon.background_follower()

zk = KazooClient(hosts='192.168.1.102:2181,192.168.1.104:2181,192.168.1.105:2181', read_only=True)
zk.start()
data, stat = zk.get("/signal_sync")