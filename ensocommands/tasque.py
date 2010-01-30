import dbus

def cmd_task(ensoapi, task):
  """Creates a task in Tasque"""
  bus = dbus.SessionBus()
  tasque = bus.get_object("org.gnome.Tasque", "/org/gnome/Tasque/RemoteControl")
  categories = list(tasque.GetCategoryNames())
  for c in categories:
    if task.lower().startswith(c.lower() + " "):
      tasktext = task[len(c)+1:]
      tasque.CreateTask(c, tasktext, False)
      return
  tasque.CreateTask("Inbox", task, False)


