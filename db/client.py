# -*- coding: utf-8 -*-

class Client(object):
	"""docstring for Client"""
	def __init__(self, id_client=-1):
		super(Client, self).__init__()
		self.id = id_client
		self.email = None
		self.shop_name = None
		self.shop_address = None
		self.delivery_address = None
		self.billing_address = None
		self.person_name = None

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			if self.id != other.id:
				return False
			if self.email != other.email:
				return False
			if self.shop_name != other.shop_name:
				return False
			if self.shop_address != other.shop_address:
				return False
			if self.delivery_address != other.delivery_address:
				return False
			if self.billing_address != other.billing_address:
				return False
			if self.person_name != other.person_name:
				return False
			return True

	def __ne__(self, other):
		return not self.__eq__(other)

	def get_client_id(self):
		''' returns Client's id '''
		return self.id

	def get_client_email(self):
		''' returns Client's email '''
		return self.email

	def set_client_email(self, email):
		''' sets Client's email '''
		self.email = email
		return self

	def get_client_shop_name(self):
		''' returns Client's shop name '''
		return self.shop_name

	def set_client_shop_name(self, shop_name):
		''' sets Client's shop name '''
		self.shop_name = shop_name
		return self

	def get_client_shop_address(self):
		''' returns Client's shop address '''
		return self.shop_address

	def set_client_shop_address(self, address):
		''' sets Client's shop address '''
		if type(address) == list:
			self.shop_address = ';'.join(address)
		else: # hopefully type(address) == str
			self.shop_address = address
		return self

	def get_client_delivery_address(self):
		''' returns Client's delivery address '''
		return self.delivery_address

	def set_client_delivery_address(self, address):
		''' sets Client's delivery address '''
		if type(address) == list:
			self.delivery_address = ';'.join(address)
		else:
			self.delivery_address = address
		return self

	def get_client_billing_address(self):
		''' returns Client's billing address '''
		return self.billing_address

	def set_client_billing_address(self, address):
		''' sets Client's billing address '''
		if type(address) == list:
			self.billing_address = ';'.join(address)
		else:
			self.billing_address = address
		return self

	def get_client_person_name(self):
		''' returns Client's name '''
		return self.person_name

	def set_client_person_name(self, person_name):
		''' sets Client's name '''
		self.person_name = person_name
		return self

	def to_string(self):
		''' returns a formatted string of all attributes '''
		try:
			string  = 'Client id: ' + (str(self.id) if self.id != -1 else "None")
		except AttributeError:
			pass
		try:
			string += ', contact person: ' + (self.person_name if self.person_name != None else "None") + '\n'
		except AttributeError:
			pass
		try:
			string += "Mail : " + (self.email if self.email != None else "None") + '\n'
		except AttributeError:
			pass
		try:
			string += "Shop_address : " + (self.shop_address if self.shop_address != None else "None") + '\n'
		except AttributeError:
			pass
		try:
			string += "Delivery_address : " + (self.delivery_address if self.delivery_address != None else "None") + '\n'
		except AttributeError:
			pass
		try:
			string += "Billing_address : " + (self.billing_address if self.billing_address != None else  "None") + '\n'
		except AttributeError:
			pass
		return string

	def to_list(self):
		''' returns all attributes of the object as a list '''
		return [self.id, self.email, self.shop_address, self.delivery_address, self.billing_address, self.shop_name, self.person_name]
