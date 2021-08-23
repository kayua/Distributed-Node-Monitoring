#
#	@author: Nelson Antonio Antunes Junior
#	@email: nelson.a.antunes at gmail.com
#	@date: (DD/MM/YYYY) 13/02/2017

import shutil, ast, os, sys
sys.path.append("..")
from .role import Role
import logging

def bytes_to_str(input):
	if type(input) is bytes:
		return input.decode('utf-8')
	else:
		return input

class Experiment(object):
	"""docstring for Experiment"""

	class Actor(object):
		def __init__(self):
			self.path = ''
			self.role_id = ''			

	def __init__(self, name, filename, roles, is_snapshot, exp_id="", actors={}):
		self.name = name
		if filename is None:
			self.filename = ''
		else:
			self.filename = bytes_to_str(filename)

		self.roles = bytes_to_str(roles)
		self.is_snapshot = bytes_to_str(is_snapshot)
		self.id = bytes_to_str(exp_id)
		self.actors = bytes_to_str(actors)
		self.actor = self.Actor()
		
	def save_file(self, fileobj):
		shutil.copyfileobj(fileobj, open(os.path.expanduser("~/controller/experiments/%s" % self.filename), 'w'))

	@staticmethod
	def decode(encoded_exp):
		
		exp_dict = ast.literal_eval(encoded_exp)
		roles = []
		for role in exp_dict["roles"]:
			roles.append(Role.decode(role))
		exp = Experiment(exp_dict["name"], exp_dict["filename"], roles, exp_dict["is_snapshot"], exp_dict["id"])

		return exp

	def __str__(self):
		roles_str = []
		for role in self.roles:
			roles_str.append(str(role))
		return str({"name": self.name, "filename": self.filename, "roles": roles_str, "is_snapshot": self.is_snapshot, "id": self.id})

	def encode(self):
		return str(self).encode()
