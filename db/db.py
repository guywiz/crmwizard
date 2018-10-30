# -*- coding: utf-8 -*-

import abc

class DatabaseInterface():
	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def get_client(self, client_id):
		''' returns Client object '''
		return

	@abc.abstractmethod
	def update_client(self, client_object):
		''' updates or creates client in database '''
		return

	@abc.abstractmethod
	def get_purchase(self, order_id):
		''' returns Order object '''
		return

	@abc.abstractmethod
	def update_purchase(self, order_object):
		''' updates or creates order in database '''
		return

	@abc.abstractmethod
	def get_article(self, article_id):
		''' returns Article object '''
		return

	@abc.abstractmethod
	def update_article(self, article_object):
		''' updates or creates article in database '''
		return

	@abc.abstractmethod
	def do_client_exists(self, client_object):
		''' returns True if client_object is already in the db '''
		''' False if not '''
		return

	@abc.abstractmethod
	def do_purchase_exists(self, purchase_object):
		''' returns True if purchase_object is already in the db '''
		''' False if not '''
		return

	@abc.abstractmethod
	def do_article_exists(self, article_object):
		''' returns True if article_object is already in the db '''
		''' False if not '''
		return

	@abc.abstractmethod
	def close(self):
		''' close the connection with the db '''
		return
