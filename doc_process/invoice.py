# -*- coding: utf-8 -*-

import subprocess
import re
from db.client import Client
from db.article import Article
from db.purchase import Purchase
from db.sqlite_db import ImpDatabaseInterface
from doc_process.date_manager import DateManager

class Invoice(object):
	"""Processes a single invoice docuemnt"""
	def __init__(self, config):
		super(Invoice, self).__init__()
		self.path = config.get('mailbox', 'mailbox_path') + 'data/'
		self.db = ImpDatabaseInterface(config)
		self.dm = DateManager()

	def read(self, filename, mail_date):
		'''
		reads pdf and organizes content into
		several elements (client, purchase, etc.)
		'''
		output_doc = filename[0:-4] + '.txt'
		cmd = ['gs', '-dBATCH', '-dNOPAUSE', '-sDEVICE=txtwrite', '-sOutputFile=' + output_doc, filename]
		subprocess.call(cmd)
		with open(output_doc, 'rU') as fp:
			return self.process_txt(fp, mail_date)

	def longest_common_substring(self, s1, s2):
		m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
		longest, x_longest = 0, 0
		for x in xrange(1, 1 + len(s1)):
			for y in xrange(1, 1 + len(s2)):
				if s1[x - 1] == s2[y - 1]:
					m[x][y] = m[x - 1][y - 1] + 1
					if m[x][y] > longest:
						longest = m[x][y]
						x_longest = x
				else:
					m[x][y] = 0
		return x_longest - longest, x_longest, s1[x_longest - longest: x_longest]

	def longest_common_suffix(self, s1, s2):
		# challenge is to deal with unknown non common prefixes and variable space separation between words in s2
		s22 = s2.replace('  ', ' ')
		# normalize space sep between words
		while s22 != s2:
			s2 = s22
			s22 = s22.replace('  ', ' ')
		# delete spaces between words
		s11 = ''.join(s1.split(' '))
		s22 = ''.join(s2.split(' '))
		# find (index of) longest common suffixes
		i = len(s11) - 1
		j = len(s22) - 1
		while i > 0 and j > 0 and s11[i] == s22[j]:
			i -= 1
			j -= 1
		# compute (catenated) prefixes
		spref1 = s11[:(i+1)]
		spref2 = s22[:(j+1)]

		# get that substring in s1 that corresponds to that catenated spref1
		pref1 = ''
		i = 0
		j = 0
		while i < len(spref1):
			pref1 += s1[j]
			if spref1[i] == s1[j]:
				i += 1
				j += 1
			elif s1[j] == ' ':
				j += 1

		# get that substring in s2 that corresponds to that catenated spref2
		pref2 = ''
		i = 0
		j = 0
		while i < len(spref2):
			pref2 += s2[j]
			if spref2[i] == s2[j]:
				i += 1
				j += 1
			elif s2[j] == ' ':
				j += 1

		suff1 = s1[len(pref1):].strip()
		suff2 = s2[len(pref2):].strip()
		return pref1, suff1, pref2, suff2

	def __extract_purchase_ref_article_description__(self, ref_desc, article_id):
		article = self.db.get_article(article_id)
		if article == None:
			# we have no way of deducing the purchase ref field from the article desc
			# a few rules of thumb are applied, but if no result is found
			# we store the whole ref_desc string as article description
			# and store an empty string as purchase ref ...
			pattern = re.compile(r'(?P<purchase_reference>HKL-\d\d\d)(?P<description>.*)')
			match = re.search(pattern, ref_desc)
			if match != None:
				purchase_reference = match.group('purchase_reference')
				description = match.group('description').strip()
				return purchase_reference, description
			else:
				pattern = re.compile(r'(?P<purchase_reference>App4Sales orde)(?P<description>.*)')
				match = re.search(pattern, ref_desc)
				if match != None:
					purchase_reference = match.group('purchase_reference')
					description = match.group('description').strip()
					return purchase_reference, description
				else:
					pattern = re.compile(r'(?P<purchase_reference>Bestel.: \d\d\d\d\d)(?P<description>.*)')
					match = re.search(pattern, ref_desc)
					if match != None:
						purchase_reference = match.group('purchase_reference')
						description = match.group('description').strip()
						return purchase_reference, description
					else:
						pattern = re.compile(r'(?P<purchase_reference>paris fair \d\d\d)(?P<description>.*)')
						match = re.search(pattern, ref_desc.lower())
						if match != None:
							purchase_reference = match.group('purchase_reference')
							description = match.group('description').strip()
							return purchase_reference, description
						else:
							pattern = re.compile(r'(?P<purchase_reference>fair paris \d\d\d)(?P<description>.*)')
							match = re.search(pattern, ref_desc.lower())
							if match != None:
								purchase_reference = match.group('purchase_reference')
								description = match.group('description').strip()
								return purchase_reference, description
							else:
								pattern = re.compile(r'(?P<purchase_reference>ws\d\d\d\d\d\d\d\d\d)(?P<description>.*)')
								match = re.search(pattern, ref_desc.lower())
								if match != None:
									purchase_reference = match.group('purchase_reference')
									description = match.group('description').strip()
									return purchase_reference, description
			purchase_reference = ''
			description = ref_desc
			return purchase_reference, description
		if article != None:
			description = article.get_article_description()
			i, j, lcsubstring = self.longest_common_substring(ref_desc, description)
			new_ref_pref = ref_desc[:i]
			new_description = ref_desc[i:j]
			new_suffix = ref_desc[j:]
			k = description.index(lcsubstring)
			old_ref_pref = description[:k]
			old_description = description[k:k+len(lcsubstring)]
			old_suffix = description[k+len(lcsubstring):]
			if k == 0:
				purchase_reference = new_ref_pref
				# is already stored article description ok
				if len(old_suffix) > 0:
					# no need to update article description if no trailing suffix
					description = description[:len(description)-len(old_suffix)]

			else:
				# already stored article description is prefixed with previous purchase ref
				purchase_reference = new_ref_pref
				description = new_description

		return purchase_reference, description

	def __extract_prices__(self, price_string):
		price_string = ''.join(price_string.split(' '))
		price_string = price_string.replace('.', '')
		price_string = price_string.replace(',', '.')
		pattern = re.compile(r'(?P<quantity_unit_price>\d*.\d\d)(?P<discount_net_price>\d*.\d\d)(?P<net_amount>\d*.\d\d)')
		match = re.search(pattern, price_string)
		net_amount = float(match.group('net_amount'))
		# we assume discount equals 0
		discount = 0
		net_price = float(match.group('discount_net_price')[1:])
		unit_price = net_price
		try:
			quantity = int(net_amount / net_price)
		except ZeroDivisionError:
			# get quantity knowing unit price is 0,00
			# this happens when catalogs are shipped with order, for instance
			quantity = -1
			pass
		return unit_price, discount, net_price, quantity, net_amount

	def __client_from_header__(self, file_pointer):
		'''
		reads the top part of a text document (obtained from a pdf document)
		containing client information (id, addresses, etc.)
		the page is then scanned until we hit the article list
		'''
		# find then process client id line
		line = file_pointer.readline()
		while 'Customer No.' not in line:
			line = file_pointer.readline()
		# try grabbing client id number
		try:
			client_id = int(line.split(':')[1].strip())
		except ValueError:
			print('Value Error when reading customer no field')
			return line, None
		# instantiate client
		client = Client(client_id)

		# find delivery and billing addresses
		line = file_pointer.readline()
		while 'Ordered by' not in line:
			line = file_pointer.readline()

		line = file_pointer.readline()
		all_fields = []
		while 'Delivery adress' not in line:
			all_fields.append(line.strip())
			line = file_pointer.readline()

		# process lines to capture delivery and billing address
		align_pos = line.index('B')

		all_fields_delivery = []
		all_fields_billing = []
		line = file_pointer.readline()
		while 'Order' not in line:
			all_fields_delivery.append(line[:align_pos].strip())
			all_fields_billing.append(line[align_pos:].strip())
			line = file_pointer.readline()
		# process all_fields
		# discard empty lines)
		all_fields = filter(lambda x: x != '', all_fields)
		all_fields_delivery = filter(lambda x: x != '', all_fields_delivery)
		all_fields_billing = filter(lambda x: x != '', all_fields_billing)
		client.set_client_shop_name(all_fields[0])
		client.set_client_person_name(all_fields[1])
		client.set_client_shop_address([all_fields[0]] + all_fields[2:])
		client.set_client_delivery_address(all_fields_delivery)
		client.set_client_billing_address(all_fields_billing)

		# send found client to db, update if necessary
		return line, client

	def __contains_date__(self, line):
		pattern = re.compile(r'\d\d-\d\d-\d\d')
		match = pattern.search(line)
		return match != None

	def __chunk_line__(self, line):
		# VAA1085S71044 09-10-18 1e orderlab lamp chartreuse (switch)09-10-18113,37013,3716,18
		pattern = re.compile(r'(?P<article_id>.{7})(?P<fill1>.*)(?P<order_id>\d{5})(?P<fill2>.*)(?P<date_order>\d\d-\d\d-\d\d)(?P<ref_desc>.*)(?P<stock_date>\d\d-\d\d-\d\d)(?P<prices_quantity_discount>.*)')
		match = re.search(pattern, line.strip())
		if match != None:
			article_id = match.group('article_id')
			order_id = match.group('order_id')
			date_order = match.group('date_order')
			ref_desc = match.group('ref_desc')
			stock_date = match.group('stock_date')
			prices_quantity_discount = match.group('prices_quantity_discount')
			return article_id, order_id, date_order, ref_desc, stock_date, prices_quantity_discount

	def __update_state__(self, state, line):
		'''
		Given the state the processing machine is,
		and given a new line that has been read in,
		determine wat state the machine migrates to
		(in two words, this method implements a state machine)
		'''
		new_state = ''
		if 'Total' in line and 'quantity' in line:
			new_state = 'end_doc'
		if state == 'start':
			if 'Article' in line:
				new_state = 'heading_to_new_article'
			elif 'Total' in line and 'quantity' in line:
				new_state = 'end_doc'
			else:
				new_state = state # state unchanged	
		if state == 'heading_to_new_article':
			if self.__contains_date__(line):
				new_state = 'new_article'
			elif 'Total' in line and 'quantity' in line:
				new_state = 'end_doc'
			else:
				new_state = state # state unchanged	
		if state == 'new_article':
			if self.__contains_date__(line):
				new_state = 'new_article'
			else:
				if 'conditions' in line and 'apply' in line and 'order' in line and 'confirmation' in line:
					new_state = 'bottom_page'
				elif 'Total' in line and 'quantity' in line:
					new_state = 'end_doc'
				else:
					new_state = 'remaining_article_description'
		if state == 'remaining_article_description':
			if self.__contains_date__(line):
				new_state = 'new_article'
			else:
				if 'conditions' in line and 'apply' in line and 'order' in line and 'confirmation' in line:
					new_state = 'bottom_page'
				elif 'Total' in line and 'quantity' in line:
					new_state = 'end_doc'
				else:
					new_state = state # state unchanged
		if state == 'bottom_page':
			if 'Article' in line:
				new_state = 'heading_to_new_article'
			elif 'Total' in line and 'quantity' in line:
				new_state = 'end_doc'
			else:
				new_state = state # state unchanged
		return new_state

	def process_txt(self, file_pointer, mail_date):
		'''
		reads a pdf document
		the file is read line by line,
		some lines a recognized as containing valuable information
		because they do contain some keyword indicating what is to be found
		- the top part contains client information (id, addresses, etc.)
		  the page is then scanned until we hit the article list
		- the HKLiving footnote indicates we have reached the bottom of page
		  and we then go and scan again a new page, looking for the article list
		- the flow is controlled using a state machine (encapsulated in the update state function)
		scanning an article line is tricky
		- it is tokenized (using the above function) to get the article id,
		  purchase order id and purchase date
		- the next column (reference) requires we make the assumption it contains
		  some fixed text followed by the article description
		- the article description is followed by the stock date
		  we use the date dashes to locate where the description text ends
		- the remaining string (starting with the stock date) contains
			- article unit price
			- quantity
			- net amount (total)
			- we make the assumption that discount is always equal to 0
			  so the net price equals unit price

		- all these are used to implement a (very tricky) way to extract
		  these information, by locating commas: since we are dealing with prices,
		  we know it is necessarily followed by two digits
		  for example, when reading 30-10-181347,500347,50 347,50
		  we know:
			- the stock date is 30-10-18
			- the net amout equals 347,50
		'''

		# get client info from file header
		line, client = self.__client_from_header__(file_pointer)
		if client == None:
			return None, None
		self.db.update_client(client)

		discount = 0 ### warning: discount not dealt with for now
		article_list = []

		line = file_pointer.readline()
		state  = self.__update_state__('start', line)
		while not state == 'end_doc':
			if state == 'new_article':
				# line is cut into article_id, order_id, ... subfields
				article_id, purchase_no, date_purchase, ref_desc, stock_date, prices_quantity_discount = self.__chunk_line__(line)
				date_purchase = self.dm.to_formatted_string(date_purchase, origin='hkliving', date_format='short')
				purchase_reference, description = self.__extract_purchase_ref_article_description__(ref_desc, article_id)

				try:
					unit_price, discount, net_price, quantity, net_amount = self.__extract_prices__(prices_quantity_discount)
				except IndexError as e:
					print('Error processing article info')
					pass
				article = Article(article_id)
				article.set_article_description(description.strip())	
				article.set_article_unit_price(net_price)
				article_list.append((article, quantity, discount))

			if state == 'remaining_article_description':
				# line simply contains extra text of previous article description
				try:
					article, quantity, discount = article_list.pop()
				except IndexError:
					print('pop error: ', line)
					return
				desc = article.get_article_description()
				desc = ' '.join([desc, line.strip()])
				article.set_article_description(desc)
				article_list.append((article, quantity, discount))

			line = file_pointer.readline()
			state  = self.__update_state__(state, line)
		purchase = Purchase(purchase_no, mail_date)
		purchase.set_purchase_client(client.get_client_id())
		purchase.set_purchase_date_order(date_purchase)
		purchase.set_purchase_reference(purchase_reference.strip())
		purchase.add_articles(article_list)
		return client, purchase

if __name__ == '__main__':
	'''
	path = 'doc_process/data/'
	filename = 'Orderbevestiging.pdf'
	filename = 'Yesss Electrique PFI Stock date March9.pdf'
	inv = Invoice(path, filename)
	client, purchase = inv.read()
	print('*************')
	print('Client id ', client.get_client_id())
	if client.get_client_email() == None:
		client.set_client_email('')
	print('*************')
	print('Client (string) ', client.to_string())
	print('*************')
	print('Client (list) ', client.to_list())
	print('*************')
	print('Purchase ', purchase.to_string())
	print('*************')

	db = ImpDatabaseInterface()
	db.update_client(client)
	c = db.get_client(client.get_client_id())
	print('*************')
	print(c.get_client_shop_address())
	#p = db.get_purchase(purchase.get_purchase_id())
	'''
	import ConfigParser
	config = ConfigParser.ConfigParser()
	config.read('crmwizard.ini') 
	inv = Invoice(config)
	s = '30-09-184174,50 0  174,50698,00'
	s = '01-10-1863,3503,3520,10'
	print(s)
	print(inv.__extract_prices__(s))

