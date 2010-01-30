import dbus

def cmd_todo(ensoapi, thing_to_do):
  """Creates or appends to a todo note in Tomboy"""
  bus = dbus.SessionBus()
  tomboy = bus.get_object("org.gnome.Tomboy", "/org/gnome/Tomboy/RemoteControl")
  note = tomboy.FindNote("To Do")
  if note:
    contents = tomboy.GetNoteContents(note)
  else:
    note = tomboy.CreateNamedNote("To Do")
    contents = "To Do\n"
  if contents[-1] != "\n":
    contents += "\n" 
  contents += thing_to_do + "\n"
  tomboy.SetNoteContents(note, contents)
  tomboy.DisplayNote(note)

