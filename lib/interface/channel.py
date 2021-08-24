import subprocess
import time

import paramiko
from scp import SCPClient
from paramiko import SSHClient


class Channel:

    connection_ssh = None

    def __init__(self):

        self.connection_ssh = SSHClient()
        self.connection_ssh.load_system_host_keys()
        self.connection_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self, hostname, user, password):

        try:

            self.connection_ssh.connect(hostname=hostname, username=user, password=password)

            return 0

        except:

            return 1

    def remote_access(self, cmd):

        _, stdout, stderr = self.connection_ssh.exec_command(cmd)

        if stderr.channel.recv_exit_status() != 0:

            return 0

        else:

            return 1

    def send_file(self, local_path, remote_path):

        with SCPClient(self.connection_ssh.get_transport()) as scp:
            scp.put(local_path, remote_path)

    @staticmethod
    def check_file_existence(file_path):

        try:
            with open(file_path, 'r') as f:
                return False
        except FileNotFoundError as e:
            return True
        except IOError as e:
            return False

    def compress_file(self):

        try:

            if self.check_file_existence("monitor.tar.gz"):

                subprocess.run(["tar", "-cvzf", "monitor.tar.gz", "-c", "../monitor"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            return 0

        except OSError:

            return 1

    def decompress_file(self):

        command = "tar -vzxf monitor.tar.gz"
        self.remote_access(command)

    def install_monitor(self):

        self.compress_file()
        self.send_file("monitor.tar.gz", "monitor.tar.gz")
        self.decompress_file()

    def remote_start_daemon(self, id_processing, host, password):

        password_msg = password + "\n"
        _, stdout, stderr = self.connection_ssh.exec_command('sudo -S chmod +x monitor/apache-zookeeper-3.6.1/bin/*')
        time.sleep(5)
        _.write(password_msg)
        _.flush()
        _, stdout, stderr = self.connection_ssh.exec_command('sudo -S monitor/apache-zookeeper-3.6.1/bin/./zkServer.sh start')
        time.sleep(5)
        _.write(password_msg)
        _.flush()
        command = 'sudo -S python3 monitor/daemon_server.py --start true --id '+id_processing + ' --password '+password
        command = command + " --host "+host
        _, stdout, stderr = self.connection_ssh.exec_command(command)
        time.sleep(5)
        _.write(password_msg)
        _.flush()

    def remote_stop_daemon(self, id_processing, host, password):

        password_msg = password + "\n"
        _, stdout, stderr = self.connection_ssh.exec_command('sudo -S monitor/apache-zookeeper-3.6.1/bin/./zkServer.sh stop')
        time.sleep(5)
        _.write(password_msg)
        _.flush()
        command = 'sudo -S python3 monitor/daemon_server.py --stop true --id '+id_processing + ' --password '+password
        command = command + " --host "+host
        _, stdout, stderr = self.connection_ssh.exec_command(command)
        time.sleep(5)
        _.write(password_msg)
        _.flush()