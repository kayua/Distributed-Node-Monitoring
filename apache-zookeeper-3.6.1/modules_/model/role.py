#
#	@author: Nelson Antonio Antunes Junior
#	@email: nelson.a.antunes at gmail.com
#	@date: (DD/MM/YYYY) 17/02/2017

import ast

def bytes_to_str(input):

	if type(input) is bytes:
		return input.decode('utf-8')
	else:
		return input


class Role(object):
	"""docstring for Role"""
	def __init__(self, name, parameters, no_workers, role_id=""):

		self.name = bytes_to_str(name)
		self.parameters = bytes_to_str(parameters)
		self.id = bytes_to_str(role_id)
		self.no_workers = bytes_to_str(no_workers)
		
	@staticmethod
	def decode(encoded_role):
		
		role_dict = ast.literal_eval(encoded_role)

		role = Role(role_dict["name"], role_dict["parameters"], role_dict["no_workers"], role_dict["id"])

		return role

	def __str__(self):
		return str({"name": self.name, "parameters": self.parameters, "no_workers": self.no_workers, "id": self.id})

	def encode(self):
		return str(self).encode()