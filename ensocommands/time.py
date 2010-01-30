import time

def cmd_time(ensoapi):
  "Shows the current time"
  ensoapi.display_message(time.asctime())

