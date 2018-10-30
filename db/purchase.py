# -*- coding: utf-8 -*-

class Purchase(object):
	"""docstring for Purchase"""
	def __init__(self, purchase_id, mail_date):
		super(Purchase, self).__init__()
		self.id = purchase_id
		self.client_id = None
		self.date_order = None
		self.date_mail  = None
		self.reference = None
		self.article_map = {} # indexed with article primary key, maps to article objects
		self.article_list = []

	def get_purchase_id(self):
		''' returns article id '''
		return self.id

	def get_purchase_client(self):
		''' returns client id '''
		return self.client_id

	def set_purchase_client(self, client_id):
		''' sets client id '''
		self.client_id = client_id
		return self

	def get_purchase_date_order(self):
		''' returns purchase's date (found in pdf) '''
		return self.date_order

	def set_purchase_date_order(self, date):
		''' sets purchase's date (found in pdf) '''
		self.date_order = date
		return self

	def get_purchase_date_mail(self):
		''' returns purchase's date (found in email) '''
		return self.date_mail

	# ##### we may suspect the get_received_date method is useless,
	# ##### somehow replaced by DateManager and called nowhere really ...
	def get_received_date(self, message):
		'''
		returns the sent date as stored in the message header (as opposed to the message internal date)
		this value shall be used for internal purposes only (not 100% reliable, but for
		computational purpose, for example)
		'''
		date_string = self.date_mail
		date_only = date_string.split('+')[0]
		offset = ''.join(date_string.split('+')[1].split(':'))
		return date_only + '+' + offset

	def set_purchase_date_mail(self, date):
		''' sets purchase's date (found in email) '''
		self.date_mail = date
		return self

	def get_purchase_reference(self):
		''' returns purchase's reference '''
		return self.reference

	def set_purchase_reference(self, reference):
		''' sets purchase's reference '''
		self.reference = reference
		return self

	def get_article_list(self):
		''' returns list of article objects '''
		if hasattr(self, 'article_list'):
			return self.article_list
		else:
			return []

	def get_article_map(self):
		''' returns list of article objects '''
		if hasattr(self, 'article_map'):
			return self.article_map
		else:
			return {}

	def add_article(self, article_object, quantity, discount):
		'''
		add articles to purchase
		a tuple is a triple (article_object, quantity, discount_rate)
		inserts tuples into (existing) list of tuples
		'''
		try:
			article_key = article_object.get_article_id()
			article_in = self.article_map[article_key][0]
			quantity_in = self.article_map[article_key][1]
			discount_in = self.article_map[article_key][2]
			# need to manage case where discount_in and discount_more disagree
			# how likely is this to happen?
			self.article_map[article_key] = [article_in, quantity_in + quantity, discount_in]
		except KeyError:
			self.article_map[article_key] = [article_object, quantity, discount]
		return self

	def add_articles(self, article_tuples):
		'''
		add articles to purchase
		a tuple is a triple (article_object, quantity, discount_rate)
		inserts tuples into (existing) list of tuples
		'''
		for article_object, quantity, discount in article_tuples:
			self.add_article(article_object, quantity, discount)

	def to_string(self):
		''' returns a formatted string of all attributes '''

		string  = str(self.id) + ', from ' + str(self.client_id) + '\n'
		for article_key in self.article_map:
			art = self.article_map[article_key][0]
			qtty = self.article_map[article_key][1]
			discount = self.article_map[article_key][2]
			string += str(art.get_article_id()) + ' | Qtty: ' + str(qtty) + 'Discount: ' + str(discount) + '\n'
		return string

	def to_list(self):
		''' returns all attributes of the object as a list '''
		return [self.id, self.date_order, self.date_mail, self.client_id, self.reference, self.article_map]
