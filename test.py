from kazoo.client import KazooClient
zk = KazooClient(hosts='192.168.1.104:2181,192.168.1.104:2181,192.168.1.105:2181', read_only=True)
zk.start()