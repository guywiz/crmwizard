# -*- coding: utf-8 -*-

from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file as oauth_file, client, tools
import base64
import json
import os
from doc_process.invoice import Invoice
from doc_process.date_manager import DateManager

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

class Mailbox(object):
	'''
	The Mailbox class offers methods to access a GMail account
	and extracts all messages. The main purpose is to get
	client information along with
	all (pdf) file attachments that are then further processed.

	The credentials.json file needs to be generated form the GMail account the app accesses.
	'''
	def __init__(self, config):
		# last_accessed_date=None
		super(Mailbox, self).__init__()
		self.mailbox_path = config.get('mailbox', 'mailbox_path')
		self.credential_file = config.get('mailbox', 'credential_file')
		self.token_file = config.get('mailbox', 'token_file')
		self.user_id = config.get('mailbox', 'user_id')
		jcredentials = json.load(open(self.mailbox_path + self.credential_file, 'rU'))

		store = oauth_file.Storage(self.mailbox_path + self.token_file)
		#store = oauth_file.Storage(self.token_file)
		creds = store.get()
		if not creds or creds.invalid:
			#flow = client.flow_from_clientsecrets('mail/cori_melancon_credentials.json', SCOPES)
			flow = client.flow_from_clientsecrets(self.mailbox_path + self.credential_file, SCOPES)
			#flow = client.flow_from_clientsecrets(self.credential_file, SCOPES)
			# flow = client.flow_from_clientsecrets('credentials_decosobredesign.json', SCOPES)
			# flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
			creds = tools.run_flow(flow, store)
		self.service = build('gmail', 'v1', http=creds.authorize(Http()))
		self.base_store_dir = self.mailbox_path + 'data'
		self.dm = DateManager()
		
	def get_message(self, msg_id):
		return self.service.users().messages().get(userId=self.user_id, id=msg_id).execute()

	def get_sender(self, message):
		'''
		parses a message and sends the content of the 'From' field (header part)
		usually structured as a two part string: First name Last name <login@domain>
		'''
		for h in message[u'payload'][u'headers']:
			if h[u'name'] == u'From':
				return h[u'value']
		return None

	def __get_recipient__(self, message):
		'''
		This method makes an assumption that the message is sent to a client,
		we need to identify which client it is so the attachment file(s)
		can be stored in a dedicated folder.
		'''
		for h in message[u'payload'][u'headers']:
			if h[u'name'] == u'To':
				return h[u'value']
		return None

	def get_message_subject(self, message):
		for h in message[u'payload'][u'headers']:
			if h[u'name'] == u'Subject':
				return h[u'value']
		return None

	def get_received_date(self, message):
		'''
		returns the sent date as stored in the message header (as opposed to the message internal date)
		this value shall be used for internal purposes only (not 100% reliable, but for
		computational purpose, for example)
		'''
		for h in message[u'payload'][u'headers']:
			if h[u'name'] == 'Date':
				date_string = h[u'value']
				return self.dm.to_formatted_string(date_string)
		return None

	def download_attachment_file(self, msg_id, att_id, store_dir, file_attachment_name):
		print('********** downloading attachment(s), storing into directory ', store_dir)
		if not os.path.exists(store_dir):
			os.makedirs(store_dir)
		path = '/'.join([store_dir, file_attachment_name])
		with open(path, 'wb') as f:
			attachPart = self.service.users().messages().attachments().get(userId=self.user_id, messageId=msg_id, id=att_id).execute()
			data = base64.urlsafe_b64decode(attachPart[u'data'].encode('UTF-8'))
			f.write(data)

	def get_attachments(self, message, store_dir):
		print('Getting attachments for message ', message[u'id'])
		msg_id = message[u'id']
		client_dir = '/'.join([self.base_store_dir, store_dir])
		print('Client directory: ', client_dir)

		for part in message[u'payload'][u'parts']:
			print('   Looking into parts')
			file_attachment_name = part[u'filename']
			file_attachment_type = part[u'mimeType']

			if file_attachment_type == u'application/pdf':
				print('      Looking into parts (pdf direct)')
				size = part[u'body'][u'size']
				if size != 0 and file_attachment_name != '':
					att_id = part[u'body'][u'attachmentId']
					if (att_id != ''):
						self.download_attachment_file(msg_id, att_id, client_dir, file_attachment_name)

			if file_attachment_type == u'multipart/mixed':
				print('      Looking into parts (mixed)')
				for subpart in part[u'parts']:
					print('      Looking into SUBparts')
					subfile_attachment_type = subpart[u'mimeType']

					if subfile_attachment_type == u'application/pdf':
						subfile_attachment_name = subpart[u'filename']
						subsize = subpart[u'body'][u'size']
						if subsize != 0 and subfile_attachment_name != '':
							att_id = subpart[u'body'][u'attachmentId']
							print('Attachment id : ', att_id)
							if (att_id != ''):
								self.download_attachment_file(msg_id, att_id, client_dir, subfile_attachment_name)

					if subfile_attachment_type == u'application/octet-stream':
						is_pdf = False
						for h in subpart[u'headers']:
							if h[u'name'] == u'Content-Type' and 'application/pdf' in h[u'value']:
								is_pdf = True
						if is_pdf:
							subfile_attachment_name = subpart[u'filename']
							subsize = subpart[u'body'][u'size']
							if subsize != 0 and subfile_attachment_name != '':
								att_id = subpart[u'body'][u'attachmentId']
								print('Attachment id : ', att_id)
								if (att_id != ''):
									self.download_attachment_file(msg_id, att_id, client_dir, subfile_attachment_name)

	def __get_messages__(self, date_after=None, date_before=None, how_many = 500, sender='noreply@hkliving.nl'):
		'''
		gets a given number of messages, presumably the most recent ones
		does not sort them in any manner, this is done in subsequent functions using
		the returned list
		'''
		get_query = q='from:' + sender
		if date_after != None:
			get_query += ' + after:' + date_after
		if date_before != None:
			get_query += ' + before:' + date_before
		messages = self.service.users().messages().list(userId=self.user_id,maxResults = how_many,q=get_query).execute()
		try:
			return messages[u'messages']
		except KeyError:
			# happens if message list is empty, and contains only headers
			return []

'''

KEEP THIS CODE AS IT CONTAINS EXAMPLE USAGE OF THE GMAIL API

def main():

	# Call the Gmail API
	results = service.users().labels().list(userId='me').execute()
	labels = results.get('labels', [])
	if not labels:
		print('No labels found.')
	else:
		pass
		# print('Labels:', len(labels), 'labels')

		for label in labels:
			print(label['name'])

	#threads = service.users().threads().list(userId='me').execute()
	#one_thread = service.users().threads().get(userId='me', id='164fac29cb70fee5').execute()
	#print(one_thread)
	messages = service.users().messages().list(userId='me',maxResults = 500).execute()
	#one_message = service.users().messages().get(userId='me', id='164fac2d2762e991').execute()
	#print(one_message)
	for m in messages['messages']:
		#print(m['id'], m['threadId'])
		one_message = service.users().messages().get(userId='me', id=m['id']).execute()

		d = datetime.datetime.fromtimestamp(int(one_message['internalDate'])/1000).strftime('%Y-%m-%d %H:%M:%S')

		try:
			print(m['id'], ' - ', d, m['threadId'], m['sizeEstimate'])
		except KeyError:
			pass

		snippet = one_message['snippet']
		headers = one_message['payload']['headers']
		for key_value_pair in headers:
			if key_value_pair['name'] =='Subject':
				subject = key_value_pair['value'].encode('utf8')
			if key_value_pair['name'] =='From':
				sender = key_value_pair['value']
			if key_value_pair['name'] =='Date':
				d = key_value_pair['value']
		if 'enprovence' in sender:
			try:
				print(m['id'], d, subject)
			except UnicodeEncodeError:
				print(m['id'], d)

		if 'Europcar' in subject and 'europcar' in sender:
			user_id='me'
			msg_id=m['id']
			print('\t' + msg_id)
			store_dir = '/Users/melancon/Documents/Dev/crmwizard/mail/'
			message = service.users().messages().get(userId=user_id, id=msg_id).execute()
			for part in message['payload']['parts']:
				newvar = part['body']
				print(part['body'])
				if 'attachmentId' in newvar:
					att_id = newvar['attachmentId']
					att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=att_id).execute()
					data = att['data']
					file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
					print(part['filename'])
					path = ''.join([store_dir, part['filename']])
					f = open(path, 'w')
					f.write(file_data)
					f.close()

			print(sender)
			print(d)
			print(subject)
			print(one_message['payload']['mimeType'])
			print(one_message['payload']['filename'])
			for part in one_message['payload']['parts']:
				print(part)
				print('****************')
				if part['filename']:
					print('part[filename]', part['filename'])
					file_data = base64.urlsafe_b64decode(part['body']['data'].encode('UTF-8'))
					path = ''.join([store_dir, part['filename']])
					#path = ''.join(['./', part['filename']])
					#f = open('/Users/melancon/Documents/Dev/crmwizard/' + part['filename'], 'w')
					f = open(path, 'w')
					print('Opened file')
					f.write(file_data)
					print('Wrote file')
					f.close()

		d = datetime.datetime.fromtimestamp(1284101485).strftime('%Y-%m-%d %H:%M:%S')
		'name': 'From'
		'name': 'Subject'
		'name': 'Date'
		print('\t', d)
		print('\t', headers)

	#print(messages)
'''

if __name__ == '__main__':
	import ConfigParser
	config = ConfigParser.ConfigParser()
	config.read('crmwizard.ini')

	mb = Mailbox(config)
	'''
	messages = mb.__get_messages__(date_after='2018/08/31', date_before='2018/09/04')
	print('Nb messages: ', len(messages))
	for m in messages:
		m_id = m[u'id']
		message = mb.get_message(m_id)
		print('\t' + 'From:', mb.get_sender(message))
		print('\t' + 'To:', mb.__get_recipient__(message))
		print('\t' + 'Received:', mb.get_received_date(message))
		print('\t' + 'Subject:', mb.get_message_subject(message))
		print()
	'''
		


