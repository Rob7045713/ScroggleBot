''' ScroggleBot.py

A chat bot for Scroggle (www.dailyscroggle.com)

Use:
	ScroggleBot.run() will start the bot

	ScroggleBot will automatically read the chat and post the current partial
	word list, as well as listen for commands

Commands:
	1ab		adds the prefix 'ab' to the word list with a count of 1

	-ab		removes the prefix 'ab' from the word list

	!list 	prints out the current list

	!clear 	clears the list

	!off 	turns off the bot

	!lock 	locks the list

	!unlock unlocks the list

	!mute 	mutes the bot

	!unmute unmutes the bot

Copyright (c) 2014 Rob Argue (robargue@gmail.com)
'''

__author__ = 'Rob Argue'

from HTMLParser import HTMLParser
import time
from datetime import datetime
import re
import urllib
import mechanize
import json

class ScroggleBot:
	''' Main class for the the ScorggleBot
	'''

	def __init__(self, user_name, password):
		''' Constructor for ScroggleBot

		Arguments:
			user_name - User name to log in with
			password  - Password to log in with
		'''

		self.partial_word_list = {}
		self.official_word_list = None
		self.last_message_processed = None
		self.list_updated = False
		self.browser = mechanize.Browser()
		self.base_url = 'http://www.dailyscroggle.com'
		self.user_name = user_name
		self.password = password
		self.DEBUG = True
		self.last_update_time = time.time()
		self.update_delay = 2
		self.last_auto_post = time.time()
		self.auto_post_delay = 10
		self.on = True
		self.locked = False
		self.mute = True
		try:
			nick_file = open('nicknames.json', 'r')
			self.nicknames = json.load(nick_file)
			nick_file.close()
		except:
			self.nicknames = {}
			print 'Error loading nicknames'


	def run(self):
		''' Starts the ScroggleBot		
		'''

		self.login()

		while self.on:
			now = time.time()
			self.update()

			# auto post list
			if self.list_updated and (time.time() - self.last_auto_post) > self.auto_post_delay:
				self.post_message(self.make_list(self.partial_word_list))
				self.list_updated = False
				self.last_auto_post = time.time()

			# if time has passed 10 pm
			last_hour = datetime.fromtimestamp(self.last_update_time).hour
			last_min = datetime.fromtimestamp(self.last_update_time).minute
			last_sec = datetime.fromtimestamp(self.last_update_time).second
			curr_hour = datetime.fromtimestamp(now).hour
			curr_min = datetime.fromtimestamp(now).minute
			curr_sec = datetime.fromtimestamp(now).second

			if curr_hour == 22 and curr_min == 0 and last_sec < 30 and curr_sec >= 30:
				self.new_day()

			self.last_update_time = now
			time.sleep(self.update_delay)


	def new_day(self):
		''' Updates for the new puzzle
		'''

		self.partial_word_list.clear()
		self.list_updated = False
		self.locked = False
		self.mute = False
		self.post_message("Good luck all!")


	def update(self):
		''' Reads and processes chat
		'''

		# grab the messages out of chat
		chat = self.get_message_html()

		# if chat was fetched properly
		if chat != None:
			try:
				parser = SBHTMLParser()
				parser.feed(chat.read())
				chat.close()
				messages = parser.get_messages()
			except:
				messages = []
		else:
			messages = []

		# process all new messages
		for i in range(len(messages)):
			if messages[i] == self.last_message_processed:
				break

			else:
				self.process_message(messages[i])

		if len(messages) > 0:
			self.last_message_processed = messages[0]

	def nickname(self, username, nick):
		''' Records a nickname for a user

		Arguments:
			username - user to add a nickname for
			nick     - nickname to give the user
		'''
		
		self.nicknames[username] = nick
		nick_file = open('nicknames.json', 'w')
		json.dump(self.nicknames, nick_file)
		nick_file.close()

	def make_list(self, word_list):
		''' Creates a string representaion of a word list

		Returns:
			String representation of the word list

		Arguments:
			word_list - Dictionary with a prefix to count mapping
		'''

		prefs = word_list.items()
		prefs.sort()

		word_list = ''

		if len(prefs) == 0:
			word_list = 'list is empty '

		for pref in prefs:
			word_list = word_list + pref[1] + pref[0] + ' '

		return word_list[:-1]


	def process_message(self, message):
		''' Processess a message and acts on all commands

		Arguments:
			message - Message object to process	
		'''

		if message.user in self.nicknames:
			user = self.nicknames[message.user]
		else:
			user = message.user

		# debug printout of the message
		if self.DEBUG:
			print '----Processing message:'
			print '      User: ', message.user
			print '      Time: ', message.time
			print '      Text: ', message.text
			print ''

		# some pleasantries
		if re.search('([Hh]i|[Hh]ello) .*([Ss]croggle)?[Bb]ot\s?', message.text):
			self.post_message('Hi ' + user)

		if re.search('^([Ff][Ii][Nn][Ii][Ss][Hh][Ee][Dd]|[Dd][Oo][Nn][Ee])', message.text):
			self.post_message('Congrats ' + user)

		if re.search('([Tt][Yy]|[Th]ank).*([Ss]croggle)?[Bb]ot\s?', message.text):
			self.post_message('You\'re welcome ' + user)
		
		if re.search('([Gg]ood)?[Nn]ight .*([Ss]croggle)?[Bb]ot\s?', message.text):
			self.post_message('Goodnight ' + user)

		# !clear command - clear list
		if re.search('![Cc]lear', message.text) != None:
			self.partial_word_list.clear()
			self.list_updated = True

		# !list command - post list
		if re.search('(^[Ll]$)|(![Ll]ist)', message.text) != None:
			self.post_message(self.make_list(self.partial_word_list))

		# !off command - turns off the bot
		if re.search('![Oo]ff', message.text) != None:
			self.on = False

		# !lock command - locks the list
		if re.search('![Ll]ock', message.text) != None:
			self.locked = True

		# !unlock command - unlocks the list
		if re.search('![Uu]nlock', message.text) != None:
			self.locked = False

		# !mute command - mutes the bot
		if re.search('![Mm]ute', message.text) != None:
			self.mute = True

		# !unmute command - unmutes the bot
		if re.search('![Uu]nmute', message.text) != None:
			self.mute = False

		# !nick command - changes your nickname
		if re.search('![Nn]ick', message.text) != None:
			sp = ' '
			self.nickname(message.user, sp.join(message.text.split()[1:]))

		if not self.locked:
			# 1ab commands - add new entries to the word list
			entries = re.findall('[0-9]+[a-zA-Z]{2}', message.text)

			for ent in entries:
				if ent[-2:] not in self.partial_word_list or ent[:-2] != self.partial_word_list[ent[-2:]]:
					if self.DEBUG:
						print '    Adding ' + ent[:-2] + ent[-2:] + ' to list'

					self.partial_word_list[ent[-2:]] = ent[:-2]
					self.list_updated = True

			# -ab commands - remove entries from the word list
			removals = re.findall('\-[a-zA-Z]{2}', message.text)

			for rem in removals:
				if self.partial_word_list.has_key(rem[-2:]):
					if self.DEBUG:
						print '    Removing ' + rem[:-2] + rem[-2:] + ' from list'

					del self.partial_word_list[rem[-2:]]
					self.list_updated = True

	
	def get_message_html(self):
		''' Pulls the HTML for the message list from the site

		Returns:
			Full HTML for the message list
		'''

		numRows = 0
		lastMessageDate = 600000000000000000
		time = self.GMTString()
		url = self.base_url + '/Chat/getMessages.aspx?CR=1'
		url = url + '&numRows=' + str(numRows)
		url = url + '&lastMessageDate=' + str(lastMessageDate)
		url = url + '&Time=' + time

		try:
			return urllib.urlopen(url)
		except IOError:
			print 'Failed to open (getMessageHTML)'
			return None
	
	def post_message(self, text):
		''' Posts a message to the site

		Arguments:
			text - Message text to post
		'''

		if self.DEBUG:
			print '++++Sending message: ' + ('(muted)' if self.mute else '')
			print '      '  + text
			print ''

		if not self.mute:

			# max length cutoff to match the javascript
			if len(text) > 300:
				text = text[:300]

			time = self.GMTString()

			url = self.base_url + '/Chat/submitMessage.aspx?CR=1'
			url = url + '&time=' + urllib.quote(time)
			url = url + '&message=' + urllib.quote(text)

			try:
				self.browser.open(url)
			except IOError:
				print 'Failed to open (post_message)'
	
	def login(self):
		''' Logs onto the site
		'''

		self.browser.open(self.base_url)
		self.browser.select_form('aspnetForm')
		self.browser['ctl00$LoginArea$Login1$UserName'] = self.user_name
		self.browser['ctl00$LoginArea$Login1$Password'] = self.password
		self.browser.submit()

	
	def GMTString(self):
		''' Creates the GMT string for time used for chat forms
		
		Returns:
			String of the current time in the same format as javascript's
			toUTCTime()
		'''
		
		return datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')


class SBHTMLParser(HTMLParser):
	''' Utility class for processing the message list HTML
	'''

	def __init__(self):
		HTMLParser.__init__(self)
		self.tag = 'None'
		self.message = Message()
		self.messages = []


	def handle_starttag(self, tag, attrs):
		for attr in attrs:
			if attr[0] == 'class':
				if attr[1] == 'ChatUserName' or attr[1] == 'ChatPostTime' or attr[1] == 'ChatMessageText':
					self.tag = attr[1]


	def handle_data(self, data):
		if self.tag == 'ChatUserName':
			self.message = Message()
			self.messages.append(self.message)
			self.message.user = data

		if self.tag == 'ChatPostTime':
			self.message.time = data

		if self.tag == 'ChatMessageText':
			self.message.text = data

		self.tag = 'None'


	def get_messages(self):
		''' Accessor for the message list
			
		Returns:
			List of Message objects that have been parsed from the HTML
		'''

		return self.messages

	def clear_messages(self):
		''' Clears the parser's message list
		'''

		self.messages = []




class Message:
	''' Data structure for messages
	'''

	def __init__(self):
		self.user = ''
		self.time = ''
		self.text = ''

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.__dict__ == other.__dict__
		else:
			return False