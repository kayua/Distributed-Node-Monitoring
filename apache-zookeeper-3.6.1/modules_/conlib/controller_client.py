#
#   @author: Nelson Antonio Antunes Junior
#   @email: nelson.a.antunes at gmail.com
#   @date: (DD/MM/YYYY) 23/01/2017

import kazoo.client, kazoo, kazoo.retry, ast, random, time, sys

from modules.model.worker import Worker
from modules.model.experiment import Experiment
from modules.model.role import Role

import logging


class PATHS(object):
	TASKS = "/tasks"
	EXPERIMENTS = "/experiments"

	CONNECTED_FREE = "/connected/free_workers"
	CONNECTED_BUSY = "/connected/busy_workers"

	REGISTERED_WORKERS = "/registered/workers"

	DISCONNECTED_WORKERS = "/disconnected/workers"

	ALL = [TASKS,
		   EXPERIMENTS,
		   CONNECTED_FREE,
		   CONNECTED_BUSY,
		   REGISTERED_WORKERS,
		   DISCONNECTED_WORKERS]


class COMMANDS(object):
	'''This class contains all the COMMANDS that the daemon_director.py module can handle.
	All the arguments must be passed as strings to the task_add() method'''

	EXIT = "EXIT"
	'''EXIT command, no arguments'''

	NEW_EXPERIMENT = "NWXP"
	'''NEW_EXPERIMENT command, 
	arguments: 
		"experiment"=<experiment_model>
	'''

	NEW_WORKER = "NWRK"
	'''NEW_WORKER commmand, if no private key or password are needed, use an empty string ("")
	arguments:
		"worker"=<worker_model>
	'''

	INSTALL_WORKER = "IWRK"
	'''INSTALL_WORKER commands
	argument:
		"worker"=<worker_model>
	'''

	SEND_EXPERIMENT = "SEND"
	'''SEND_EXPERIMENT command,
	argument:
		"experiment"=<experiment_model>
	'''

	START_WORKER = "STWK"
	'''START_WORKER command,
	argument:
		"worker"=<worker_model>
	'''

	RECOVER_ACTOR = "RCAT"
	'''RECOVER_ACTOR command,
	argument:
		"worker"=<worker_model>
	'''


class ControllerClient:
	"""docstring for ControllerClient"""

	# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s\t%(message)s', datefmt="%Y-%m-%d %H:%M:%S",filename='daemon_controller.log', filemode='w')

	#### SERVER CONFIGURATION METHODS
	# rafael
	# def __init__(self, zk_addr="127.0.0.1:2181"):
	def __init__(self, zk_addr):
		self.zk_addr = zk_addr
		logging.debug("Instantiating kazoo using address: {}".format(self.zk_addr))
		self.zk = kazoo.client.KazooClient(zk_addr, connection_retry=kazoo.retry.KazooRetry(max_tries=-1, max_delay=180))
		# self.zk = kazoo.client.KazooClient(self.zk_addr,
		# 								   connection_retry=kazoo.retry.KazooRetry(max_tries=2, max_delay=5))

		logging.debug("Kazoo instantiated at address: {}".format(self.zk_addr))
		try:
			logging.debug("Kazoo start... ")
			self.zk.start()
			logging.debug("Kazoo start done. ")

		except Exception as e:
			logging.error("Exception while connecting with Zookeeper:\n\n", e)
		logging.debug("End Controller Client init ")

	def config_stop(self):
		return self.zk.stop()

	def config_create_missing_paths(self):
		logging.debug(" before loop kz connected: {}".format(self.zk.connected))
		try:
			for path in PATHS.ALL:

				logging.debug(" path: {}".format(path))
				if path in [PATHS.CONNECTED_FREE, PATHS.CONNECTED_BUSY]:
					logging.debug(" before ensure path: {}".format(path))
					self.zk.ensure_path(path)
					logging.debug(" after ensure path: {}".format(path))
				else:
					logging.debug(" before ensure path: {}".format(path))
					self.zk.ensure_path(path)
					logging.debug(" after ensure path: {}".format(path))
		except Exception as e:
			logging.error(" Exception: {}".format(e))

		logging.debug(" after loop")

	#### TASKS CONTROL METHODS

	''' TASK = (task_cmd, args)
		args = {arg: value,...}

		task_cmd (string): task's function
		arg (string): an input for the task
		value (string): the arg's value

		It's identified by an id (== znode's name)
	'''

	def task_add(self, task_cmd, **task_args):
		task_path = self.zk.create("%s/t" % (PATHS.TASKS), value=task_cmd.encode(), sequence=True)
		# print "\t\t task_add task_path: ", task_path
		for key in task_args:
			# print "\t\t\t key : ", key, " value: ", task_args[key].encode()
			self.zk.create("%s/%s" % (task_path, key), value=task_args[key].encode())

		self.zk.create('%s/ready' % task_path)
		return task_path

	def task_get(self, task_id):
		logging.debug('task_id: %s', task_id)
		task_path = "%s/%s" % (PATHS.TASKS, task_id)
		logging.debug('PATHS.TASKS: %s', PATHS.TASKS)
		if self.zk.exists(task_path):
			# busy loop/wait required for sync
			logging.debug('Before loop')
			while not self.zk.exists('%s/ready' % task_path):
				pass

			logging.debug('After loop')
			t, _ = self.zk.get(task_path)
			logging.debug('t: %s', t)
			children = self.zk.get_children(task_path)
			args = {}
			for c in children:
				args[c], _ = self.zk.get("%s/%s" % (task_path, c))

			return (t, args)

		return None

	def task_del(self, task_id):
		task_path = "%s/%s" % (PATHS.TASKS, task_id)
		return self.zk.delete(task_path, recursive=True)

	#### EXPERIMENTS CONTROL METHODS

	def exp_add(self, exp):
		exp.path = self.zk.create("%s/e" % (PATHS.EXPERIMENTS), value=exp.name.encode(), sequence=True)

		exp.id = exp.path.split('/')[-1]

		self.zk.create("%s/file" % (exp.path), value=exp.filename.encode())
		self.zk.create("%s/is_snapshot" % (exp.path), value=str(exp.is_snapshot).encode())
		self.zk.create("%s/roles" % (exp.path))
		for role in exp.roles:
			role_path = self.zk.create("%s/roles/r" % (exp.path), value=role.name.encode(), sequence=True)
			self.zk.create("%s/parameters" % (role_path), value=role.parameters.encode())
			self.zk.create("%s/no_workers" % (role_path), value=str(role.no_workers).encode())

			role.id = role_path.split('/')[-1]

		self.zk.create("%s/actors" % (exp.path))

		return exp.path

	def exp_get(self, exp_path):

		if type(exp_path) is bytes:
			exp_path = exp_path.decode('utf-8')

		logging.debug("[CPEG1] exp_path: {}".format(exp_path))

		if self.zk.exists(exp_path):
			logging.debug("[CPEG2] exp_path: {}".format(exp_path))
			name, _ = self.zk.get(exp_path)

			logging.debug("[CPEG3] exp_path: {}/file".format(exp_path))
			file, _ = self.zk.get("%s/file" % (exp_path))

			logging.debug("[CPEG4] {}/is_snapshot".format(exp_path))
			is_snapshot, _ = self.zk.get("%s/is_snapshot" % (exp_path))

			logging.debug("[CPEG5] {}/roles".format(exp_path))
			role_id_list = self.zk.get_children("%s/roles" % (exp_path))

			logging.debug("[CPEG6]  {}/actors".format(exp_path))
			actor_id_list = self.zk.get_children("%s/actors" % (exp_path))

			roles = []
			actors = {}
			for role_id in role_id_list:
				role_path = "%s/roles/%s" % (exp_path, role_id)
				role_name, _ = self.zk.get(role_path)
				role_parameters, _ = self.zk.get("%s/parameters" % (role_path))
				role_no_workers, _ = self.zk.get("%s/no_workers" % (role_path))

				logging.debug("[CPEG7]  role_name: {} ".format(exp_path))
				role = Role(role_name, role_parameters, role_no_workers, role_id=role_id)

				logging.debug("[CPEG8]  role : {} ".format(role))
				roles.append(role)

			for actor_id in actor_id_list:
				actor_path = "%s/actors/%s" % (exp_path, actor_id)
				actor_worker_path, _ = self.zk.get(actor_path)
				if type(actor_worker_path) is bytes:
					actor_worker_path = actor_worker_path.decode('utf-8')

				logging.debug("[CPEG9]  actor_worker_path : {} ".format(actor_worker_path))
				actor_hostname = actor_worker_path.split('/')[-1]

				logging.debug("[CPEG10] checking {}/output ".format(actor_path))
				if self.zk.exists("%s/output" % (actor_path)):
					actors[actor_id] = (actor_hostname, self.zk.get("%s/output" % (actor_path))[0])

				else:
					actors[actor_id] = (actor_hostname, "(?)")

			return Experiment(name, file, roles, is_snapshot, exp_id=exp_path.split('/')[-1], actors=actors)

		return None

	def exp_get_all(self):
		exp_list = []

		exp_id_list = self.zk.get_children(PATHS.EXPERIMENTS)

		for exp_id in exp_id_list:
			exp_path = "%s/%s" % (PATHS.EXPERIMENTS, exp_id)
			exp_list.append(self.exp_get(exp_path))

		return exp_list

	def exp_get_by_id(self, exp_id):
		try:
			return self.exp_get("%s/%s" % (PATHS.EXPERIMENTS, exp_id))
		except Exception as e:
			logging.debug("Exception: {}".format(e))
			return None

	def exp_start(self, exp_id):
		path = "%s/%s/start" % (PATHS.EXPERIMENTS, exp_id)
		logging.debug(" create path: {}".format(path))
		try:
			return self.zk.create(path)

		except Exception as e:
			logging.error("Exception: {}".format(e))
			sys.exit(-1)

	def exp_ready_on_worker(self, exp_id, worker_path, actor_id):
		exp_path = "%s/%s" % (PATHS.EXPERIMENTS, exp_id)
		actor_path = '%s/actors/%s' % (exp_path, actor_id)
		exp_relative_path = self.zk.create("%s/torun/e" % (worker_path), value=exp_path.encode(), sequence=True)
		self.zk.create("%s/actor_path" % (exp_relative_path), value=actor_path.encode())

	def exp_create_actor(self, exp_id, worker_path, role_id, actor_path=''):
		exp_path = "%s/%s" % (PATHS.EXPERIMENTS, exp_id)
		if actor_path == '':
			actor_path = self.zk.create("%s/actors/a" % (exp_path), value=worker_path.encode(), sequence=True)
			self.zk.create("%s/role_id" % (actor_path), value=role_id.encode())
		else:
			self.zk.set(actor_path, value=worker_path.encode())

		return actor_path.split('/')[-1]

	#### WORKERS CONTROL METHODS

	def worker_add(self, worker):
		worker.path = "%s/%s" % (PATHS.REGISTERED_WORKERS, worker.hostname)
		try:
			self.zk.ensure_path(worker.path)

			self.zk.create("%s/user" % (worker.path), value=worker.username.encode())
			self.zk.create("%s/password" % (worker.path), value=worker.password.encode())
			self.zk.create("%s/pkey" % (worker.path), value=worker.pkey.encode())
			self.zk.create("%s/connection" % (worker.path))
			self.zk.create("%s/torun" % (worker.path))
			self.zk.create("%s/failures" % (worker.path), value=str(0).encode())
			self.zk.create("%s/connection_time" % (worker.path))
			self.zk.create("%s/disconnection_time" % (worker.path))
			self.zk.create("%s/active_time" % (worker.path), value=str(0.0).encode())
			self.zk.create("%s/actor_id" % (worker.path), value=str(worker.actor_id).encode())
			self.worker_add_disconnected(worker.hostname, 'ADDING WORKER', is_failure=False)

			return True

		except Exception as e:
			logging.error("Exception while adding worker: {}".format(e))
			return False

	def worker_check(self, worker_hostname):
		return self.zk.exists("%s/%s" % (PATHS.REGISTERED_WORKERS, worker_hostname))

	# def worker_add_disconnected(self, worker_hostname, worker_status, is_failure=True):
	# 	connection_path = "%s/%s" % (PATHS.DISCONNECTED_WORKERS, worker_hostname)
	# 	self.zk.ensure_path(connection_path)
	# 	worker_path = '%s/%s'%(PATHS.REGISTERED_WORKERS, worker_hostname)
	# 	self.zk.ensure_path(worker_path)
	#
	# 	try:
	# 		self.zk.create(connection_path, value=worker_path.encode(), makepath=True)
	# 	except:
	# 		print "cannot create connection_path: ", connection_path, " worker_path: ", worker_path, " worker_hostname: ", worker_hostname
	#
	# 	try:
	# 		self.zk.create("%s/status" % connection_path, value=worker_status.encode())
	# 		self.zk.set("%s/disconnection_time"%(worker_path), str(time.time()).encode())
	#
	# 	except:
	# 		self.zk.set("%s/status" % connection_path, worker_status.encode())
	#
	# 	if is_failure:
	# 		failures = 0
	# 		try:
	# 			failures = int(self.zk.get('%s/failures' % worker_path)[0])
	# 		except:
	# 			self.zk.ensure_path('%s/failures' % worker_path)
	#
	#
	# 		self.zk.set('%s/failures' % worker_path, value=str(failures+1).encode())
	#
	# 	self.zk.set("%s/connection" % worker_path, connection_path.encode())

	def worker_add_disconnected(self, worker_hostname, worker_status, is_failure=True):

		connection_path = "%s/%s" % (PATHS.DISCONNECTED_WORKERS, worker_hostname)
		worker_path = '%s/%s' % (PATHS.REGISTERED_WORKERS, worker_hostname)

		logging.debug("connection_path: {} worker_path: {}".format(connection_path, worker_path))
		try:
			logging.debug('[CP1] creating connection_path: {}'.format(connection_path))
			self.zk.create(connection_path, value=worker_path.encode())

			logging.debug('[CP2] creating %s/status: {} value: {}'.format(connection_path, worker_status.encode()))
			self.zk.create("%s/status" % connection_path, value=worker_status.encode())

			logging.debug('[CP3] creating  %s/disconnection_time: {} value: {}'.format(worker_path, str(time.time()).encode()))
			self.zk.set("%s/disconnection_time" % (worker_path), str(time.time()).encode())

		except Exception as e:
			logging.error("Exception : {}".format(e))

			logging.debug('[CP4] creating  %s/status: {} value: {}'.format(connection_path, worker_status.encode()))
			self.zk.set("%s/status" % connection_path, worker_status.encode())

		if is_failure:
			failures = int(self.zk.get('%s/failures' % worker_path)[0])
			self.zk.set('%s/failures' % worker_path, value=str(failures + 1).encode())

		logging.debug('node: %s/connection', worker_path)
		logging.debug('Sleeping 10 secs...')
		time.sleep(10)
		logging.debug('Sleeping Done')
		self.zk.set("%s/connection" % worker_path, connection_path.encode())
		logging.debug('[CP6] DONE')

	def worker_get_status(self, worker_path):

		worker_connection, _ = self.zk.get("%s/connection" % (worker_path))
		worker_connection = worker_connection.decode('utf-8')

		logging.debug('worker_connection {}'.format(worker_connection))

		worker_status = ''
		# logging.debug('ERROR: CL['+str(type(worker_connection)) + str(worker_connection)+']')
		if self.zk.exists(worker_connection) and worker_connection != '':

			if 'free_workers' in worker_connection:
				worker_status = 'IDLE'

			elif 'busy_workers' in worker_connection:
				worker_status = 'BUSY'

			else:
				worker_status, _ = self.zk.get("%s/status" % (worker_connection))
				worker_status = worker_status.decode('utf-8')

		elif self.zk.get_children("%s/torun" % (worker_path)) == []:
			worker_status = 'NEW LOST IDLE'

		else:
			worker_status = 'NEW LOST BUSY'

		logging.debug("worker_status : {} ".format(worker_status))
		return worker_status

	def worker_get(self, worker_path):
		# Rafael# line 351
		try:
			# worker_path = str(worker_path)#TODO#
			if type(worker_path) is str:
				pass
			else:
				worker_path = worker_path.decode('utf-8')

			logging.debug('[1] worker_path {}'.format(type(worker_path)))

			worker_hostname = worker_path.split('/')[-1]
			logging.debug('[2] worker_hostname: {}'.format(worker_hostname))

			worker_username, _ = self.zk.get("%s/user" % (worker_path))
			logging.debug('[3] worker_username {}'.format(worker_username))

			worker_password, _ = self.zk.get("%s/password" % (worker_path))
			logging.debug('[4] worker_password {}'.format(worker_password))

			worker_pkey, _ = self.zk.get("%s/pkey" % (worker_path))
			logging.debug('[5] worker_pkey {}'.format(worker_pkey))

			worker_connection, _ = self.zk.get("%s/connection" % (worker_path))
			logging.debug('[6] worker_connection {}'.format(worker_connection))

			worker_status = self.worker_get_status(worker_path)
			logging.debug('[7] worker_status {}'.format(worker_status))

			worker_active_time, _ = self.zk.get("%s/active_time" % (worker_path))
			logging.debug('[8] worker_active_time {}'.format(worker_active_time))

			worker_disconnection_time, _ = self.zk.get("%s/disconnection_time" % (worker_path))
			logging.debug('[9] worker_disconnection_time {}'.format(worker_disconnection_time))

			worker_connection_time, _ = self.zk.get("%s/connection_time" % (worker_path))
			logging.debug('[10] worker_connection_time {}'.format(worker_connection_time))

			worker_failures, _ = self.zk.get("%s/failures" % (worker_path))
			logging.debug('[11] worker_failures {}'.format(worker_failures))

			actor_id, _ = self.zk.get("%s/actor_id" % (worker_path))

			if type(actor_id) is str:
				pass
			else:
				actor_id = actor_id.decode('utf-8')
			logging.debug('[12] actor_id {}'.format(actor_id))

			worker_actors = []
			for i in self.zk.get_children("%s/torun" % (worker_path)):
				logging.debug('[12] worker_path %s', worker_path)
				logging.debug('[13] CL worker_path {}'.format(type(worker_path)))
				logging.debug('[13.5] CL E {}'.format(type(i)))
				var_aux = "%s/torun/%s/actor_path" % (worker_path, i)
				var_aux = var_aux.split('/')[-1]
				# var_aux = var_aux[0].split('/')[-1]
				worker_aux = self.zk.get("%s/torun/%s/actor_path" % (worker_path, i))
				worker_aux = worker_aux[0].decode('utf-8')
				# logging.debug('[13]ERROR {}'.format(type(y[0])))
				# logging.debug('[13]ERROR {}'.format(y[0]))
				# worker_actors += [self.zk.get("%s/torun/%s/actor_path" % (worker_path,i))[0].split('/')[-1]]
				worker_actors += [worker_aux.split('/')[-1]]
				logging.debug('[14] CL ')

			logging.debug('[15] CL')
			w = Worker(worker_hostname,
					   worker_username,
					   path=worker_path,
					   password=worker_password,
					   pkey=worker_pkey,
					   status=worker_status,
					   actors=worker_actors,
					   failures=int(worker_failures or '0'),
					   active_time=float(worker_active_time or '0'),
					   disconnection_time=float(worker_disconnection_time or '0'),
					   connection_time=float(worker_connection_time or '0'),
					   actor_id=actor_id)

			logging.debug('[16] CL {}'.format(w))
			return w

		except Exception as e:
			logging.exception('[17]ERROR_Exception: {}'.format(e))

	def worker_get_by_hostname(self, worker_hostname):
		# logging.debug('ERROR: CL['+str(type(worker_hostname)) + str(worker_hostname)+']')
		return self.worker_get("%s/%s" % (PATHS.REGISTERED_WORKERS, worker_hostname))

	def worker_get_experiments(self, worker_hostname):
		logging.debug(" [CPWGE1] worker_hostname: {}".format(worker_hostname))

		exp_local_path = "%s/%s/torun" % (PATHS.REGISTERED_WORKERS, worker_hostname)
		exp_list = []

		try:
			logging.debug(" CPWGE2] zk.get_children exp_local_path: {}".format(exp_local_path))
			exp_local_ids = self.zk.get_children(exp_local_path)

			for exp_local_id in exp_local_ids:
				logging.debug(" [CPWGE3] exp_local_id: {}".format(exp_local_id))

				#logging.debug("zk.get_children exp_local_path: {}".format(exp_local_path))
				exp_path, _ = self.zk.get("%s/%s" % (exp_local_path, exp_local_id))
				exp_path = exp_path.decode('utf-8')
				logging.debug(" [CPWGE4] exp_path: {}".format(exp_path))

				actor_path, _ = self.zk.get("%s/%s/actor_path" % (exp_local_path, exp_local_id))
				actor_path = actor_path.decode('utf-8')
				logging.debug(" [CPWGE5] actor_path: {}".format(exp_path))

				exp = self.exp_get(exp_path)
				logging.debug(" [CPWGE6] exp: {}".format(exp))
				exp.actor.path = actor_path
				exp.actor.role_id, _ = self.zk.get("%s/role_id" % actor_path)
				exp.actor.role_id = exp.actor.role_id.decode('utf-8')
				exp_list += [exp]

		except Exception as e:
			logging.error("Exception : {}".format(e))
			sys.exit(-1)

		return exp_list

	def worker_remove_experiments(self, worker_path):
		exp_local_path = "%s/torun" % worker_path
		exp_local_ids = self.zk.get_children(exp_local_path)
		for exp_local_id in exp_local_ids:
			self.zk.delete("%s/%s" % (exp_local_path, exp_local_id), recursive=True)

	def worker_remove(self, worker):
		try:
			if worker.path != '':
				self.zk.delete(worker.path, recursive=True)
				self.zk.delete('%s/%s' % (PATHS.DISCONNECTED_WORKERS, worker.hostname), recursive=True)
		except:
			pass

	def worker_get_all(self):
		logging.debug("CP1 PATHS.REGISTERED_WORKERS: {}".format(PATHS.REGISTERED_WORKERS))
		#self.zk.ensure_path(PATHS.REGISTERED_WORKERS)
		logging.debug("CP2 PATHS.REGISTERED_WORKERS: {}".format(PATHS.REGISTERED_WORKERS))
		workers_hostnames = self.zk.get_children(PATHS.REGISTERED_WORKERS, include_data=False)
		workers_list = []
		logging.debug("CP2")
		for worker_hostname in workers_hostnames:
			logging.debug("CP3")
			worker = self.worker_get_by_hostname(worker_hostname)
			logging.debug("CP4")
			workers_list.append(worker)

		logging.debug("CP5")
		return workers_list

	def worker_allocate(self, number_of_workers=1, alloc_list=[]):
		logging.debug('workChose0')
		workers_free_list = list(set(self.zk.get_children(PATHS.CONNECTED_FREE)) - set(alloc_list))
		logging.debug('workChose0.5 {}'.format(self.zk.get_children(PATHS.CONNECTED_FREE)))
		# logging.debug('workers_free_list %s', workers_free_list)
		# logging.debug('PATHS.CONNECTED_FREE %s', PATHS.CONNECTED_FREE)
		workers_chosen = []
		try:

			workers_chosen = random.sample(workers_free_list, number_of_workers)
			logging.debug('workChose1 {}'.format(PATHS.CONNECTED_FREE))
		except:
			logging.debug('workChose2')
			return None

		workers_allocated_list = []

		for w in workers_chosen:
			worker_allocated, _ = self.zk.get("%s/%s" % (PATHS.CONNECTED_FREE, w))
			workers_allocated_list.append(worker_allocated)

		return workers_allocated_list  # list of paths!

	def worker_update_connection_time(self, worker_path, time):
		self.zk.set("%s/connection_time" % worker_path, value=str(time).encode())

	#### WATCHERS METHODS

	def watch_new_tasks(self, event_handler):
		logging.debug("before watchers")
		try:
			kazoo.recipe.watchers.ChildrenWatch(self.zk, PATHS.TASKS, event_handler)
		except:
			pass
		logging.debug("after watchers")
