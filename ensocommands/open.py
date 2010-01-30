import gmenu
import os


directory = 1
entry = 2
def get_sub_items(node):
    sub = []
    for item in node.contents:
        if item.get_type() == directory:
            sub += get_sub_items(item)
        else:
            if item.get_type() == entry and not item.is_excluded: 
                sub += [item]
    return sub

def get_items():
    m = gmenu.lookup_tree(os.path.expandvars('~/.config/menus/applications.menu'))
    return get_sub_items(m.root)
    

def Command(CommandManager):
    
    def __init__(self):
        items = get_items()
        for item in items:
            pass
        ensoapi.display_message(str(items))



def cmd_application(ensoapi, new_command):
  "Run applications in the menu"
  sel = ensoapi.get_selection().get("text", "")
  if not sel:
    ensoapi.display_message("No selection!")
    return
  cmd_folder = ensoapi.get_enso_commands_folder()
  learned_commands = os.path.join(cmd_folder, "learned_commands.py")
  write_os = False
  if not os.path.exists(learned_commands): write_os = True
  fp = open(learned_commands,"a")
  if write_os: fp.write("import os\n")
  fp.write("def cmd_%s(ensoapi): os.system('gnome-open %s')\n" % (new_command.replace(" ","_"),sel))
  fp.close()
  ensoapi.display_message("%s is now a command" % new_command)
