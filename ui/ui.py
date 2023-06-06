import wx
import wx.adv

from ui import app
from ui import config
from ui import dialogs
from ui import habitica_functions as habitica


label_flags = wx.ALL | wx.ALIGN_CENTER_VERTICAL
control_flags = wx.ALL | wx.EXPAND


class LoginDialog(wx.Dialog):
	def __init__(self, parent, title="Login"):
		super().__init__(parent, title=title)
		self.setup_layout()
		username = config.config.get("username")
		if username:
			self.username.SetValue(username)
			# if we already have a proven working username, focus the password field for convenience
			self.password.SetFocus()
		api_key = config.config.get("api_key", "")
		api_user = config.config.get("api_user", "")
		self.api_key.SetValue(api_key)
		self.api_user.SetValue(api_user)
		self.remember_me.SetValue(True)
		self.bind_events()

	def setup_layout(self):
		self.main_sizer = wx.BoxSizer(wx.VERTICAL)
		username_label = wx.StaticText(self, label="Username:")
		self.username = wx.TextCtrl(self)
		username_sizer = wx.BoxSizer(wx.HORIZONTAL)
		username_sizer.Add(username_label, 0, label_flags, 5)
		username_sizer.Add(self.username, 1, control_flags, 5)
		self.main_sizer.Add(username_sizer, 0, wx.EXPAND)
		password_label = wx.StaticText(self, label="Password:")
		self.password = wx.TextCtrl(self, style=wx.TE_PASSWORD)
		pw_sizer = wx.BoxSizer(wx.HORIZONTAL)
		pw_sizer.Add(password_label, 0, label_flags, 5)
		pw_sizer.Add(self.password, 1, control_flags, 5)
		self.main_sizer.Add(pw_sizer, 0, wx.EXPAND)
		self.remember_me = wx.CheckBox(self, label="Remember username")
		cb_sizer = wx.BoxSizer(wx.HORIZONTAL)
		cb_sizer.Add(self.remember_me, 1, control_flags, 5)
		self.main_sizer.Add(cb_sizer, 0, wx.EXPAND)
		options_box = wx.StaticBox(self, label="API Credentials")
		options_sizer = wx.StaticBoxSizer(options_box, wx.VERTICAL)
		api_user_label = wx.StaticText(self, label="API User:")
		self.api_user = wx.TextCtrl(self)
		api_user_sizer = wx.BoxSizer(wx.HORIZONTAL)
		api_user_sizer.Add(api_user_label, 0, label_flags, 5)
		api_user_sizer.Add(self.api_user, 1, control_flags, 5)
		options_sizer.Add(api_user_sizer, 0, wx.EXPAND)
		api_key_label = wx.StaticText(self, label="API Key:")
		self.api_key = wx.TextCtrl(self, style=wx.TE_PASSWORD)
		api_key_sizer = wx.BoxSizer(wx.HORIZONTAL)
		api_key_sizer.Add(api_key_label, 0, label_flags, 5)
		api_key_sizer.Add(self.api_key, 1, control_flags, 5)
		options_sizer.Add(api_key_sizer, 0, wx.EXPAND)
		self.main_sizer.Add(options_sizer, 0, wx.EXPAND)
		self.options_box = wx.StaticBox(self, label="Other options")
		self.reset_password = wx.Button(self.options_box, label="Forgot password")
		self.register = wx.Button(self.options_box, label="Register new account")
		options_sizer = wx.BoxSizer(wx.HORIZONTAL)
		options_sizer.Add(self.options_box, 1, control_flags, 5)
		self.main_sizer.Add(options_sizer, 0, wx.EXPAND)
		self.add_buttons()
		self.SetSizerAndFit(self.main_sizer)
		self.Layout()

	def bind_events(self):
		self.Bind(wx.EVT_BUTTON, self.on_login, self.login_btn)

	def add_buttons(self):
		btn_sizer = wx.StdDialogButtonSizer()
		self.login_btn = wx.Button(self, label="Login")
		btn_sizer.AddButton(self.login_btn)
		self.cancel_btn= wx.Button(self, id=wx.ID_CANCEL)
		btn_sizer.AddButton(self.cancel_btn)
		self.main_sizer.Add(btn_sizer, 0, wx.EXPAND)
		btn_sizer.Realize()
		self.SetEscapeId(self.cancel_btn.GetId())
		# so that an enter press in the password field activates the login button
		self.login_btn.SetDefault()
		self.SetAffirmativeId(self.login_btn.GetId())

	def on_login(self, event):
		username = self.username.GetValue()
		password = self.password.GetValue()
		api_user = self.api_user.GetValue()
		api_key = self.api_key.GetValue()
		if not username or not password or not api_user or not api_key:
			wx.MessageBox("You must enter a username, password, API user, and API key.", "Error", wx.OK | wx.ICON_ERROR)
			self.username.SetFocus()
			return
		config.config["api_user"] = api_user
		config.config["api_key"] = api_key
		config.config.write()
		success = habitica.login(self, username, password)
		if not success:
			self.username.SetFocus()
			return
		else:
			if self.remember_me.IsChecked():
				config.config["username"] = username
				config.config.write()
		self.EndModal(success)


class CronDialog(wx.Dialog):
	def __init__(self, parent, task_data, incomplete_items, title="Yesterdays activities"):
		super().__init__(parent, title=title)
		self.task_data = task_data
		self.incomplete_items = incomplete_items
		self.setup_layout()

	def setup_layout(self):
		self.main_sizer = wx.BoxSizer(wx.VERTICAL)
		dailies_box = wx.StaticBox(self, label="Check off any dailies you did yesterday")
		dailies_sizer = wx.StaticBoxSizer(dailies_box, wx.HORIZONTAL)
		self.checkboxes = []
		for task in self.incomplete_items:
			cb = wx.CheckBox(dailies_box, label=str(task))
			cb.task = task
			self.checkboxes.append(cb)
			dailies_sizer.Add(cb, 1, control_flags, 5)
		self.main_sizer.Add(dailies_sizer, 0, wx.EXPAND)
		btn_sizer = wx.StdDialogButtonSizer()
		self.done_btn = wx.Button(self, id=wx.ID_OK)
		btn_sizer.AddButton(self.done_btn)
		self.main_sizer.Add(btn_sizer, 0, wx.EXPAND)
		btn_sizer.Realize()
		self.SetAffirmativeId(self.done_btn.GetId())

	def complete_selected(self):
		for ctrl in self.checkboxes:
			if not ctrl.IsChecked() or not hasattr(ctrl, "task"):
				continue
			# do not pass as a parent, as we only call this function after this dialog has been closed
			habitica.score_task(None, ctrl.task, up=True, update_ui=False)
		print(habitica.cron())  # todo: currently we're eating the notifications

class TaskTreeFrame(wx.Frame):
	def __init__(self, parent=None, title="Task Viewer", cached_tasks=[], **kwargs):
		super().__init__(parent, title=title, **kwargs)
		self.cached_tasks = cached_tasks
		self.panel = wx.Panel(self)
		self.descendants = []
		self.setup_layout()
		self.bind_events()
		self.update_descendant_tab_order()
		self.panel.SetMinSize((200, 200))
		self.panel.SetSizerAndFit(self.main_sizer)
		self.panel.Layout()

	def setup_layout(self):
		self.main_sizer = wx.BoxSizer(wx.VERTICAL)
		nb_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.notebook = wx.Notebook(self.panel)
		self.tasks_panel = TaskTreePanel(self.notebook)
		self.notebook.AddPage(self.tasks_panel, "Tasks")
		nb_sizer.Add(self.notebook, 0, control_flags, 5)
		self.main_sizer.Add(nb_sizer, 1, wx.EXPAND)
		#self.main_sizer.Add(self.notebook, 1, wx.EXPAND)

	def bind_events(self):
		self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_notebook_page_changed)
		#self.notebook.Bind(wx.EVT_NAVIGATION_KEY, self.on_notebook_navigation)
		self.Bind(wx.EVT_NAVIGATION_KEY, self.on_navigation)

	def on_notebook_page_changed(self, event):
		selected_page = self.notebook.GetSelection()
		if selected_page == 0:
			self.panel.update_focused_item_text("Tasks")

	def get_last_enabled_descendant(self, item):
		children = [i for i in item.GetChildren()]
		if not children:
			return
		for child in children[::-1]:
			if child.IsEnabled():
				return child

	def on_navigation(self, event):
		#print(f"current focus: {event.GetCurrentFocus()}")
		#print(f"find focus: {self.FindFocus()}")
		if self.FindFocus() in self.descendants:
			self.notebook.SetFocus()
		elif not event.GetDirection():
			event.Skip()
			last_descendant = self.get_last_enabled_descendant(self.notebook.GetPage(self.notebook.GetSelection()))
			if last_descendant and last_descendant != self.notebook:
				last_descendant.SetFocus()
		else:
			event.Skip()

	def update_descendant_tab_order(self):
		for page_num in range(self.notebook.GetPageCount()):
			last_descendant = self.get_last_enabled_descendant(self.notebook.GetPage(page_num))
			if last_descendant:
				self.descendants.append(last_descendant)


class BasePanel(wx.Panel):
	def __init__(self, parent):
		super().__init__(parent)
		self.setup_layout()
		self.init_menus()
		self.bind_events()

	def tab_control_focus(self):
		self.GetParent().SetFocus()

	def setup_layout(self):
		pass  # implement in subclass

	def init_menus(self):
		pass  # implement in subclass

	def bind_events(self):
		pass  # implement in subclass


class  TaskTreePanel(BasePanel):
	def __init__(self, parent):
		super().__init__(parent)
		self.add_task_types()
		self.tree_ctrl.SetFocus()

	def init_menus(self):
		self.new_menu = wx.Menu()
		for task_type in habitica.create_task_types:
			item = self.new_menu.Append(wx.ID_ANY, task_type.capitalize())
			self.Bind(wx.EVT_MENU, self.on_new_menu_item, item)
		self.task_context_menu = wx.Menu()
		self.mark_up_item = self.task_context_menu.Append(wx.ID_ANY, "Mark up")
		self.mark_down_item = self.task_context_menu.Append(wx.ID_ANY, "Mark down")
		self.view_item = self.task_context_menu.Append(wx.ID_ANY, "View task")
		self.copy_json_item = self.task_context_menu.Append(wx.ID_ANY, "Copy JSON")
		self.delete_item = self.task_context_menu.Append(wx.ID_ANY, "Delete")

	def setup_layout(self):
		self.main_sizer = wx.BoxSizer(wx.VERTICAL)
		self.tree_ctrl = wx.TreeCtrl(self)
		self.root = self.tree_ctrl.AddRoot("Task Types")
		self.main_sizer.Add(self.tree_ctrl, 0, control_flags, 5)
		self.new_button = wx.Button(self, label="&New")
		self.main_sizer.Add(self.new_button, 0, control_flags, 5)

	def bind_events(self):
		self.tree_ctrl.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_item_activate)
		self.tree_ctrl.Bind(wx.EVT_TREE_ITEM_MENU, self.on_context_menu)
		self.new_button.Bind(wx.EVT_BUTTON, self.on_new)
		self.Bind(wx.EVT_MENU, self.on_mark_up, self.mark_up_item)
		self.Bind(wx.EVT_MENU, self.on_mark_down, self.mark_down_item)
		self.Bind(wx.EVT_MENU, self.on_item_activate, self.view_item)
		self.Bind(wx.EVT_MENU, self.on_copy_json, self.copy_json_item)
		self.Bind(wx.EVT_MENU, self.on_delete, self.delete_item)
		self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)

	def on_set_focus(self, event):
		self.SetFocusIgnoringChildren()

	def on_new(self, event):
		self.PopupMenu(self.new_menu)

	def on_new_menu_item(self, event):
		label = self.new_menu.GetLabel(event.Id).lower()
		dlg = self.dialog_from_type(label)
		dlg = dlg(self)
		res = dlg.ShowModal()
		if res in [wx.ID_CLOSE, wx.ID_CANCEL]:
			return
		res = dlg.get_task_result()
		if not res:
			return
		habitica.create_task(self, res)

	def on_mark_up(self, event):
		task = self.get_focused_item_data()
		if not task:
			event.Skip()
			return
		habitica.score_task(self, task, up=True)

	def on_mark_down(self, event):
		task = self.get_focused_item_data()
		if not task:
			event.Skip()
			return
		habitica.score_task(self, task, up=False)

	def on_item_activate(self, event):
		task = self.get_focused_item_data()
		dlg = self.dialog_from_type(task.type)
		if not dlg:  # we're on a tree view or item that is not a task
			return
		dlg = dlg(self, data=task.__dict__)
		res = dlg.ShowModal()
		if res in [wx.ID_CLOSE, wx.ID_CANCEL]:
			return
		res = dlg.get_task_result(include_id=True)
		if not res:
			return
		habitica.update_task(self, res)

	def on_copy_json(self, event):
		task = self.get_focused_item_data()
		if not task:
			print("no data")
			event.Skip()
			return
		habitica.copy_json(self, task)

	def on_delete(self, event):
		task = self.get_focused_item_data()
		if not task:
			print("no data")
			event.Skip()
			return
		habitica.delete_task(self, task)


	def on_context_menu(self, event):
		task = self.get_focused_item_data()
		if not task:
			print("no data")
			event.Skip()
			return
		if task.type in ["daily", "todo"]:
			self.remove_mark_down_from_menu()
			self.mark_up_item.SetItemLabel("Complete "+task.type)
			self.mark_up_item.Enable(True)
		else:
			self.mark_up_item.SetItemLabel("Score "+task.type+" up")
			self.mark_down_item.SetItemLabel("Score "+task.type+" down")
			if task.up:
				self.mark_up_item.Enable(True)
			else:
				self.mark_up_item.Enable(False)
			if task.down:
				# only show this item when it's available
				self.add_mark_down_to_menu()
				self.mark_down_item.Enable(True)
			else:
				self.remove_mark_down_from_menu()
				self.mark_down_item.Enable(False)
			#self.complete_item.Enable(False)
		self.PopupMenu(self.task_context_menu)

	def dialog_from_type(self, type):
		if type == "habit":
			dlg = HabitDialog
		elif type == "daily":
			dlg = DailyDialog
		elif type == "todo":
			dlg = TodoDialog
		elif type == "reward":
			dlg = RewardDialog
		return dlg

	def add_task_types(self):
		"""Add each task type to the tree as a child of the root node"""
		for task_type in habitica.valid_task_types:
			item = self.tree_ctrl.AppendItem(self.root, task_type)
			setattr(self, task_type, item)
		cached_tasks = self.GetParent().GetParent().GetParent().cached_tasks or []
		habitica.update_tasks(self, tasks_dict=cached_tasks)

	def update_task_types(self, clear_children=True, **kwargs):
		"""Update first level tree view items.

		args:
			clear_children (bool): Delete pre-existing children under each type node.
			kwargs (dict): Tree view entries in the form {type, items}, where type can be any of habitica.valid_task_types and items is a list of strings to be displayed.
		"""
		self.tree_ctrl.Freeze()
		for root, items in kwargs.items():
			if not root in habitica.valid_task_types:
				print(f"{root} not found in tree")
				continue
			task_type = getattr(self, root, None)
			if not task_type:
				print("error")
				continue
			if clear_children:
				self.tree_ctrl.DeleteChildren(task_type)
			for item in items:
				self.tree_ctrl.AppendItem(task_type, str(item), data={"item": item})
		self.tree_ctrl.Thaw()

	def add_mark_down_to_menu(self):
		if not self.task_context_menu.FindItemById(self.mark_down_item.GetId()):
			self.task_context_menu.Insert(1, self.mark_down_item)

	def remove_mark_down_from_menu(self):
		if self.task_context_menu.FindItemById(self.mark_down_item.GetId()):
			self.task_context_menu.Remove(self.mark_down_item)

	def get_focused_item_data(self):
		item = self.tree_ctrl.GetFocusedItem()
		data = self.tree_ctrl.GetItemData(item)
		if data and "item" in data:
			return data["item"]

	def update_focused_item_text(self, new_text):
		item = self.tree_ctrl.GetFocusedItem()
		self.tree_ctrl.SetItemText(item, new_text)


class BaseTaskDialog(wx.Dialog):
	def __init__(self, parent, title, data={}, include_reminders_box=True, include_checklist_box=True, **kwargs):
		super().__init__(parent=parent, title=title, **kwargs)
		self.title = title
		self.include_reminders_box = include_reminders_box
		self.include_checklist_box = include_checklist_box
		self.panel = wx.Panel(self)
		self.main_sizer = wx.BoxSizer(wx.VERTICAL)
		self.setup_layout()
		if data:
			self.populate_fields(data)
			self.SetTitle("Update"+self.title[self.title.find(" "):])
		self.finalize()

	def setup_layout(self):
		text_label = wx.StaticText(self.panel, label="Text:")
		self.text = wx.TextCtrl(self.panel)
		text_sizer = wx.BoxSizer(wx.HORIZONTAL)
		text_sizer.Add(text_label, 0, label_flags, 5)
		text_sizer.Add(self.text, 1, control_flags, 5)
		self.main_sizer.Add(text_sizer, 0, wx.EXPAND)
		notes_label = wx.StaticText(self.panel, label="Notes (formatted in Markdown):")
		self.notes = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE)
		notes_sizer = wx.BoxSizer(wx.HORIZONTAL)
		notes_sizer.Add(notes_label, 0, label_flags, 5)
		notes_sizer.Add(self.notes, 1, control_flags, 5)
		self.main_sizer.Add(notes_sizer, 0, wx.EXPAND)
		difficulty_label = wx.StaticText(self.panel, label="difficulty:")
		self.difficulty = wx.Choice(self.panel, choices=list(habitica.difficulties.keys()))
		self.difficulty.SetSelection(habitica.default_difficulty)
		difficulty_sizer = wx.BoxSizer(wx.HORIZONTAL)
		difficulty_sizer.Add(difficulty_label, 0, label_flags, 5)
		difficulty_sizer.Add(self.difficulty, 1, control_flags, 5)
		self.main_sizer.Add(difficulty_sizer, 0, wx.EXPAND)
		attribute_label = wx.StaticText(self.panel, label="attribute to effect:")
		self.attribute = wx.Choice(self.panel, choices=list(habitica.user_attributes))
		self.attribute.SetSelection(habitica.user_attributes.index(habitica.default_task_attribute))
		attribute_sizer = wx.BoxSizer(wx.HORIZONTAL)
		attribute_sizer.Add(attribute_label, 0, label_flags, 5)
		attribute_sizer.Add(self.attribute, 1, control_flags, 5)
		self.main_sizer.Add(attribute_sizer, 0, wx.EXPAND)
		if self.include_reminders_box:
			self.reminders_box = wx.StaticBox(self.panel, label="Reminders")
			reminders_label = wx.StaticText(self.reminders_box, label="Reminders")
			self.reminders = wx.ListCtrl(self.reminders_box, style=wx.LC_REPORT)
			self.reminders.InsertColumn(0, "Start date")
			self.reminders.InsertColumn(1, "Time")
			self.add_reminder_btn = wx.Button(self.reminders_box, label="Add reminder")
			self.delete_reminder_btn = wx.Button(self.reminders_box, label="Delete reminder")
			self.main_sizer.Add(self.reminders_box, 0, wx.EXPAND)
		if self.include_checklist_box:
			self.checklist_box = wx.StaticBox(self.panel, label="Checklist")
			self.include_checklist_ctrl = wx.CheckBox(self.checklist_box, label="Include checklist")
			checklist_label = wx.StaticText(self.checklist_box, label="Items")
			self.checklist_ctrl = wx.ListCtrl(self.checklist_box, style=wx.LC_REPORT)
			self.checklist_ctrl.InsertColumn(0, "Item")
			self.add_checklist_item_btn = wx.Button(self.checklist_box, label="Add Item")
			self.delete_checklist_item_btn = wx.Button(self.checklist_box, label="Delete Item")
			self.main_sizer.Add(self.checklist_box, 0, wx.EXPAND)

	def populate_fields(self, task_data):
		self.data = task_data
		self.text.SetValue(task_data["text"])
		self.notes.SetValue(task_data["notes"])
		# ugh
		self.difficulty.SetSelection(list(habitica.difficulties.values()).index(task_data["priority"]))
		self.attribute.SetSelection(habitica.user_attributes.index(task_data["attribute"]))

	def get_task_result(self, include_id=False):
		result = {
			"text": self.text.GetValue(),
			"type": self.type,
			"notes": self.notes.GetValue(),
			"priority": habitica.difficulties[self.difficulty.GetStringSelection()],
			"attribute": self.attribute.GetStringSelection()
		}
		if self.data and include_id:
			result["id"] = self.data["_id"]
		return result

	def bind_events(self):
		if self.include_checklist_box:
			self.include_checklist_ctrl.Bind(wx.EVT_CHECKBOX, self.on_include_checklist_changed)

	def add_buttons(self):
		btn_sizer = wx.StdDialogButtonSizer()
		self.save_btn = wx.Button(self.panel, label="Save")
		btn_sizer.AddButton(self.save_btn)
		self.close_btn= wx.Button(self.panel, id=wx.ID_CLOSE)
		btn_sizer.AddButton(self.close_btn)
		self.main_sizer.Add(btn_sizer, 0, wx.EXPAND)
		btn_sizer.Realize()
		self.SetEscapeId(self.close_btn.GetId())
		self.SetAffirmativeId(self.save_btn.GetId())

	def finalize(self):
		self.add_buttons()
		self.bind_events()
		if self.include_checklist_box:
			self.on_include_checklist_changed(None)  # show or hide the checklist based on checkbox state
		self.panel.SetSizerAndFit(self.main_sizer)
		self.panel.Layout()

	def on_include_checklist_changed(self, event):
		show = self.include_checklist_ctrl.GetValue()
		self.checklist_ctrl.Show(show)
		self.add_checklist_item_btn.Show(show)
		self.delete_checklist_item_btn.Show(show)
		self.panel.Layout()  # always update the layout after changing controls visibility


class HabitDialog(BaseTaskDialog):
	type="habit"
	def __init__(self, parent, title="Add habit", data={}, **kwargs):
		super().__init__(parent, title=title, data=data, **kwargs)

	def setup_layout(self):
		super().setup_layout()
		self.controls_box = wx.StaticBox(self.panel, label="Controls")
		self.plus = wx.CheckBox(self.controls_box, label="Positive control")
		self.minus = wx.CheckBox(self.controls_box, label="Negative control")
		self.main_sizer.Add(self.controls_box, 0, wx.EXPAND)

	def populate_fields(self, task_data):
		super().populate_fields(task_data)
		self.plus.SetValue(task_data.get("up", False))
		self.minus.SetValue(task_data.get("down", False))

	def get_task_result(self, include_id=False):
		result = super().get_task_result(include_id=include_id)
		result["up"] = self.plus.GetValue()
		result["down"] = self.minus.GetValue()
		return result

class RewardDialog(BaseTaskDialog):
	type = "reward"
	def __init__(self, parent, title="Add reward", data={}, **kwargs):
		super().__init__(parent, title=title, data=data, include_checklist_box=False, include_reminders_box=False, **kwargs)

	def setup_layout(self):
		super().setup_layout()
		value_label = wx.StaticText(self.panel, label="Cost in gold")
		self.value = wx.SpinCtrl(self.panel, min=0, max=100, initial=0)
		value_sizer = wx.BoxSizer(wx.HORIZONTAL)
		value_sizer.Add(value_label, 0, label_flags, 5)
		value_sizer.Add(self.value, 1, control_flags, 5)
		self.main_sizer.Add(value_sizer, 0, wx.EXPAND)

	def populate_fields(self, task_data):
		super().populate_fields(task_data)
		self.value.SetValue(task_data.get("value", 0))

	def get_task_result(self, include_id=False):
		result = super().get_task_result(include_id=include_id)
		result["value"] = self.value.GetValue()
		return result


class DailyDialog(BaseTaskDialog):
	type="daily"
	def __init__(self, parent, title="Add daily", data={}, **kwargs):
		super().__init__(parent, title=title, data=data, include_checklist_box=True, include_reminders_box=True, **kwargs)

	def setup_layout(self):
		super().setup_layout()
		pass # this is where we add frequency etc etc


class TodoDialog(BaseTaskDialog):
	type="todo"
	def __init__(self, parent, title="Add todo", data={}, **kwargs):
		super().__init__(parent, title=title, data=data, include_checklist_box=True, include_reminders_box=True, **kwargs)

	def setup_layout(self):
		super().setup_layout()
		due_label = wx.StaticText(self.panel, label="Due date")
		self.due_date = wx.adv.DatePickerCtrl(self.panel)
		due_date_sizer = wx.BoxSizer(wx.HORIZONTAL)
		due_date_sizer.Add(due_label, 0, label_flags, 5)
		due_date_sizer.Add(self.due_date, 0, control_flags, 5)
		self.main_sizer.Add(due_date_sizer, 0, wx.EXPAND)

	def populate_fields(self, task_data):
		super().populate_fields(task_data)
		pass  # todo


def start():
	#t = TaskTree(title="Habitica task viewer")
	#t.Show()
	#dlg = HabitDialog(None)
	#dlg.ShowModal()
	dlg = LoginDialog(None)
	result = dlg.ShowModal()
	dlg.Destroy()
	if result == True:
		user = habitica.get_user()
		if not user:
			app.exit()
		if user and user.needsCron:
			tasks = habitica.get_tasks()
			if not tasks:
				app.exit()
			incomplete = habitica.get_incomplete_dailies(tasks)
			if len(incomplete) > 0:
				dlg = CronDialog(None, tasks, incomplete)
				dlg.ShowModal()
				try:
					dlg.complete_selected()
				except Exception as exc:
					dialogs.error("Error", f"There was an error marking your dailys as complete: {exc}")
				dlg.Destroy()
		tree = TaskTreeFrame(None)
		app.app.SetTopWindow(tree)
		tree.Show()
	else:
		print("Could not login")
		app.exit()
	print("before")
	app.app.MainLoop()
