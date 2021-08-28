import subprocess
import time

import paramiko
from scp import SCPClient
from paramiko import SSHClient

DEFAULT_DELAY_COMMAND_SEND = 1
DEFAULT_PATH_ZOOKEEPER_SERVER = "monitor/apache-zookeeper-3.6.1/bin/*"
DEFAULT_ZOOKEEPER_SERVER = "monitor/apache-zookeeper-3.6.1/bin/./zkServer.sh"


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

    def remote_start_zookeeper(self, id_processing, host, password):

        password_super_user = password + "\n"
        set_permission = "sudo -S "
        command_exec_permission = "chmod -R +x "
        command = set_permission+command_exec_permission+"monitor/apache-zookeeper-3.6.1/* "
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)

        time.sleep(DEFAULT_DELAY_COMMAND_SEND+1)
        channel_stdin.write(password_super_user)
        channel_stdin.flush()
        command = " echo "+str(id_processing)+" >> monitor/server_id/myid"
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)

        print(channel_stdout.read())
        print(channel_stderr.read())
        print(command)

        command_start = " start "
        command = set_permission+DEFAULT_ZOOKEEPER_SERVER + command_start
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND+1)
        channel_stdin.write(password_super_user)
        channel_stdin.flush()

        print(command)
        print(channel_stdout.read())
        print(channel_stderr.read())

    def remote_start_monitors(self, id_processing, host, password):

        set_permission = "sudo -S "
        password_super_user = password + "\n"
        command_daemon_server = "python3 monitor/daemon_server.py "
        command_start_server = "--stop true "
        command = set_permission + command_daemon_server+command_start_server + "--id " + id_processing + ' --password '+ password
        command = command + " --host "+host
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_super_user)
        channel_stdin.flush()
        print(command)
        print(channel_stdout.read())
        print(channel_stderr.read())

        command_start_server = "--start true "
        command = set_permission + command_daemon_server+command_start_server + "--id " + id_processing + ' --password '+ password
        command = command + " --host "+host
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_super_user)
        channel_stdin.flush()

        print(command)
        print(channel_stdout.read())
        print(channel_stderr.read())

    def remote_stop_daemon(self, id_processing, host, password):

        password_msg = password + "\n"
        set_permission = "sudo -S "
        command_stop = " stop "
        command_daemon_server = "python3 monitor/daemon_server.py "
        command = set_permission + DEFAULT_ZOOKEEPER_SERVER + command_stop
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()
        command = set_permission + command_daemon_server + '--stop true --id '+id_processing + ' --password '+password
        command = command + " --host "+host
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()
