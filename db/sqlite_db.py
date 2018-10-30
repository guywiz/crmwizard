# -*- coding: utf-8 -*-

import sqlite3
import datetime

from client import Client
from article import Article
from purchase import Purchase
from db import DatabaseInterface

class ImpDatabaseInterface(DatabaseInterface):
	def __init__(self, config):
		self.config = config
		self.db = sqlite3.connect(self.config.get('database', 'filename'))
		self.db.text_factory = str
		self.cursor = self.db.cursor()

	def get_mailbox_last_access_date(self):
		'''
		returns the date of most recent accessed and processed email

		fake date for now, until db is fixed
		'''
		try:
			self.cursor.execute("SELECT mail_date FROM Purchase ORDER BY mail_date DESC")
			date = self.cursor.fetchall()[0]
			date_format = '%Y-%m-%d %H:%M:%S'

			today = datetime.datetime.today()
			return today + datetime.timedelta(-5)

			return datetime.datetime.strptime(date[0].split('+')[0], date_format)
		except IndexError as e:
			# this error should not occur but only if the db is empty ...
			print("Error on get_mailbox_last_access_date() : " + str(e))
			today = datetime.datetime.today()
			print today + datetime.timedelta(-5)
			return today + datetime.timedelta(-5)

	def get_client(self, client_id):
		''' returns Client object '''
		try:
			self.cursor.execute("SELECT * FROM Client WHERE id = " + str(client_id))
			info_client = self.cursor.fetchall()[0]
			client = Client(info_client[0])
			client.set_client_email(info_client[1]).set_client_shop_address(info_client[2]).set_client_delivery_address(info_client[3]).set_client_billing_address(info_client[4]).set_client_shop_name(info_client[5]).set_client_person_name(info_client[6])
			return client
		except Exception as e:
			print("Error on get_client(", client_id, ") : ", str(e))
			return

	def get_client_from_mail(self, email):
		'''
		gets a client id from (one of) his/her email address
		'''
		try:
			self.cursor.execute("SELECT * FROM Client WHERE mail = ?", (email,))
			info_client = self.cursor.fetchall()[0]
			client = Client(info_client[0])
			client.set_client_email(info_client[1]).set_client_shop_address(info_client[2]).set_client_delivery_address(info_client[3]).set_client_billing_address(info_client[4]).set_client_shop_name(info_client[5]).set_client_person_name(info_client[6])
			return client
		except IndexError as e:
			# this error occurs when client is unknown and thus does not exist in the DB
			print("Client does not exist (yet) " + email + ") : " + str(e))
			return None

	def update_client(self, client_object):
		''' updates or creates client in database '''
		values = client_object.to_list()
		if (self.do_client_exists(client_object)):
			values.append(client_object.get_client_id())
			self.__update__("Client", values)
		else:
			self.insert("Client", values)
		return self

	def get_purchase(self, order_id, date_mail):
		''' returns Order object '''
		try:
			query = "SELECT * FROM Purchase WHERE id = ? AND mail_date = ?"
			values = (str(order_id), date_mail)
			self.cursor.execute(query, values)
			info_purchase = self.cursor.fetchall()[0]
		except Exception as e:
			print("Error on get_purchase(" +  str(order_id) + ") : ", str(e))
			return

		try:
			order = Purchase(info_purchase[0])
			order.set_purchase_date_order(info_purchase[1]).set_purchase_date_mail(info_purchase[2])
			order.set_purchase_client(info_purchase[3]).set_purchase_reference(info_purchase[4])

			self.cursor.execute("SELECT * FROM PurchaseList WHERE order_id = " + str(order_id))
			info_articles = self.cursor.fetchall()

			for article_data in info_articles:
				article_object = self.get_article(article_data[1])
				order.add_articles([(article_object, article_data[2], article_data[3])])

			return order
		except Exception as e:
			print("Error on get_purchase(" +  str(order_id) + ") : ", str(e))
			return

	def get_all_purchase_reference(self):
		try:
			self.cursor.execute("SELECT reference FROM 'Purchase'")
			purchase_references = set([purchase[0] for purchase in self.cursor.fetchall()])
		except Exception as e:
			print("Error on get_purchase(" +  str(order_id) + ") : ", str(e))
			return

	def update_purchase(self, purchase_object):
		''' updates or creates order in database '''
		values = purchase_object.to_list()[:-1][1:]
		if self.do_purchase_exists(purchase_object):
			values.append(purchase_object.get_purchase_id())
			self.__update__("Purchase", values)
			for article_key in purchase_object.article_map.keys():			
				article_object, quantity, discount = purchase_object.article_map[article_key]
				self.update_article(article_object)
				values = [quantity, discount]
				if self.do_purchaselist_exists(purchase_object.get_purchase_id(), article_object.get_article_id()):
					values.append(purchase_object.get_purchase_id())
					values.append(article_object.get_article_id())
					self.__update__("PurchaseList", values)
				else:
					values.insert(0, article_object.get_article_id())
					values.insert(0, purchase_object.get_purchase_id())
					self.insert("PurchaseList", values)
		else:
			self.insert("Purchase", purchase_object.to_list()[:-1])
			for article_key in purchase_object.article_map.keys():			
				article_object, quantity, discount = purchase_object.article_map[article_key]
				self.update_article(article_object)
				values = [purchase_object.get_purchase_id(), article_object.get_article_id(), quantity, discount]
				self.insert("PurchaseList", values)

		return self

	def get_article(self, article_id):
		''' returns Article object '''
		try:
			query = "SELECT * FROM Article WHERE id = '" + str(article_id) + "'"
			self.cursor.execute(query)
			info_article = self.cursor.fetchall()[0]
			article = Article(info_article[0])
			article.set_article_description(info_article[1]).set_article_unit_price(info_article[2])
			return article
		except Exception as e:
			# print("Article does not exist (yet) : " + str(e), 'Query : ', query)
			return None

	def update_article(self, article_object):
		'''
		updates or creates article in database
		note that there is no obvious ways to update article
		if unit prices differs between two instances ...
		so we simply do not deal with it
		'''

		article_id = article_object.get_article_id()
		article_description = article_object.get_article_description()
		article_unit_price = article_object.get_article_unit_price()
		existing_article = self.do_article_exists(article_object)
		if existing_article == None:
			values = [article_id, article_description, article_unit_price]
			self.insert("Article", values)
		else:
			existing_description = existing_article.get_article_description()
			existing_unit_price = existing_article.get_article_unit_price()
			if article_description != existing_description:
				if article_unit_price != existing_unit_price:
					print('Problem article ', article_id, ' has incoherent prices between two purchase orders')
				values = [article_description, article_unit_price, article_id]
				self.__update__("Article", values)
		return self

	def close(self):
		''' close the connection with the db '''
		self.db.close()
		self.cursor = None
		return self

	def insert(self, table, values):
		''' insert in db "values" inside "table" '''
		query = "INSERT INTO "
		if (table.lower() == "client"):
			query += "Client(id, mail, adrPHY, adrLIV, adrBILL, nameSHOP, namePERS) VALUES (?,?,?,?,?,?,?)"
		elif (table.lower() == "purchase"):
			query += "Purchase(id, order_date, mail_date, client, reference) VALUES (?,?,?,?,?)"
		elif (table.lower() == "article"):
			query += "Article(id, description, price) VALUES (?,?,?)"
		elif (table.lower() == 'purchaselist'):
			query += "PurchaseList(order_id, article_id, quantity, discount) VALUES (?,?,?,?)"

		try:
			self.cursor.execute(query, tuple(values))
			self.db.commit()
			return self
		except Exception as e:
			print("Cannot insert: " + query, "Table given is" + table)
			print("Error: " + str(e) + ". Values : \n", values)

	def __update__(self, table, values):
		''' update in db "values" inside "table" '''
		query = "UPDATE " + table + " SET "
		if (table.lower() == "client"):
			query += "id = ?, mail = ?, adrPHY = ?, adrLIV = ?, adrBILL = ?, nameSHOP = ?, namePERS = ?"
		elif (table.lower() == "purchase"):
			query += "order_date = ?, client = ?, reference = ?"
		elif (table.lower() == "article"):
			query += "description = ?, price = ?"
		elif (table.lower() == "purchaselist"):
			# query += "order_id = ?, article_id = ?, quantity = ?, discount = ?"
			query += "quantity = ?, discount = ?"

		if (table.lower() == "purchaselist"):
			query += " WHERE order_id = ? AND article_id = ?"
		elif (table.lower() == "purchase"):
			query += " WHERE id = ? AND mail_date = ?"
		else:
			query += " WHERE id = ?"
		try:
			self.cursor.execute(query, tuple(values))
			self.db.commit()
			return self
		except Exception as e:
			print("Cannot update: " + query, values, "Table given is " + table)
			print("Error: " + str(e) + ". Values : \n", values)

	def do_client_exists(self, client_object):
		''' returns True if client_object is already in the db '''
		''' False if not '''
		try:
			self.cursor.execute("SELECT * FROM Client WHERE id = " + str(client_object.get_client_id()))
			rows = self.cursor.fetchall()
			return len(rows) > 0
		except Exception as e:
			print("Error on do_client_exists() : " + str(e))

	def do_purchase_exists(self, purchase_object):
		''' returns True if purchase_object is already in the db '''
		''' False if not '''
		try:
			query = "SELECT * FROM Purchase WHERE id = ? and mail_date = ?"
			values = (purchase_object.get_purchase_id(), purchase_object.get_purchase_date_mail())
			self.cursor.execute(query, values)
			rows = self.cursor.fetchall()
			return len(rows) > 0
		except Exception as e:
			print("Purchase does not exist (yet) : " + str(e))

	def do_purchaselist_exists(self, purchase_id, article_id):
		''' returns True if purchase_list is already in the db '''
		''' False if not '''
		try:
			query = "SELECT * FROM PurchaseList WHERE order_id = ? and article_id = ?"
			values = (purchase_id, article_id)
			self.cursor.execute(query, values)
			rows = self.cursor.fetchall()
			return len(rows) > 0
		except Exception as e:
			print("Error on do_purchase_exists() : " + str(e))

	def do_article_exists(self, article_object):
		''' returns article object if it already exists in the db '''
		''' None if not '''
		self.cursor.execute("SELECT * FROM Article WHERE id = ?", (article_object.get_article_id(),) )
		rows = self.cursor.fetchall()
		if len(rows) > 0:
			item_list = rows[0]
			article_id = item_list[0]
			article = Article(article_id)
			article.hydrate(item_list)
			return article
		return None

if __name__ == '__main__':

	import ConfigParser
	config = ConfigParser.ConfigParser()
	config.read('crmwizard.ini')
	db = ImpDatabaseInterface(config)

	db.cursor.execute("SELECT reference FROM 'Purchase'")
	purchase_references = set([purchase[0] for purchase in db.cursor.fetchall()])
	print(purchase_references)
	'''
	# 	test client insert, alternatively tests client update
	client1 = Client(1)
	client1.set_client_email('abc1@abc.fr')
	client1.set_client_person_name('M. ABC1')
	client1.set_client_shop_name('ABC Road, ABC Town, ABC Country')
	client1.set_client_billing_address('ABC Road, ABC Town, ABC Country')
	client1.set_client_delivery_address('ABC Road, ABC Town, ABC Country')
	client1.set_client_shop_address('ABC Road, ABC Town, ABC Country')
	db.update_client(client1)
	client_id = client1.get_client_id()
	ext_client1 = db.get_client(client_id)
	print(ext_client1.to_string())

	article1 = Article('AOA9962')
	article1.set_article_unit_price(8.91)
	article1.set_article_description('bamboo letter rack')
	db.update_article(article1)
	article_id = article1.get_article_id()
	ext_article1 = db.get_article(article_id)
	print(ext_article1.to_string())

	article2 = Article('AWD8028')
	article2.set_article_unit_price(29.02)
	article2.set_article_description('wall chart: XXL jungle')
	db.update_article(article2)
	article_id = article2.get_article_id()
	print(article_id)
	ext_article2 = db.get_article(article_id)
	print(ext_article2.to_string())

	article3 = Article('MOU5002')
	article3.set_article_unit_price(44.20)
	article3.set_article_description('bohemian hammock')
	db.update_article(article3)
	article_id = article3.get_article_id()
	print(article_id)
	ext_article3 = db.get_article(article_id)
	print(ext_article3.to_string())

	purchase = Purchase(1001)
	purchase.set_purchase_client(client1.get_client_id())
	purchase.set_purchase_date_order(datetime.datetime.today())
	purchase.set_purchase_date_mail(datetime.datetime.today())
	purchase.set_purchase_reference('App4Sales orde')
	purchase.set_purchase_state('Init')
	print(purchase.to_list())
	print('')
	db.update_purchase(purchase)
	ext_purchase = db.get_purchase(purchase.get_purchase_id())
	print(purchase.to_list())
	print('')

	purchase.add_articles([(article1, 5, 10), (article2, 10, 15)])
	print(purchase.to_list())
	print('')
	db.update_purchase(purchase)
	ext_purchase = db.get_purchase(purchase.get_purchase_id())
	print(purchase.to_list())
	print('')

	purchase.add_articles([(article1, 3, 9), (article3, 2, 5)])
	print(purchase.to_list())
	print('')
	db.update_purchase(purchase)
	ext_purchase = db.get_purchase(purchase.get_purchase_id())
	print(purchase.to_list())
	print('')
	'''
