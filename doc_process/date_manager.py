# -*- coding: utf-8 -*-

import datetime
import dateutil.parser

class DateManager(object):
	'''
	The DataManager object is responsible for normalizing date expressions
	before storing them in the database,
	and also responsible for converting from the database format to
	a datetime object.
	'''
	def __init__(self):
		super(DateManager, self).__init__()
		# python full (date, time, offset) normalize follows format 2018-09-07 14:01:28+0200
		self.full_format = '%Y-%m-%d %H:%M:%S%z'
		self.short_format = '%Y-%m-%d'
		
	def to_formatted_string(self, date_string, origin='gmail', date_format='full'):
		# outputs date as a full formated string
		if origin == 'gmail':
			# GMail reveived date follows format 2018-09-07 14:01:28+02:00
			# which differs from python's standard way of writing offsets
			date_time_z = dateutil.parser.parse(date_string)
			if date_format == 'full':
				print('Outputting date as: ', datetime.datetime.strftime(date_time_z, self.full_format))
				return datetime.datetime.strftime(date_time_z, self.full_format)
			else:
				print('Outputting date as: ', datetime.datetime.strftime(date_time_z, self.short_format))
				return datetime.datetime.strftime(date_time_z, self.short_format)

		if origin == 'hkliving':
			# HK Living date appear in order confirmations and invoices
			# as dd-mm-yy strings
			date = datetime.datetime.strptime(date_string, '%d-%m-%y')
			if date_format == 'full':
				return datetime.datetime.strftime(date, self.full_format)
			else:
				return datetime.datetime.strftime(date, self.short_format)

if __name__ == '__main__':
	dm = DateManager()
	d = '2018-09-07 14:01:28+02:00'
	d= '6 Jul 2018 09:00:07 +0200'
	print dm.to_formatted_string(d, date_format='full')
	print dm.to_formatted_string(d, date_format='short')
	d = '07-09-18'
	print dm.to_formatted_string(d, origin='hkliving', date_format='full')
	print dm.to_formatted_string(d, origin='hkliving', date_format='short')
