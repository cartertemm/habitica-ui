import json

import pyperclip
import requests
import wx
import habitica
from habitica import api as habitica_api
from habitica.constants import *
from habitica import themes_manager

from ui import config
from ui import dialogs
from ui import sound
from ui import utils


api = None
sound_slug = "rosstavoTheme"
player = sound.Sound()
current_tasks = {}


def init_api():
	global api
	api = habitica_api.HabiticaAPI(
		api_user=config.config["api_user"],
		api_key=config.config["api_key"]
	)



def login(parent, username, password):
	if not api:
		init_api()
	try:
		response = api.login(username, password)
	except requests.exceptions.RequestException as exc:
		if exc.response.status_code == 401:
			dialogs.error(parent, "Error", "The username or password you entered is incorrect.")
		else:
			dialogs.error(parent, "Error logging in", str(exc))
		return False
	return True


def play_sound(sound_name):
	sound_name = themes_manager.get_sound(sound_name)
	if not sound_name:
		return False
	url = themes_manager.join_sound_url(sound_slug, sound_name)
	if not player.url_stream(url):
		return False
	return player.play()


def play_sound_for_task(task, up):
	up = True if up or up == "up" else False
	if task.type == "daily":
		play_sound("daily")
	elif task.type == "todo":
		play_sound("todo")
	elif task.type == "reward":
		play_sound("reward")
	else:  # task.type == "habit":
		if up:
			play_sound("plus_habit")
		else:
			play_sound("minus_habit")

def get_user(parent=None):
	response_dict = api.get_user()
	if not response_dict:
		dialogs.error(parent, "Error", f"Could not retrieve user information: {response_dict}")
		return False
	return response_dict

def get_tasks(parent=None):
	response_dict = api.get_tasks_for_user()
	if not response_dict.get("success"):
		dialogs.error(parent, "Error", f"Could not retrieve your tasks: {response_dict}")
		return False
	tasks_dict = response_dict["data"]
	return tasks_dict

def get_incomplete_dailies(task_data):
	choices = []
	for task in task_data:
		if task.type == "daily" and not task.completed:
			choices.append(task)
	return choices

def cron():
	return api.cron()

@utils.run_threaded
def update_tasks(parent, tasks_dict={}, update_ui=True):
	global current_tasks
	if not tasks_dict:
		response = api.get_tasks_for_user()
		tasks_dict = response["data"]
	current_tasks = tasks_dict
	items = {}
	for item in tasks_dict:
		type = item.type+"s"
		if not type in items:  # avoid KeyError
			items[type] = []
		items[type].append(item)
	if not items:
		print("error updating tasks")
	if update_ui:
		wx.CallAfter(parent.update_task_types, **items)


@utils.run_threaded
def score_task(parent, task, up=True, update_ui=True):
	if not task or not hasattr(task, "id"):
		return
	up = "up" if up else "down"
	# get the current set of user stats so we have a basis for comparison
	## todo: remove if this becomes too costly. If so we could fall back on api.current_user which is cached and not guaranteed to be valid
	#user = api.get_user()
	user = api.cached_user
	response = api.score_task(task.id, up)
	if not response["success"]:
		wx.CallAfter(dialogs.error, parent, "Error", f"An error occurred while attempting to score the selected task {up}: {response}")
		return
	data = response["data"]
	# do we have an item drop?
	tmp = data.get("_tmp", {})
	drop = tmp.get("drop")
	if drop:  # we do
		print(tmp)
		wx.CallAfter(dialogs.information, parent, f"{drop['key']} ({drop.get('target', '')} {drop.get('type', '')}!)", drop["dialog"])
		wx.CallAfter(play_sound, "Item_Drop")
	# have our stats changed?
	stat_changes = user.diff_stats(api._cached_user.stats)
	if stat_changes:
		wx.CallAfter(dialogs.information, parent, "Information", stat_changes)
	wx.CallAfter(play_sound_for_task, task, up)
	if update_ui:
		update_tasks(parent, update_ui=update_ui)


@utils.run_threaded
def create_task(parent, task_data):
	type = task_data["type"]
	text = task_data["text"]
	del task_data["type"]
	del task_data["text"]
	response = api.create_task(type, text, **task_data)
	if not response["success"]:
		dialogs.error(parent, "Error", f"An error occurred while attempting to create the given task: {response}")
		return
	update_tasks(parent)


@utils.run_threaded
def update_task(parent, task_data):
	task_id= task_data["id"]
	del task_data["id"]
	response = api.update_task(task_id, **task_data)
	if not response["success"]:
		dialogs.error(parent, "Error", f"An error occurred while attempting to modify the given task: {response}")
		return
	update_tasks(parent)

def copy_json(parent, cls):
	pyperclip.copy(cls.to_json())

@utils.run_threaded
def delete_task(parent, task):
	confirmation = dialogs.question(parent, "Delete task?", "Are you sure you want to delete the selected "+task.type+"?", warning=True)
	if confirmation:
		print("deleting")
		response = api.delete_task(task._id)
		if not response["success"]:
			dialogs.error(parent, "Error", "There was an error deleting the requested "+task.type+": "+response)
			return
		update_tasks(parent)
