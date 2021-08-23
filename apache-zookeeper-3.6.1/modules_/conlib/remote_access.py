#
#	@author: Nelson Antonio Antunes Junior
#	@email: nelson.a.antunes at gmail.com
#	@date: (DD/MM/YYYY) 24/01/2017

import paramiko, paramiko.rsakey, io, scp, hashlib, os
import logging
def MD5(filename):
	hash_md5 = hashlib.md5()
	with open(filename, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)
	return hash_md5.hexdigest()


class Channel(object):
	def __init__(self, hostname, username=None, password=None,
		pkey=None, timeout=None):

		self.ssh = paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		if type(hostname) is bytes:
			self.hostname = hostname.decode('utf-8')
		else:
			self.hostname = hostname
		
		if type(username) is bytes:
			self.username = username.decode('utf-8')
		else:
			self.username = username
		
		self.timeout = timeout

		if type(password) is bytes:
			password = password.decode('utf-8')

		if type(pkey) is bytes:
			pkey = pkey.decode('utf-8')

		if password == "":
			password = None
		if pkey is None or pkey == "":
			self.pkey = None
		else:
			self.pkey = paramiko.rsakey.RSAKey(file_obj=io.StringIO(pkey), password=password)
			password = None

		self.password = password
		self.path = "~/"
		try:
			#logging.debug('connect_y')
			self.ssh.connect(hostname=self.hostname, username=self.username,
				password=self.password, pkey=self.pkey, timeout=self.timeout)
			#logging.debug('connect_n')
		except Exception as e:
			logging.debug('Excepetion: {}'.format(e))
			raise e
		self.scp = scp.SCPClient(self.ssh.get_transport())
		self.connected = True

	def _actual_path(self, path):
		return self.path+path

	def run(self, cmd, async_=False):
		if not self.connected:
			return None,None,None
		cmd = "cd %s; %s" % (self.path, cmd)

		if async_:
			return tuple(self.ssh.exec_command(cmd)[1:])

		_,stdout,stderr = self.ssh.exec_command(cmd)
		
		stdout.channel.recv_exit_status()
		stderr.channel.recv_exit_status()

		return (stdout, stderr)

	def chkdir(self, path):
		stdout,_ = self.run("[ -d %s ]" % path)
		return stdout.channel.recv_exit_status() == 0

	def chkfile(self, path):
		stdout,_ = self.run("[ -f %s ]" % path)
		return stdout.channel.recv_exit_status() == 0

	def chdir(self, path):

		if type(path) is bytes:
			path = path.decode('utf-8')

		if path[-1] != "/":
			path += "/"

		if path[0] in ["/", "~"]:
			if self.chkdir(path):
				self.path = path
		else:
			if self.chkdir(path):
				self.path = self._actual_path(path)

	def mkdir(self, path):
		self.run("mkdir -p %s" % path)

	def _cmpfiles(self, local_path, remote_path):
		stdout,_ = self.run("md5sum %s" % remote_path)
		# logging.debug('putt 2.5.2 %s', stdout.read().decode('utf-8').split(' ', 1)[0])
		# logging.debug('putt 2.5.2 %s', MD5(local_path))
		# return stdout.read().split(" ")[0] != MD5(local_path)
		return stdout.read().decode('utf-8').split(' ', 1)[0] != str(MD5(local_path))

	def put(self, local_path, remote_path):
		#logging.debug('putt start')
		if self.connected and os.path.isfile(local_path):
			#logging.debug('putt 1')
			if self.chkfile(self._actual_path(remote_path)):
				#logging.debug('putt 2')
				if self._cmpfiles(local_path, self._actual_path(remote_path)):
					#logging.debug('putt 3')
					self.scp.put(local_path,self._actual_path(remote_path))
					#logging.debug('putt 4')
					return True
			else:
				#logging.debug('putt 5')
				self.scp.put(local_path,self._actual_path(remote_path))
				#logging.debug('putt 6')
				return True
			#logging.debug('putt 7')
		return False

	def get(self, remote_path, local_path):
		if self.connected and self.chkfile(self._actual_path(remote_path)):
			if os.path.isfile(local_path):
				if self._cmpfiles(local_path, self._actual_path(remote_path)):
					self.scp.get(self._actual_path(remote_path),local_path)
					return True
			else:
				self.scp.get(self._actual_path(remote_path),local_path)
				return True
		return False

	def get_full_path(self, remote_path, local_path):
		#print("connected:%s self.chkfile(remote_path): %s " % (self.connected, self.chkfile(remote_path) ))
		if self.connected and self.chkfile(remote_path):
			#print(" os.path.isfile(local_path):%s " % ( os.path.isfile(local_path) ))
			if os.path.isfile(local_path):
				#print(" self._cmpfiles(local_path, remote_path):%s " % (self._cmpfiles(local_path, remote_path)))
				if self._cmpfiles(local_path, self._actual_path(remote_path)):
					self.scp.get(self._actual_path(remote_path),local_path)
					return True
			else:
				self.scp.get(remote_path, local_path)
				return True
		return False

	def close(self):
		if self.connected:
			return self.ssh.close()
		return None
