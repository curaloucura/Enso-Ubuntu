"Various text manipulation utilities"

import re

def cmd_replace(ensoapi, old, new):
  "Replace old with new in the selected text"
  seldict = ensoapi.get_selection()
  text = seldict.get("text", "")
  if not text:
    ensoapi.display_message("No selection!")
  else:
    result = text.replace(old, new)
    ensoapi.set_selection({
      "text":result
    })

def cmd_word_count(ensoapi):
  "Display the number of words"
  sel = ensoapi.get_selection().get("text", "")
  if not sel:
    ensoapi.display_message("No selection!")
    return
  ensoapi.display_message(len(re.findall(r"\w\b",sel)))

def cmd_character_count(ensoapi):
  "Display the number of characters"
  sel = ensoapi.get_selection().get("text", "")
  if not sel:
    ensoapi.display_message("No selection!")
    return
  ensoapi.display_message(len(sel))


