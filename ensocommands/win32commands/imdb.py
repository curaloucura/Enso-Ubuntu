from win32com.shell import shell, shellcon
import os
import glob
import operator
import re

import enso.messages
import logging

def displayMessage(msg):
	enso.messages.displayMessage("<p>%s</p>" % msg)

def cmd_imdb(ensoapi, name=False):
	""" Search IMDB for {name} """
	import urllib

	if (name == False):
		name = ensoapi.get_selection().get('text', '').strip()
		if (not name):
			displayMessage('No text was selected')
			return False

	displayMessage(u"Searching IMDB for <command>%s</command>" % name)

	try:
		url = 'http://www.imdb.com/find?s=all&q=%s&x=0&y=0' % urllib.quote_plus(name)
		os.startfile(url)
		return True
	except Exception, e:
		logging.error(e)
		return False
