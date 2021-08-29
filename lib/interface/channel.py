import subprocess
import time
import paramiko
from scp import SCPClient
from paramiko import SSHClient

DEFAULT_DELAY_COMMAND_SEND = 1
DEFAULT_TAR_FILE = "monitor.tar.gz"
DEFAULT_PATH_ZOOKEEPER_SERVER = "monitor/apache-zookeeper-3.6.1/bin/*"
DEFAULT_ZOOKEEPER_SERVER = "monitor/apache-zookeeper-3.6.1/bin/./zkServer.sh"
DEFAULT_ZOOKEEPER_ID = "monitor/server_id/myid"
DEFAULT_DAEMON_MONITOR = "monitor/daemon_server.py"
DEFAULT_FILE_DATABASE = "database.csv"
DEFAULT_FILE_LOG = 'logfile.log'


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

            if self.check_file_existence(DEFAULT_TAR_FILE):

                subprocess.run(["tar", "-cvzf", DEFAULT_TAR_FILE, "-c", "../monitor"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            return 0

        except OSError:

            return 1

    def decompress_file(self):

        command = "tar -vzxf {}".format(DEFAULT_TAR_FILE)
        self.remote_access(command)

    def install_monitor(self):

        self.compress_file()
        self.send_file(DEFAULT_TAR_FILE, DEFAULT_TAR_FILE)
        self.decompress_file()

    def install_client(self):

        self.compress_file()
        self.send_file(DEFAULT_TAR_FILE, DEFAULT_TAR_FILE)
        self.decompress_file()

    def remote_start_zookeeper(self, id_processing, host, password):

        password_super_user = password + "\n"
        set_permission = "sudo -S"
        command_echo = "echo"
        command_start = "start"

        command_exec_permission = "chmod -R +x"
        command = "{} {} {}".format(set_permission, command_exec_permission, DEFAULT_PATH_ZOOKEEPER_SERVER)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_super_user)
        channel_stdin.flush()

        command = "{} {} >> {}".format(command_echo, str(id_processing), DEFAULT_ZOOKEEPER_ID)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        print(channel_stdout.read())
        print(channel_stderr.read())
        print(command)

        command = "{} {} {}".format(set_permission, DEFAULT_ZOOKEEPER_SERVER, command_start)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND+1)
        channel_stdin.write(password_super_user)
        channel_stdin.flush()

        print(command)
        print(channel_stdout.read())
        print(channel_stderr.read())

    def remote_start_monitors(self, id_processing, host, password):

        set_permission = "sudo -S"
        password_super_user = password + "\n"
        command_daemon_server = "python3 {}".format(DEFAULT_DAEMON_MONITOR)
        command_start_server = "--stop true "
        command = set_permission + command_daemon_server+command_start_server + "--id " + id_processing + ' --password '+ password
        command = command + " --host "+host
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_super_user)
        channel_stdin.flush()

        command_start_server = "--start true "
        command = set_permission + command_daemon_server+command_start_server + "--id " + id_processing + ' --password '+ password
        command = command + " --host "+host
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_super_user)
        channel_stdin.flush()

    def remove_stop_daemon(self, id_processing, host, password):

        password_msg = password + "\n"
        set_permission = "sudo -S "
        command_remove = "rm -r"
        command = "{} pkill python3".format(set_permission)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()

        command = "{} pkill java".format(set_permission)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()

        command = "{} {} monitor".format(set_permission, command_remove)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()

        command = "{} {} {}".format(set_permission, command_remove, DEFAULT_TAR_FILE)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()

        command = "{} {} {}".format(set_permission, command_remove, DEFAULT_FILE_DATABASE)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()

        command = "{} {} {}".format(set_permission, command_remove, DEFAULT_FILE_LOG)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()

    def remove_start_client(self, id_processing, host, password):

        password_msg = password + "\n"
        set_permission = "sudo -S "
        command_remove = "rm -r"
        command = "{} pkill python3".format(set_permission)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()

        command = "{} pkill java".format(set_permission)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()

        command = "{} {} monitor".format(set_permission, command_remove)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()

        command = "{} {} {}".format(set_permission, command_remove, DEFAULT_TAR_FILE)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()

        command = "{} {} {}".format(set_permission, command_remove, DEFAULT_FILE_DATABASE)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()

        command = "{} {} {}".format(set_permission, command_remove, DEFAULT_FILE_LOG)
        channel_stdin, channel_stdout, channel_stderr = self.connection_ssh.exec_command(command)
        time.sleep(DEFAULT_DELAY_COMMAND_SEND)
        channel_stdin.write(password_msg)
        channel_stdin.flush()