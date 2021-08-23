#
#   @author: Nelson Antonio Antunes Junior
#   @email: nelson.a.antunes at gmail.com
#   @date: (DD/MM/YYYY) 08/02/2017

import ast

SCRIPT = "daemon_worker.py"
# import logging

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s\t%(message)s', datefmt="%Y-%m-%d %H:%M:%S",filename='daemon_controller.log', filemode='w')

LOGGING_LEVEL = 100

def bytes_to_str(input):

	if type(input) is bytes:
		return input.decode('utf-8')
	else:
		return input


class Worker(object):
	"""docstring for Worker"""

	def __init__(self, hostname, username, path="", password="", pkey="", status="", actors=[], active_time=0.0,
				 failures=0, disconnection_time=0.0, connection_time=0, actor_id="default"):

		self.path = path # path means ZK path and must be byte string
		self.hostname = bytes_to_str(hostname)
		self.username = bytes_to_str(username)
		self.password = bytes_to_str(password)
		self.pkey = bytes_to_str(pkey)
		self.status = bytes_to_str(status)

		self.active_time = bytes_to_str(active_time)
		self.failures = bytes_to_str(failures)
		self.disconnection_time = bytes_to_str(disconnection_time)
		self.connection_time = bytes_to_str(connection_time)
		self.actors = bytes_to_str(actors)
		self.actor_id = bytes_to_str(actor_id)

	@staticmethod
	def decode(encoded_worker):
		worker_dict = ast.literal_eval(encoded_worker)
		# logging.debug(type(encoded_worker))
		# logging.debug('Literal_Debug: ' + encoded_worker)
		worker = Worker(worker_dict["hostname"],
						worker_dict["username"],
						path=worker_dict["path"],
						password=worker_dict["password"],
						pkey=worker_dict["pkey"],
						status=worker_dict["status"],
						actor_id=worker_dict["actor_id"])

		return worker

	@staticmethod
	def get_script():
		return SCRIPT

	def get_command(self):
		return "python3 {} --id {} --log {} ".format(SCRIPT, self.actor_id, LOGGING_LEVEL)

	def get_command_stop(self):
		return "{} stop".format(self.get_command())

	def get_command_restart(self):
		return "{} restart".format(self.get_command())

	def get_command_start(self):
		return "{} start".format(self.get_command())

	def get_remote_path(self):
		return "actor_{}".format(self.actor_id)

	def get_remote_experiment_path(self):
		return "{}/experiments".format(self.get_remote_path())

	def id(self):
		if self.path != "":
			return self.path.split("/")[-1]
		return None

	def __str__(self):
		return str({"path": self.path,
					"hostname": self.hostname,
					"actor_id": self.actor_id,
					"username": self.username,
					"password": self.password,
					"pkey": self.pkey,
					"status": self.status})

	# "pkey": "{}...{}".format(self.pkey[:10], self.pkey[-10:]),
	def encode(self):
		return str(self).encode()
