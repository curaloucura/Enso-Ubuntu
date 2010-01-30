import dbus

def banshee(cmd, *args):
  bus = dbus.SessionBus()
  bansheeEngine = bus.get_object("org.bansheeproject.Banshee", 
    "/org/bansheeproject/Banshee/PlayerEngine")
  try:
    getattr(bansheeEngine,cmd)(*args)
  except:
    bansheeController = bus.get_object("org.bansheeproject.Banshee", 
      "/org/bansheeproject/Banshee/PlaybackController")
    try:
      getattr(bansheeController,cmd)(*args)
    except:
      pass
    
def cmd_play(ensoapi):
  """Start Banshee playing"""
  banshee("Play")

def cmd_pause(ensoapi):
  """Stop Banshee playing"""
  banshee("Pause")

def cmd_next(ensoapi):
  """Skip to next track in Banshee"""
  banshee("Next", False)

def cmd_previous(ensoapi):
  """Skip to previous track in Banshee"""
  banshee("Previous", False)

