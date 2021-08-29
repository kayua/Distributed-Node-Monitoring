import sys
import time
from datetime import datetime
from kazoo.client import KazooClient
from lib.interface.channel import Channel
from lib.interface.view import View
from lib.interface.view import print_help

DEFAULT_SERVER_LOGS = "servers/server_list.log"
DEFAULT_CLIENTS_LOGS = "servers/client_list.log"
DEFAULT_SETTINGS = "settings/config.txt"
DEFAULT_ZOOKEEPER_SETTINGS = "monitor/apache-zookeeper-3.6.1/conf/zoo.cfg"
DEFAULT_PATH_NUM_CLIENTS = "/number_clients"
DEFAULT_PATH_NUM_SERVERS = "/number_servers"
DEFAULT_SIGNAL_SYNC = "/signal_sync"
DEFAULT_SIGNAL_HOUR = "/server_hour"
DEFAULT_CODIFICATION_FILE = "utf-8"
DEFAULT_NUMBER_CLIENTS = 0


def add_set_servers(hostname, username, password):

    file_servers = open(DEFAULT_SERVER_LOGS, "a+")
    new_server = "{}:{}:{}-".format(hostname, username, password)
    file_servers.write(new_server)
    file_servers.close()


def add_set_client(hostname, username, password):

    file_clients = open(DEFAULT_CLIENTS_LOGS, "a+")
    new_client = "{}:{}:{}-".format(hostname, username, password)
    file_clients.write(new_client)
    file_clients.close()


def get_set_servers():

    file_servers = open(DEFAULT_SERVER_LOGS, "r")
    list_servers = file_servers.read().split("-")
    return list_servers[:-1]


def install_servers(hostname, user, password):

    channel = Channel()

    if channel.connect(hostname, user, password):

        return True

    channel.install_monitor()
    channel.remote_access("")


def install_client(hostname, user, password):

    channel = Channel()

    if channel.connect(hostname, user, password):

        return True

    channel.install_client()


def create_settings_servers(list_servers):

    zookeeper_settings_pointer = open(DEFAULT_SETTINGS, "+a")
    zookeeper_settings_pointer.write("\n")

    for i in range(len(list_servers)):

        zookeeper_server = "server.{}={}:2888:3888\n".format(str(i + 1), list_servers[i])
        zookeeper_settings_pointer.write(zookeeper_server)

    zookeeper_settings_pointer.close()


def get_date_hour():

    return str(datetime.today())


def register_metadata(hosts, num_servers):

    print("\n     Creating registers of session")

    zookeeper_client = KazooClient(hosts=hosts, read_only=True)
    zookeeper_client.start()

    if not zookeeper_client.exists(DEFAULT_PATH_NUM_CLIENTS):

        zookeeper_client.create(DEFAULT_PATH_NUM_CLIENTS, b"0")

    number_servers_byte = num_servers.encode(DEFAULT_CODIFICATION_FILE)

    if not zookeeper_client.exists(DEFAULT_PATH_NUM_SERVERS):

        zookeeper_client.create(DEFAULT_PATH_NUM_SERVERS, number_servers_byte)

    print("\n         - Create data struct in Servers")

    for i in range(int(num_servers)):

        server_name = "/server{}".format(str(i+1))

        if not zookeeper_client.exists(server_name):

            zookeeper_client.create(server_name, b"False")

    print("\n         - Synchronizing server nodes")

    if not zookeeper_client.exists(DEFAULT_SIGNAL_SYNC):

        zookeeper_client.create(DEFAULT_SIGNAL_SYNC, b"False")

    if not zookeeper_client.exists(DEFAULT_SIGNAL_HOUR):

        zookeeper_client.create(DEFAULT_SIGNAL_HOUR, get_date_hour().encode(DEFAULT_CODIFICATION_FILE))


def clear_metadata(hosts):

    print("     Remove registers of session")

    zookeeper_client = KazooClient(hosts=hosts, read_only=True)
    zookeeper_client.start()
    number_clients, _ = zookeeper_client.get(DEFAULT_PATH_NUM_CLIENTS)

    for i in range(0, int(number_clients.decode(DEFAULT_CODIFICATION_FILE))):

        client_name = "/client{}".format(str(i))
        zookeeper_client.delete(client_name, recursive=True)

    number_servers, _ = zookeeper_client.get(DEFAULT_PATH_NUM_SERVERS)

    for i in range(0, int(number_servers.decode(DEFAULT_CODIFICATION_FILE))):

        server_name = "/server{}".format(str(i))
        zookeeper_client.delete(server_name, recursive=True)

    zookeeper_client.delete(DEFAULT_PATH_NUM_SERVERS, recursive=True)
    zookeeper_client.delete(DEFAULT_PATH_NUM_CLIENTS, recursive=True)
    zookeeper_client.delete(DEFAULT_SIGNAL_SYNC, recursive=True)
    zookeeper_client.delete(DEFAULT_SIGNAL_HOUR, recursive=True)


def start_servers():

    saved_nodes = get_set_servers()
    hostname_list, username_list, password_list = [], [], []

    for i in saved_nodes:

        hostname_list.append(i.split(":")[0])
        username_list.append(i.split(":")[1])
        password_list.append(i.split(":")[2])

    host_list = ":2181,".join(hostname_list) + ":2181"

    create_settings_servers(hostname_list)

    for i in range(len(hostname_list)):

        channel = Channel()
        print("         - {} Starting Zookeeper server".format(hostname_list[i]))
        channel.connect(hostname_list[i], username_list[i], password_list[i])
        channel.send_file(DEFAULT_SETTINGS, DEFAULT_ZOOKEEPER_SETTINGS)
        channel.remote_start_zookeeper(str(i+1), host_list, password_list[i])

    time.sleep(20)

    for i in range(len(hostname_list)):

        channel = Channel()
        print("         - {} Starting monitor".format(hostname_list[i]))
        channel.connect(hostname_list[i], username_list[i], password_list[i])
        channel.remote_start_monitors(str(i+1), host_list, password_list[i])

    register_metadata(host_list, str(len(hostname_list)))
    print("\n")


def stop_servers():

    saved_nodes = get_set_servers()
    hostname_list, username_list, password_list = [], [], []

    print("\n     Starting Servers: \n")

    for i in saved_nodes:

        hostname_list.append(i.split(":")[0])
        username_list.append(i.split(":")[1])
        password_list.append(i.split(":")[2])

    host_list = ":2181,".join(hostname_list) + ":2181"

    for i in range(len(hostname_list)):

        channel = Channel()
        print("         - {} Stopping monitor".format(hostname_list[i]))
        channel.connect(hostname_list[i], username_list[i], password_list[i])
        channel.remove_stop_daemon(str(i+1), host_list, password_list[i])

    clear_metadata(host_list)
    print("\n")


def start_client(host, username, password):

    saved_nodes = get_set_servers()
    hostname_list = []

    for i in saved_nodes:

        hostname_list.append(i.split(":")[0])

    host_list = ":2181,".join(hostname_list) + ":2181"
    channel = Channel()
    print("         - {} Starting client".format(host))
    channel.connect(host, username, password)
    channel.remote_start_client(host_list, password)
    print("\n")


def remove_servers():

    saved_nodes = get_set_servers()
    hostname_list, username_list, password_list = [], [], []

    print("\n     Starting Servers: \n")

    for i in saved_nodes:

        hostname_list.append(i.split(":")[0])
        username_list.append(i.split(":")[1])
        password_list.append(i.split(":")[2])

    host_list = ":2181,".join(hostname_list) + ":2181"

    for i in range(len(hostname_list)):

        channel = Channel()

        print("         - {} Stopping monitor".format(hostname_list[i]))
        channel.connect(hostname_list[i], username_list[i], password_list[i])
        channel.remove_stop_daemon(str(i), host_list, password_list[i])

    clear_metadata(host_list)
    print("\n")


def init_view():

    print("")
    view = View()
    view.print_view()
    print_help()
    print("Saved Servers:", end=" ")

    saved_nodes = get_set_servers()

    for i in saved_nodes:
        print(i.split(":")[0], end=" ")

    print("\n")


def choice_command(commands):

    if commands[0] == "ServerInstall":

        print("\n     Please wait: Installing")

        if install_servers(commands[-3], commands[-2], commands[-1]):

            print("\n     Installation Error\n")

        else:

            print("\n     Successfully Installation\n")
            add_set_servers(commands[-3], commands[-2], commands[-1])

    elif commands[0] == "ClientInstall":

        print("\n     Please wait: Installing")

        if install_client(commands[-3], commands[-2], commands[-1]):
            print("\n     Installation Error\n")

        else:

            print("\n     Successfully Installation\n")
            add_set_client(commands[-3], commands[-2], commands[-1])

    elif commands[0] == "ServerStart":

        print("\n     Starting Servers: \n")
        start_servers()

    elif commands[0] == "ServerStop":

        print("\n     Stopping Servers: \n")
        stop_servers()

    elif commands[0] == "ServerUninstall":

        print("\n     Stopping Servers: \n")
        remove_servers()

    elif commands[0] == "ClientAdd":

        print("\n     Starting Client: \n")
        start_client(commands[-3], commands[-2], commands[-1])

    elif commands[0] == "exit":

        exit(0)


def main():

    init_view()

    while True:

        commands = input('Command > ')
        commands = commands.split(" ")
        choice_command(commands)


if __name__ == '__main__':
    sys.exit(main())
