import wnck, gmenu, os, gtk

def cmd_close(ensoapi):
  """Close current window"""
  s = wnck.screen_get_default()
  s.force_update()
  win = s.get_active_window()
  if win: win.close(0)

class WindowSwitcher(object):
  """Switches to a window by name
  
  Looks through the list of open windows and switches to the first one that
  matches what you entered."""

  def __init__(self): self.valid_args = []
  def on_quasimode_start(self):
    self.screen = wnck.screen_get_default()
    self.screen.force_update()
    while gtk.events_pending():
      gtk.main_iteration()
    self.valid_args = [w.get_name() for w in self.screen.get_windows()]

  def __call__(self, ensoapi, name):
    windows = [w for w in self.screen.get_windows() if w.get_name() == name]
    windows[0].activate(0)

cmd_show = WindowSwitcher()


def traverse_gmenu(d):
  """For each item in this gmenu tree, if it's an entry, return its name from 
     .desktop and its executable (so gedit is returned as "Text Editor gedit"
     so that you can search for either name or executable)."""
  if d.get_type() == gmenu.TYPE_ENTRY:
    yield {"search": "%s (%s)" % (d.get_name(), os.path.split(d.get_exec())[1]), 
           "exe": d.get_exec()}
  elif d.get_type() == gmenu.TYPE_DIRECTORY:
    for item in d.get_contents():
      for x in traverse_gmenu(item):
        yield x
  else:
    return

class Application_Launcher(object):
  """Starts an application by name
  
  Enter part of an application's name and start it up"""

  def __init__(self): self.valid_args = []
  def on_quasimode_start(self):
    tree = gmenu.lookup_tree('applications.menu' 
      ,gmenu.FLAGS_SHOW_EMPTY|gmenu.FLAGS_INCLUDE_EXCLUDED|gmenu.FLAGS_INCLUDE_NODISPLAY) 
    self.possibles = []
    for i in traverse_gmenu(tree.root):
      self.possibles.append(i)
      yield
    self.valid_args = [x["search"] for x in self.possibles]

  def __call__(self, ensoapi, name):
    
    matches = [x for x in self.possibles if x["search"] == name]
    os.system(matches[0]["exe"].replace("%U","").replace("%u","") + " &")
    ensoapi.display_message("Opening %s" % name)

cmd_open = Application_Launcher()

def cmd_lock(ensoapi):
  """Lock the screen
  
  Lock the screen"""
  os.system("gnome-screensaver-command --lock &")

class FolderOpener(object):
  """Opens a folder from your Gtk bookmarks by name
  
  Opens a folder from your Gtk bookmarks by name"""
  def __init__(self): 
    self.valid_args = []
  def on_quasimode_start(self):
    fp = open(os.path.expanduser("~/.gtk-bookmarks"))
    self.valid_args = []
    self.possibles = {}
    for line in fp:
      bits = line.strip().split(" ", 1)
      if len(bits) == 1:
        # grab the last non-blank bit between / characters
        # this caters for file:///home/foo/bar/baz -> baz and trash:/// -> trash:
        parts = bits[0].split("/")
        parts.reverse()
        short = [x for x in parts if x][0]
      else:
        short = bits[1]
      self.valid_args.append(short)
      self.possibles[short.lower()] = bits[0]
    fp.close()
    print self.possibles
  def __call__(self, ensoapi, bookmark):
    os.system("nautilus %s" % self.possibles[bookmark.lower()])

cmd_folder = FolderOpener()

