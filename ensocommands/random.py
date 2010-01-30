import re, os



def cmd_install(ensoapi):
  seldict = ensoapi.get_selection()
  text = seldict.get("text", "").strip()
  lines = text.split("\n")
  ensoapi.display_message(lines)
  return
  if len(lines) < 3:
    msg = "There was no command to install!"
    ensoapi.display_message(msg)
    ensoapi.set_selection({
        "text":"Enso: %s" % msg
    })
    return
  while lines[0].strip() == "": 
    lines.pop(0)
  if lines[0].strip() != "# Enso command file":
    msg = "There was no command to install!"
    ensoapi.display_message(msg)
    ensoapi.set_selection({
        "text":"Enso: %s" % msg
    })
    return
  command_file_name = re.sub("^\s*#\s*","",lines[1].strip())
  if not command_file_name.endswith(".py"):
    msg = "Couldn't install this command %s" % command_file_name
    ensoapi.display_message(msg)
    ensoapi.set_selection({
        "text":"Enso: %s" % msg
    })
    return
  cmd_folder = ensoapi.get_enso_commands_folder()
  command_file_path = os.path.join(cmd_folder, command_file_name)
  shortname = os.path.splitext(command_file_name)[0]
  if os.path.exists(command_file_path):
    msg = "You already have a command named %s" % shortname
    ensoapi.display_message(msg)
    ensoapi.set_selection({
        "text":"Enso: %s" % msg
    })
    return
  installed_commands = [x['cmdName'] for x in ensoapi.get_commands_from_text(text)]
  if len(installed_commands) == 1:
    install_message = "%s is now a command" % installed_commands[0]
  else:
    install_message = "%s are now commands" % ", ".join(installed_commands)
  fp = open(command_file_path, "w")
  fp.write(text)
  fp.close()
  ensoapi.display_message(install_message)
  ensoapi.set_selection({
      "text":"Enso: %s" % install_message
  })

def cmd_footnote(ensoapi):
  "Wrap text in my in-HTML footnote style"
  seldict = ensoapi.get_selection()
  text = seldict.get("text", "")
  html = seldict.get("html", text)
  if not text:
    ensoapi.display_message("No selection!")
  else:
    result = '<span style="color:red" title="%s">*</span>' % html
    ensoapi.set_selection({
      "text":result
    })



def cmd_echo(ensoapi):
  "Displays the current selection dictionary"
  sel = ensoapi.get_selection()
  ensoapi.display_message(str(sel))
  

def cmd_learn_as(ensoapi, new_command):
  "Remember current selection as a command"
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


