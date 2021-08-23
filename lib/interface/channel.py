import subprocess
import time

from paramiko import SSHClient
import paramiko
from scp import SCPClient


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

    def remote_access(self, cmd, sudo=False):

        if sudo:
            _, stdout, stderr = self.connection_ssh.exec_command('su')
            _.write('kayua\n')
            _, stdout, stderr = self.connection_ssh.exec_command('chmod +x monitor/apache-zookeeper-3.6.1/bin/*')
            _, stdout, stderr = self.connection_ssh.exec_command('python3 daemon_server.py')
            _.flush()
            return 0

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






