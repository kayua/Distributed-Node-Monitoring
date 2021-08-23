#
#   @author: Nelson Antonio Antunes Junior
#   @email: nelson.a.antunes at gmail.com
#   @date: (DD/MM/YYYY) 25/05/2017

import sys, time, traceback
sys.path.append("..")

class Snapshot(object):
	def __init__(self):
		self.values = {}
		self.types = {}
		self.poll = None
		self.local_path = ''

	def config(self, wclient, exp_path='', actor_id='', local_path=''):
		self.actor_path = "%s/actors/%s" % (exp_path, actor_id)
		self.actor_id = actor_id
		self.wclient = wclient
		self.local_path = local_path
		self._load()

	def start(self, args, name=None):
		fdo = None
		fde = None
		if name != None:
			fdo = open(name+'.out','a+',1)
			sys.stdout.write(fdo)			
			fde = open(name+'.err','a+',1)
			sys.stderr.write(fde)

		try:
			self.run(args)
			self.poll = 0
		except:
			traceback.print_exc()
			self.poll = -1

		fdo.close() if fdo != None else None
		fde.close() if fde != None else None

	def run(self, args):
		NotImplemented()

	def _save(self):
		data_dict = {k:v for k,v in zip(iter(self.values.keys()),list(zip([x.__name__ for x in iter(self.types.values())],iter(self.values.values()))))}
		if data_dict != {}:
			self.wclient.snap_set(self.actor_path, data_dict)

	def _load(self):
		data_dict = self.wclient.snap_get(self.actor_path)
		if data_dict != None:
			for k,v in data_dict.items():
				self.types[k] = eval(v[0])
				self.values[k] = v[1]

	def get(self, name):
		try:
			return self.values[name]
		except:
			return None

	def set(self, name, value, check_types=True):
		if not (name in self.values) or not check_types or (type(value) == self.types[name] and check_types):
			self.values[name] = value
			self.types[name] = type(value)
			return True
		return False

	def open_file(self, filename, mode):
		return open(self.local_path+filename,mode)

class Testcase(Snapshot):	
	def run(self, args):
		local_counter = 0
		while True:
			time.sleep(5)
			counter = self.get('counter')

			if counter:
				counter += 1
				self.set('counter', counter)
			else:
				self.set('counter', 1)			

			local_counter+=1

			if counter == 20:
				print('snapshot counter:', counter)
				print('local counter:', local_counter)
				break
