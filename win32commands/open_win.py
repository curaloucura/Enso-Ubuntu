from win32com.shell import shell, shellcon
import os
import glob
import operator
import re

import enso.messages
import logging

my_documents_dir = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, 0, 0)
LEARN_AS_DIR = os.path.join(my_documents_dir, u"Enso's Learn As Open Commands")

# Check if Learn-as dir exist and create it if not
if (not os.path.isdir(LEARN_AS_DIR)):
    os.makedirs(LEARN_AS_DIR)


def displayMessage(msg):
    enso.messages.displayMessage("<p>%s</p>" % msg)


def get_shortcuts():
    return [operator.itemgetter(0)(os.path.splitext(x))
        for x in os.listdir(LEARN_AS_DIR)
        if x.lower().endswith('.lnk') or x.lower().endswith('.url')]

ignored = re.compile("(uninstall|read ?me|faq|f.a.q|help)", re.IGNORECASE)

def get_desktop():
    desktop_dir = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOPDIRECTORY, 0, 0)
    for i in os.walk(desktop_dir):
        for file in glob.iglob(os.path.join(i[0], "*.lnk")):
            #print file
            pass
        for file in glob.iglob(os.path.join(i[0], "*.url")):
            #print file
            pass
    quick_launch_dir = os.path.join(shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0), "Microsoft", "Internet Explorer", "Quick Launch")
    for i in os.walk(quick_launch_dir):
        for file in glob.iglob(os.path.join(i[0], "*.lnk")):
            #print file
            pass
        for file in glob.iglob(os.path.join(i[0], "*.url")):
            #print file
            pass
    start_menu_dir = shell.SHGetFolderPath(0, shellcon.CSIDL_STARTMENU, 0, 0)
    for i in os.walk(start_menu_dir):
        for file in glob.iglob(os.path.join(i[0], "*.lnk")):
            if not ignored.search(file):
                #print file
                pass
        for file in glob.iglob(os.path.join(i[0], "*.url")):
            if not ignored.search(file):
                #print file
                pass


shortcuts = get_shortcuts()
get_desktop()


def cmd_open(ensoapi, name):
    """ Open learned command """
    import win32process
    import win32con

    displayMessage(u"Opening <command>%s</command>" % name)

    try:
        file = os.path.normpath(os.path.join(LEARN_AS_DIR, name))
        if os.path.isfile(file + ".lnk"):
            file += ".lnk"
        else:
            file += ".url"
        logging.info("Executing '%s'" % file)

        os.startfile(file)

        return True
    except Exception, e:
        logging.error(e)
        return False


cmd_open.valid_args = shortcuts


def is_url(text):
    urlfinders = [
        re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?/[-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]*[^]'\\.}>\\),\\\"]"),
        re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?"),
        re.compile("(~/|/|\\./)([-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]|\\\\)+"),
        re.compile("'\\<((mailto:)|)[-A-Za-z0-9\\.]+@[-A-Za-z0-9\\.]+"),
    ]

    for urltest in urlfinders:
        if urltest.search(text, re.I):
            return True

    return False


def cmd_learn_as_open(ensoapi, name):
    """ Learn to open a document or application as {name} """
    if name is None:
        displayMessage(u"You must provide name")
        return
    seldict = ensoapi.get_selection()
    if seldict.get('files'):
        file = seldict['files'][0]
    elif seldict.get('text'):
        file = seldict['text'].strip()

    if not os.path.isfile(file) and not os.path.isdir(file) and not is_url(file):
        displayMessage(
            u"Selection represents no existing file, folder or URL.")
        return

    file_name = name.replace(":", "").replace("?", "").replace("\\", "")
    file_path = os.path.join(LEARN_AS_DIR, file_name)

    if os.path.isfile(file_path + ".url") or os.path.isfile(file_path + ".lnk"):
        displayMessage(
            u"<command>open %s</command> already exists. Please choose another name."
            % name)
        return

    from win32com.shell import shell
    import pythoncom

    if is_url(file):
        shortcut = pythoncom.CoCreateInstance (
            shell.CLSID_InternetShortcut,
            None,
            pythoncom.CLSCTX_INPROC_SERVER,
            shell.IID_IUniformResourceLocator
        )
    
        shortcut.SetURL(file)
        shortcut.QueryInterface( pythoncom.IID_IPersistFile ).Save(
            file_path + ".url", 0 )
    else:
        shortcut = pythoncom.CoCreateInstance(
            shell.CLSID_ShellLink, None,
            pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
        )

        shortcut.SetPath(file)
        shortcut.SetWorkingDirectory(os.path.dirname(file))
        shortcut.SetIconLocation(file, 0)

        shortcut.QueryInterface( pythoncom.IID_IPersistFile ).Save(
            file_path + ".lnk", 0 )

    shortcuts = get_shortcuts()
    cmd_open.valid_args = shortcuts
    cmd_unlearn_open.valid_args = shortcuts

    displayMessage(u"<command>open %s</command> is now a command" % name)


def cmd_unlearn_open(ensoapi, name):
    u""" Unlearn <command>open {name}</command> command """
    import os
    os.remove(os.path.join(LEARN_AS_DIR, name + ".lnk"))
    shortcuts = get_shortcuts()
    cmd_open.valid_args = shortcuts
    cmd_unlearn_open.valid_args = shortcuts
    displayMessage(u"Unlearned <command>open %s</command>" % name)


cmd_unlearn_open.valid_args = shortcuts

# vi:set ff=unix tabstop=4 shiftwidth=4 expandtab:
