import os
import sys
import appdirs
import wx

from ui import config


name = "Habitica Task Viewer"
version = "0.1 Beta"
author="Carter Temm <cartertemm@gmail.com>"
data_dir = appdirs.user_data_dir("Habitica", roaming=True)
config_path = os.path.join(data_dir, "config.ini")
debug = False
app = None


def from_source():
	return getattr(sys, "frozen", False)

def init():
	"""Non UI-critical app initialization"""
	global app, debug
	args = sys.argv[1:]
	if "--debug" in args:
		debug = True
		print("Running with debug flag")
	if not os.path.isdir(data_dir):
		if debug:
			print("Creating configuration directory")
		os.makedirs(data_dir)
	config.load(config_path)
	app = wx.App()

def exit():
	if app:
		app.ExitMainLoop()
	sys.exit()
