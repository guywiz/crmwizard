# -*- coding: utf-8 -*-

import sys
import os
import datetime
from dateutil.parser import parse
import re
import json
from mail.mailbox import Mailbox
from doc_process.invoice import Invoice
from doc_process.date_manager import DateManager
from db.sqlite_db import ImpDatabaseInterface

'''
not sure whether we are using python 2.7 or python 3, I preferred making sure
the code would work in both settings
'''
if '2.7' in sys.version:
	import ConfigParser
	config = ConfigParser.ConfigParser()
else:
	import configparser
	config = configparser.ConfigParser()

class CRMWizard(object):
	'''
	The CRMWizard implements the controller part of the app.
	The data model part is implemented through modules
	dealing with all database transactions, email processing from which
	documents are borought into the system; the doc_process module then
	extracts useful information from these documents to feed the database.

	Still missing a module answering queries to feed the view part (dashboard)
	of the app.
	'''
	def __init__(self, config, date = None):
		super(CRMWizard, self).__init__()
		self.config = config
		self.config.read('crmwizard.ini')
		self.mailbox_path = self.config.get('mailbox', 'mailbox_path')
		self.client_base_document_dir = self.mailbox_path + 'data'
		self.db = ImpDatabaseInterface(config)
		self.dm = DateManager()
		self.last_access_date = date

	def run(self):
		'''
		This should be the main app routine associated with the index page of the application.
		When called the server should
		- send the index page, with a main menu
		- perform a data update (see the __data_update__ method)
		- (warn user that a data update is launched)

		The data update routine should be launched periodically whenever the app is running.
		'''
		return

	def __data_update__(self):
		'''
		This is a subroutine of the run routine. When called it triggers
		a data update, which will cascade into:
		-- a query on the mailbox to grab the most recent, unprocessed emails
		-- then process all extracted documents (attached files to the emails)
		-- update the database
		'''
		if self.last_access_date == None:
			self.last_access_date = self.db.get_mailbox_last_access_date()
		return self.last_access_date

		mailbox = Mailbox(self.config)
		doc_processor = Invoice(self.config)

		print('Getting messages from mailbox ', self.config.get('mailbox', 'user_id'))
		most_recent_date, messages = mailbox.get_messages_after(self.last_access_date)
		print('\t', 'Got', len(messages), 'messages')
		for m in messages:
			if not 'order confirmation' in mailbox.get_message_subject(m).lower():
				continue
			print('Getting attachements')
			print('\t', 'to message', m[u'id'])
			email = mailbox.__get_recipient__(m)
			subject = mailbox.get_message_subject(m)
			pattern = re.compile(r'(?P<subject_prefix>.*for order )(?P<purchase_number>\d*)(?P<subject_suffix>.*)')
			match = re.search(pattern, subject)
			purchase_number = match.group('purchase_number')

			# received date follows format: 9 Sep 2018 17:01:06 +0200
			date_received = self.dm.to_formatted_string(mailbox.get_received_date(m), origin='gmail', date_format='full')
			print('\t' + 'date received ', date_received)
			client_dir = '_'.join([str(purchase_number), date_received.replace(':', '_').replace('-', '_').replace('+', '_').replace(' ', '_')])
			mailbox.get_attachments(m, client_dir)
			dir_name = '/'.join([self.client_base_document_dir, client_dir])
			for doc_tuples in os.walk(dir_name):
				for doc in doc_tuples[2]:
					print('Looking at doc ', dir_name, doc)
					# only process pdf's for now, need to be refined
					if '.pdf' in doc:
						print('\t', 'Processing doc ', doc)
						filename = '/'.join([dir_name, doc])
						client, purchase = doc_processor.read(filename, date_received)
						if client != None:
							client.set_client_email(email)
							purchase.set_purchase_date_mail(date_received)
							print(client.get_client_id(), purchase.get_purchase_id())
							print(purchase.to_string())
							self.db.update_purchase(purchase)
							print('\t\t', '(DB) Updated purchase', purchase.get_purchase_id())
							self.db.update_client(client)
							print('\t\t', '(DB) Updated client', client.get_client_id())
							# return
		return most_recent_date, messages

	def __data_recollect__(self, date_after, date_before, sender='noreply@hkliving.nl'):
		'''
		This is a subroutine of the run routine. When called it triggers
		a data update, which will cascade into:
		-- a query on the mailbox to grab the most recent, unprocessed emails
		-- then process all extracted documents (attached files to the emails)
		-- update the database
		'''
		mailbox = Mailbox(self.config)
		doc_processor = Invoice(self.config)

		print('Getting messages from mailbox ', self.config.get('mailbox', 'user_id'))
		messages = mailbox.__get_messages__(date_after, date_before, 500, sender)
		print('\t + Got', len(messages), 'messages')
		full_messages = map(lambda m: mailbox.get_message(m[u'id']), messages)
		for m in full_messages:
			if not 'order confirmation' in mailbox.get_message_subject(m).lower():
				continue
			print('Getting attachements')
			print('\t' + 'to message', m[u'id'])
			email = mailbox.__get_recipient__(m)
			subject = mailbox.get_message_subject(m)
			pattern = re.compile(r'(?P<subject_prefix>.*for order )(?P<purchase_number>\d*)(?P<subject_suffix>.*)')
			match = re.search(pattern, subject)
			purchase_number = match.group('purchase_number')

			date_received = self.dm.to_formatted_string(mailbox.get_received_date(m), origin='gmail', date_format='full')
			print('\t' + 'date received ', date_received)
			client_dir = '_'.join([str(purchase_number), date_received.replace(':', '_').replace('-', '_').replace('+', '_').replace(' ', '_')])
			dir_name = '/'.join([self.client_base_document_dir, client_dir])
			mailbox.get_attachments(m, client_dir)
			if not os.path.exists(dir_name):
				os.makedirs(dir_name)
			message_file_name = ''.join([dir_name, '/', m[u'id'], '.json'])
			with open(message_file_name, 'w') as fout:
				json.dump(m, fout)
			for doc_tuples in os.walk(dir_name):
				for doc in doc_tuples[2]:
					# only process pdf's for now, need to be refined
					if '.pdf' in doc:
						filename = '/'.join([dir_name, doc])
						client, purchase = doc_processor.read(filename, date_received)
						if client != None:
							client.set_client_email(email)
							purchase.set_purchase_date_mail(date_received)
							self.db.update_purchase(purchase)
							self.db.update_client(client)
							# return
		return messages

if __name__ == '__main__':

	collect_all = False
	collect = False
	debug = True
	if collect_all:
		last_access_date = datetime.datetime.strptime('01-12-2018', '%d-%m-%Y')
		crm = CRMWizard(config, last_access_date)
		# most_recent_date, messages = crm.__data_update__()
		months = ['01', '02', '03' ,'05', '05', '06', '07', '08', '09', '10', '11', '12']
		years = ['2018', '2017', '2016']
		for year in years:
			print('GETTING MESSAGES FOR YEAR ', year)
			for i in range(len(months)-1):
				start_date = '/'.join([year, months[i], '01'])
				end_date = '/'.join([year, months[i+1], '01'])
				print('GETTING MESSAGES FOR PERIOD ', start_date, ' -- ', end_date)
				crm.__data_recollect__(start_date, end_date, sender='noreply@hkliving.nl')
	if collect:
		last_access_date = datetime.datetime.strptime('01-12-2018', '%d-%m-%Y')
		crm = CRMWizard(config, last_access_date)
		# messages = crm.__data_recollect__('2018/10/01', '2018/10/31', sender='noreply@hkliving.nl')
		messages = crm.__data_recollect__('2018/09/01', '2018/09/05', sender='noreply@hkliving.nl')
		# messages = crm.__data_recollect__('2018/08/01', '2018/09/01', sender='noreply@hkliving.nl')
		# messages = crm.__data_recollect__('2018/07/01', '2018/08/01', sender='noreply@hkliving.nl')
		# messages = crm.__data_recollect__('2018/06/01', '2018/07/01', sender='noreply@hkliving.nl')
	if debug:
		crm = CRMWizard(config, None)
		print(crm.__data_update__())
