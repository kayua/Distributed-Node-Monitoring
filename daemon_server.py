import os
import subprocess
import time
from datetime import datetime

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
        self.zookeeper_client = KazooClient(hosts='192.168.1.102:2181,192.168.1.104:2181,192.168.1.105:2181',
                                            read_only=True)
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
                self.write_database("Monitoring started at:"+time_now.decode('utf-8'))
                break

            time.sleep(2)

    def get_zookeeper_signal_sync(self):

        print("  Verificando sinal de sicronizacao")
        signal_sync, _ = self.zookeeper_client.get("/signal_sync")

        if signal_sync == b'True':

            print("    - Sinal positivo")
            return True

        else:

            print("    - Sinal negativo")
            return False

    def get_list_active_nodes(self):
        pass

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
                        self.write_database()

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
