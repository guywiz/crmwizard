# -*- coding: utf-8 -*-

class Article(object):
	"""docstring for Article"""
	def __init__(self, article_id):
		super(Article, self).__init__()
		self.id = article_id
		self.price = None
		self.description = None

	def hydrate(self, db_item_list):
		article_description = db_item_list[1]
		unit_price = db_item_list[2]
		self.set_article_description(article_description)
		self.set_article_unit_price(unit_price)
		return self

	def get_article_id(self):
		''' returns article id '''
		return self.id

	def get_article_unit_price(self):
		''' returns article unit price '''
		return self.price

	def set_article_unit_price(self, price):
		''' sets article unit price '''
		self.price = price
		return self

	def get_article_description(self):
		''' returns article description text '''
		return self.description

	def set_article_description(self, description):
		''' sets article description text '''
		self.description = description
		return self

	def to_string(self):
		''' returns a formatted string of all attributes '''
		try:
			string  = str(self.id) + '\n'
			string += "Price : " + (str(self.price) if self.price != None else "None") + '\n'
			string += "Description : " + (self.description if self.description != None else "None") + '\n'
			return string
		except AttributeError:
			pass

	def to_list(self):
		''' returns all attributes of the object as a list '''
		return [self.id, self.description, self.price]
