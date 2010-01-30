import dbus, wnck, gtk, time

class IMBuddies(object):
  """Opens up an IM conversation window via Pidgin to the name specified
  
  Find a person in your Pidgin contacts and open up a conversation window
  to talk to them."""  
  def __init__(self):
    self.buddies = {}
    self.valid_args = []
  
  def on_quasimode_start(self):
    bus = dbus.SessionBus()
    try:
      obj = bus.get_object('im.pidgin.purple.PurpleService', 
        '/im/pidgin/purple/PurpleObject')
    except:
      self.pidgin_running = False
      return
    self.pidgin_running = True
    self.purple = dbus.Interface(obj, 'im.pidgin.purple.PurpleInterface')

    # Build a list of buddies and check the entered name against the list
    # Prefer a buddy's alias to their screen name; prefer exact matches to
    # substring matches
    
    import time
    for ac in self.purple.PurpleAccountsGetAllActive():
      acname = self.purple.PurpleAccountGetProtocolName(ac)
      for buddy in self.purple.PurpleFindBuddies(ac,""):
        base = 0
        online = self.purple.PurpleBuddyIsOnline(buddy)
        if online:
          screenname = self.purple.PurpleBuddyGetName(buddy).lower()
          alias = self.purple.PurpleBuddyGetAlias(buddy)
          self.buddies["%s (%s) (%s)" % (alias, screenname, acname)] = ac
        yield # give up control so as to not hang
        self.valid_args = self.buddies.keys()
  
  def __call__(self, ensoapi, buddy):
    if not self.pidgin_running:
      ensoapi.display_message("Pidgin must be running to chat to people")
      return
    ac = self.buddies[buddy]
    conv = self.purple.PurpleConversationNew(1, ac, buddy)
    self.purple.PurpleConversationPresent(conv)
    # raise the window
    screen = wnck.screen_get_default()
    while gtk.events_pending():
      gtk.main_iteration()
    for window in screen.get_windows():
      for window in screen.get_windows():
        if window.get_class_group().get_name() == "Pidgin":
          window.activate(int(time.time()))

cmd_im = IMBuddies()

def pidgin_status(status):
  bus = dbus.SessionBus()
  pidgin = bus.get_object('im.pidgin.purple.PurpleService', 
    '/im/pidgin/purple/PurpleObject')
  found_stati = [x for x in pidgin.PurpleSavedstatusesGetAll()
           if pidgin.PurpleSavedstatusGetTitle(x) == status]
  if found_stati:
    pidgin.PurpleSavedstatusActivate(found_stati[0])

def cmd_offline(ensoapi):
  "Set Pidgin's status to offline"
  pidgin_status("Offline")

def cmd_online(ensoapi):
  "Set Pidgin's status to online"
  pidgin_status("Available")

