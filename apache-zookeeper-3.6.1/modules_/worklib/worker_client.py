#
#   @author: Nelson Antonio Antunes Junior
#   @email: nelson.a.antunes at gmail.com
#   @date: (DD/MM/YYYY) 27/01/2017
import shlex

from modules.worklib.snapshot import Snapshot
from kazoo.client import *
import kazoo, traceback, threading, imp, os, time, subprocess
import sys
import logging

# STATIC PATHS
class PATHS(object):
	CONNECTED_FREE = "/connected/free_workers"
	CONNECTED_BUSY = "/connected/busy_workers"
	DISCONNECTED = '/disconnected/workers'
	REGISTERED_WORKERS = "/registered/workers/"


def bytes_to_str(input):
	if type(input) is bytes:
		return input.decode('utf-8')
	else:
		return input

class Experiment(object):

	def __init__(self, exp_path, exp_name, exp_parameters, exp_actor_id, is_snapshot):
		logging.debug('\t\t\t #Checkpoint-EXP-1')

		self.path = bytes_to_str(exp_path)
		self.name = bytes_to_str(exp_name)

		#self.stdout = "{}.out".format(self.name)
		#self.stderr = "{}.err".format(self.name)
		self.stdout = "experiments/{}/{}.out".format(self.name, self.name)
		self.stderr = "experiments/{}/{}.err".format(self.name, self.name)

		self.fout = None
		self.ferr = None

		self.parameters = bytes_to_str(exp_parameters)

		self.popen = None

		self.actor_id = bytes_to_str(exp_actor_id)

		self.worker_torun_id = ''

		self.is_snapshot = bytes_to_str(is_snapshot)
		self.snapshot = Snapshot()

	def run(self, wclient):
		logging.debug('\t\t\t #Checkpoint-EXP-2')

		if self.is_snapshot:
			try:
				logging.debug("Running experiment snapshot...")
				exp_mod = imp.load_source('Actor', 'experiments/%s/Actor.py' % self.name)
				self.snapshot = exp_mod.Actor()
				self.snapshot.config(wclient, self.path, self.actor_id, 'experiments/%s/' % self.name)
				self.popen = threading.Thread(target=self.snapshot.start,
											  args=(self.parameters, 'experiments/%s/%s.' % (self.name, self.name)))
				self.popen.daemon = True
				self.popen.start()

			except Exception as e:
				logging.error("Exception: {}".format(e))
				traceback.print_exc()
				self.snapshot.poll = -2
		else:
			try:
				logging.debug("Running the experiment. self.parameters: {}".format(self.parameters))
				#self.popen = subprocess.Popen(["cd", "experiments/%s;" % self.name, "%s" % self.parameters, "1>%s.out" % self.name,"2>%s.err" % self.name])
				#param = self.parameters.split(" ")
				param = shlex.split(self.parameters)
				logging.debug("param: {}".format(param))
				#param += ["1>, "2>{}.err".format(self.name)]
				cwd = "%s/experiments/%s/" % (os.getcwd(), self.name)
				logging.debug("cwd: {}".format(cwd))
				#logging.debug("Running param: {} cwd: {} stdout: {} stderr: {}".format(param, cwd, self.stdout, self.stderr))
				self.fout = open(self.stdout, 'w')
				self.ferr = open(self.stderr, 'w')
				self.popen = subprocess.Popen(param, cwd=cwd, stdout=self.fout, stderr=self.ferr)
				logging.debug("popen: {}".format(self.popen))
				#self.poll = self.popen.poll()
				logging.debug("self.popen.poll(): {}".format(self.popen.poll()))

			except Exception as e:
				logging.error("Exception: {}".format(e))
				self.poll = -2

	def get_main_script(self):
		logging.debug('\t\t\t #Checkpoint-EXP-3')
		logging.debug("parameters: {}".format(self.parameters))
		return shlex.split(self.parameters)[1]
		#return self.parameters.split(" ")[1]


	def ps_based_is_running(self):
		logging.debug('\t\t\t #Checkpoint-EXP-4')

		#script = self.get_main_script()
		#cmd = "ps aux | grep %s | grep -v grep " % script
		cmd = "ps -p {} | grep -v TTY ".format(self.popen.pid)
		logging.debug("cmd: {}".format(cmd))
		#self.printd("ps_based_is_running - cmd " + cmd)
		#r = subprocess.call(cmd, shell=True)
		r = subprocess.getoutput(cmd)
		logging.debug("result: {}".format(r))
		#self.printd("ps_based_is_running - r " + r)
		is_running = True
		if r == "" or '<defunct>' in r:
			self.ferr.close()
			self.fout.close()
			is_running = False

		return is_running

	# def poll_based_is_running(self):
	# 	logging.debug('\t\t\t #Checkpoint-EXP-4.1 popen: {}'.format(self.popen))
	#
	# 	if self.popen.poll() is None:
	# 		logging.debug('\t\t Process ended. popen return code: {}'.format(self.popen.returncode))
	# 		# process terminated
	# 		self.ferr.close()
	# 		self.fout.close()
	# 		return False
	#
	# 	else:
	# 		return True

	def is_running(self):
		logging.debug('\t\t\t #Checkpoint-EXP-5')

		logging.debug("is_snapshot: {}".format(self.is_snapshot))
		if self.is_snapshot:
			if self.popen:
				return self.popen.is_alive()
			else:
				return False
		else:
			return self.ps_based_is_running()
			#return self.poll_based_is_running()

	def is_finished(self):
		logging.debug('\t\t\t #Checkpoint-EXP-6')

		if self.is_snapshot:
			return not (self.snapshot.poll is None)
		else:
			return not self.ps_based_is_running()
			#return not self.poll_based_is_running()

	def is_started(self):
		logging.debug("\t\t\t #Checkpoint-EXP-7")
		return self.popen


class WorkerClient(object):

	def __init__(self, zk_addr, worker_hostname=''):
		logging.debug('\t\t\t #Checkpoint-WK-1')
		self.current_experiments = []  # Experiment objects
		self.zk = KazooClient(zk_addr, connection_retry=kazoo.retry.KazooRetry(max_tries=-1, max_delay=250))
		self.zk_addr = zk_addr
		self.hostname = worker_hostname
		self.worker_path = PATHS.REGISTERED_WORKERS + worker_hostname
		self.reregister = True
		self.busy = None
		self.connection = None
		self.connection_timeout = 0
		self.zk.add_listener(lambda x: os._exit(1) if x == KazooState.LOST else None)
		self.zk.start()

	def connected(self):
		logging.debug('\t\t\t #Checkpoint-WK-2')
		if self.connection is None:
			return False
		if self.zk.exists(self.connection):
			return True
		self.connection = None
		return False

	@staticmethod
	def load_config_file(filepath):
		logging.debug('\t\t\t #Checkpoint-WK-3 filepath: {}'.format(filepath))
		cfg = {}
		f = open(filepath, "r")
		for l in f.readlines():
			opt, arg = l.split("=")
			cfg[opt] = arg[:-1]
		return cfg

	def worker_active_time_update(self, adding_time):
		logging.debug('\t\t\t #Checkpoint-WK-4')
		active_time = float(self.zk.get("%s/active_time" % self.worker_path)[0])
		self.zk.set("%s/active_time" % self.worker_path, value=str(active_time + adding_time).encode())

	def worker_keep_alive(self, time, busy=False):
		logging.debug('\t\t\t #Checkpoint-WK-5')
		connected = False
		try:
			connected = self.connected()
		except:
			pass

		if connected:
			self.worker_active_time_update(time)

		if (not self.connection) or busy != self.busy:

			connection_path = "%s/%s" % (PATHS.CONNECTED_BUSY if busy else PATHS.CONNECTED_FREE, self.hostname)
			delete_path = "%s/%s" % (PATHS.CONNECTED_BUSY if not busy else PATHS.CONNECTED_FREE, self.hostname)

			try:
				self.zk.create(connection_path, value=self.worker_path.encode(), ephemeral=True)
				self.zk.set("%s/connection" % self.worker_path, value=connection_path.encode())
			except:
				pass

			try:
				self.zk.delete(delete_path)
			except Exception as e:
				pass

			try:
				self.zk.delete("%s/%s" % (PATHS.DISCONNECTED, self.hostname), recursive=True)
			except:
				pass

			self.connection = connection_path
			self.busy = busy

		return self.connection

	def watch_new_exp(self):
		logging.debug('\t\t\t #Checkpoint-WK-6')
		kazoo.recipe.watchers.ChildrenWatch(self.zk, "%s/torun" % self.worker_path, self.exp_handler)

	def exp_get(self, exp_path):
		logging.debug('\t\t\t #Checkpoint-WK-7')
		exp_name, _ = self.zk.get(exp_path.decode('utf-8'))

		exp_cfg = WorkerClient.load_config_file("experiments/%s/info.cfg" % exp_name.decode('utf-8'))

		return Experiment(exp_path, exp_name, exp_cfg["parameters"], exp_cfg["actor_id"], eval(exp_cfg["is_snapshot"]))

	def exp_ready(self, exp_obj):
		logging.debug('\t\t\t #Checkpoint-WK-8')
		wc = WorkerClient(self.zk_addr)

		@self.zk.DataWatch('%s/start' % exp_obj.path)
		def ready(data, stat):
			if stat:
				exp_obj.run(wc)
				return False

	def exp_finished(self, exp_obj):
		logging.debug('\t\t\t #Checkpoint-WK-9')

		# stdout = "experiments/{}/{}".format(exp_obj.name, exp_obj.stdout)
		# stderr = "experiments/{}/{}".format(exp_obj.name, exp_obj.stderr)
		code_output = exp_obj.popen.poll() if not exp_obj.is_snapshot else exp_obj.snapshot.poll
		output = '(%i): ' % code_output
		logging.debug(' code output: {}'.format(output))
		try:
			msg = None
			if os.path.isfile(exp_obj.stdout):
				msg = " stdout: {}".format(exp_obj.stdout)
			else:
				msg = " stdout not found!: {}".format(exp_obj.stdout)

			logging.debug(msg)
			output += msg

			if os.path.isfile(exp_obj.stderr):
				output += " stderr found: {}".format(exp_obj.stderr)
				f_error = open(exp_obj.stderr, 'r+')
				error = f_error.read()

				if error != '':
					output += '\nerror: ' + error
				logging.info(output)

			else:
				msg = " stderr not found: {}".format(exp_obj.stderr)
				logging.debug(msg)

		except Exception as e:
			output += 'Exception while processing results: {}'.format(e)

		try:
			self.zk.create("%s/actors/%s/output" % (exp_obj.path, exp_obj.actor_id), value=output.encode())

			self.zk.delete("%s/torun/%s" % (self.worker_path, exp_obj.worker_torun_id), recursive=True)
		except:
			pass

		self.current_experiments.remove(exp_obj)

	def exp_handler(self, exp_diff):
		logging.debug('\t\t\t #Checkpoint-WK-10')
		logging.debug('[1]#torun')
		try:
			logging.debug('[2]#torun')
			exp_new = [n for n in exp_diff if n not in self.current_experiments]
			logging.debug('[3]#torun')
			for exp_id in exp_new:
				logging.debug('[4]#torun')
				if self.zk.exists("%s/torun/%s" % (self.worker_path, exp_id)):
					logging.debug('[5]#torun')
					# not deleted
					exp_path, _ = self.zk.get("%s/torun/%s" % (self.worker_path, exp_id))
					logging.debug('[6]#torun')
					exp_obj = self.exp_get(exp_path)
					logging.debug('[7]#torun')
					exp_obj.worker_torun_id = exp_id
					logging.debug('[8]#torun')
					#print "append... len current_experiments before %s"%len(self.current_experiments)
					self.current_experiments.append(exp_obj)
					logging.debug('[9]#torun')
					#print "append... len current_experiments before %s" % len(self.current_experiments)
					self.exp_ready(exp_obj)
					logging.debug('[10]#torun')
		except:
			logging.debug('[11]#torun')
			traceback.print_exc()
			logging.debug('[12]#torun')

	def exp_load(self):
		logging.debug('\t\t\t #Checkpoint-WK-11')
		logging.debug('[1]#exp_load')
		self.current_experiments = []  # Experiment objects
		logging.debug('[2]#exp_load')
		self.watch_new_exp()
		logging.debug('[3]#exp_load')

	def snap_get(self, actor_path):
		logging.debug('\t\t\t #Checkpoint-WK-12')
		if self.zk.exists("%s/data" % actor_path):
			s, _ = self.zk.get("%s/data" % actor_path)
			return eval(s)

		return None

	def snap_set(self, actor_path, value):
		logging.debug('\t\t\t #Checkpoint-WK-13')
		if self.zk.exists("%s/data" % actor_path):
			self.zk.set("%s/data" % actor_path, str(value).encode())
		else:
			self.zk.create("%s/data" % actor_path, str(value).encode())
