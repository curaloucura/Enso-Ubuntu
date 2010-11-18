# Author : Pavel Vitis "blackdaemon"
# Email  : blackdaemon@seznam.cz
#
# Copyright (c) 2010, Pavel Vitis <blackdaemon@seznam.cz>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of Enso nor the names of its contributors may
#       be used to endorse or promote products derived from this
#       software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# AUTHORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

# Future imports
from __future__ import with_statement

# Imports
import os
import re
import logging
import unicodedata
from itertools import chain

# PyWin32 imports
import ctypes
import win32api
import win32con
import winerror
from ctypes import wintypes
import pythoncom
from xml.sax.saxutils import escape as xml_escape

from win32com.shell import shell, shellcon


from enso.contrib.open import interfaces
from enso.contrib.open.shortcuts import * #IGNORE:W0401
from enso.contrib.open.platform.win32 import win_shortcuts
from enso.contrib.open.platform.win32 import utils
from enso.contrib.open.interfaces import AbstractOpenCommand, ShortcutAlreadyExistsError
from enso.contrib.scriptotron.ensoapi import EnsoApi

# This import should be changed as soon as registry support gets merged into
# the working branch
from enso.contrib.open.platform.win32 import registry


logger = logging.getLogger(__name__)

EXECUTABLE_EXTS = ['.exe', '.com', '.cmd', '.bat', '.py', '.pyw']
EXECUTABLE_EXTS.extend(
    [ext for ext
        in os.environ['PATHEXT'].lower().split(os.pathsep)
        if ext not in EXECUTABLE_EXTS])


ensoapi = EnsoApi()


def get_special_folder_path(folder_id):
    return unicode(
        shell.SHGetPathFromIDList(
            shell.SHGetFolderLocation(0, folder_id)
        )
    )

LEARN_AS_DIR = os.path.join(
    get_special_folder_path(shellcon.CSIDL_PERSONAL),
    u"Enso's Learn As Open Commands")

# Check if Learn-as dir exist and create it if not
if (not os.path.isdir(LEARN_AS_DIR)):
    os.makedirs(LEARN_AS_DIR)

RECYCLE_BIN_LINK = os.path.join(LEARN_AS_DIR, "recycle bin.lnk")

# Shortcuts in Start-Menu/Quick-Links that are ignored
startmenu_ignored_links = re.compile(
    r"(^uninstall|^read ?me|^faq|^f\.a\.q|^help|^copying$|^authors$|^website$|"
    "^license$|^changelog$|^release ?notes$)",
    re.IGNORECASE)




def display_xml_message(msg):
    import enso.messages
    enso.messages.displayMessage("<p>%s</p>" % msg)


# TODO: Refactor get_file_type, it's too complex, solves too many cases, ...
# ...is unreliable, split url/file detection: url should be detected outside of this
def get_file_type(target):
    # Stripping \0 is needed for the text copied from Lotus Notes
    target = target.strip(" \t\r\n\0")
    # Before deciding whether to examine given text using URL regular expressions
    # do some simple checks for the probability that the text represents a file path
    if not os.path.exists(target):
        if interfaces.is_url(target):
            return SHORTCUT_TYPE_URL

    file_path = target
    file_name, file_ext = os.path.splitext(file_path)
    file_ext = file_ext.lower()

    if file_ext == ".url":
        return SHORTCUT_TYPE_URL

    if file_ext == ".lnk":
        sl = win_shortcuts.PyShellLink(file_path)
        file_path = sl.get_target()
        if file_path and os.path.exists(file_path):
            file_name, file_ext = os.path.splitext(file_path)
            file_ext = file_ext.lower()
        elif target.startswith("http"):
            return SHORTCUT_TYPE_URL
        else:
            return SHORTCUT_TYPE_DOCUMENT

    if os.path.isdir(file_path):
        return SHORTCUT_TYPE_FOLDER

    if (os.path.isfile(file_path) and ext in EXECUTABLE_EXTS):
        return SHORTCUT_TYPE_EXECUTABLE

    #TODO: Finish this
    #if ext in (".", ""):
    #    for ext in EXECUTABLE_EXTS:
    #        if os.path.isfile(os.path.extsep)
    return SHORTCUT_TYPE_DOCUMENT


def get_shortcuts_from_dir(directory, re_ignored = None):
    if not os.path.isdir(directory):
        return

    #shortcuts = []
    splitext = os.path.splitext
    pathjoin = os.path.join
    #total_files_processed = 0
    #really_processed = 0
    #import string
    for dirpath, _, filenames in os.walk(directory):
        #total_files_processed += len(filenames)
        """
        filenames = (
            (name, ext)
            for (name, ext)
            in map(splitext, filenames)
            if ext in (".lnk", ".url")
                and (re_ignored is None or not re_ignored.search(name))
        )
        """
        for filename in filenames:
            target = None
            name, ext = splitext(filename)
            ext = ext.lower()
            # rdp is remote-desktop shortcut
            if not ext in (".lnk", ".url", ".rdp"):
                continue
            if re_ignored and re_ignored.search(name):
                continue
            #print name, ext
            shortcut_type = SHORTCUT_TYPE_DOCUMENT
            #FIXME:Getting the path/URL should be done in the Shortcut object
            #doing all the wxtracting magic there
            if ext == ".lnk":
                shell_link = win_shortcuts.PyShellLink(pathjoin(dirpath, filename))
                #FIXME: Maybe extracting of path could be done lazily in the Shortcut object itself
                #bottom-line here is: we need to extract it to get the type
                #type could be also get lazily, but the advantage is then void
                target = shell_link.get_target()
                if target:
                    if os.path.isdir(target):
                        shortcut_type = SHORTCUT_TYPE_FOLDER
                    elif os.path.isfile(target):
                        shortcut_type = get_file_type(target)
                    elif target.startswith("http"):
                        shortcut_type = SHORTCUT_TYPE_URL
                else:
                    continue
            elif ext == ".url":
                url_link = win_shortcuts.PyInternetShortcut(pathjoin(dirpath, filename))
                target = url_link.get_target()
                shortcut_type = SHORTCUT_TYPE_URL
            elif ext == ".rdp":
                target = os.path.join(dirpath, filename)
                shortcut_type = SHORTCUT_TYPE_DOCUMENT

            #shortcuts.append((shortcut_type, name.lower(), os.path.join(dirpath, filename)))
            try:
                #old_name = name
                name = unicodedata.normalize('NFKD', unicode(name)).encode('ascii', 'ignore')
                #if name != old_name:
                #    print "NORMALIZED:", old_name, name
            except Exception, e: #IGNORE:W0703
                print e, name, dirpath
            else:
                try:
                    yield Shortcut(
                        name.lower(), shortcut_type, target, pathjoin(dirpath, filename))
                except AssertionError, e:
                    logging.error(e)
                #really_processed += 1
    #print "Total files to process:", total_files_processed, ", really processed:", really_processed
    #return shortcuts


def get_special_folders():
    #TODO:Use sublasses here (something like SpecialShortcut, or FixedShortcut)
    try:
        yield Shortcut(
                "desktop folder",
                SHORTCUT_TYPE_FOLDER,
                get_special_folder_path(shellcon.CSIDL_DESKTOPDIRECTORY)
            )
    except:
        pass #IGNORE:W0702

    try:
        yield Shortcut(
                "my documents folder",
                SHORTCUT_TYPE_FOLDER,
                get_special_folder_path(shellcon.CSIDL_PERSONAL)
            )
    except:
        pass #IGNORE:W0702

    try:
        yield Shortcut(
                "my pictures folder",
                SHORTCUT_TYPE_FOLDER,
                get_special_folder_path(shellcon.CSIDL_MYPICTURES)
            )
    except:
        pass #IGNORE:W0702

    try:
        yield Shortcut(
                "my videos folder",
                SHORTCUT_TYPE_FOLDER,
                get_special_folder_path(shellcon.CSIDL_MYVIDEO)
            )
    except:
        pass #IGNORE:W0702

    try:
        yield Shortcut(
                "my music folder",
                SHORTCUT_TYPE_FOLDER,
                get_special_folder_path(shellcon.CSIDL_MYMUSIC)
            )
    except:
        pass #IGNORE:W0702

    if not os.path.isfile(RECYCLE_BIN_LINK):
        recycle_shortcut = pythoncom.CoCreateInstance(
            shell.CLSID_ShellLink, None,
            pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
        )
        recycle_shortcut.SetPath("")
        recycle_shortcut.SetWorkingDirectory("")
        recycle_shortcut.SetIDList(['\x1f\x00@\xf0_d\x81P\x1b\x10\x9f\x08\x00\xaa\x00/\x95N'])
        recycle_shortcut.QueryInterface( pythoncom.IID_IPersistFile ).Save(
            RECYCLE_BIN_LINK, 0 )
    yield Shortcut(
            "recycle bin",
            SHORTCUT_TYPE_FOLDER,
            RECYCLE_BIN_LINK
            )


def get_control_panel_applets():
    if utils.platform_windows_vista() or utils.platform_windows_7():
        from enso.contrib.open.platform.win32 import control_panel_vista_win7
        return control_panel_vista_win7.get_control_panel_applets()
    else:
        from enso.contrib.open.platform.win32 import control_panel_2000_xp
        return control_panel_2000_xp.get_control_panel_applets()


def reload_shortcuts_map():
    desktop_dir = get_special_folder_path(shellcon.CSIDL_DESKTOPDIRECTORY)
    quick_launch_dir = os.path.join(
        get_special_folder_path(shellcon.CSIDL_APPDATA),
        "Microsoft",
        "Internet Explorer",
        "Quick Launch")
    start_menu_dir = get_special_folder_path(shellcon.CSIDL_STARTMENU)
    common_start_menu_dir = get_special_folder_path(shellcon.CSIDL_COMMON_STARTMENU)

    shortcuts = chain(
        get_shortcuts_from_dir(desktop_dir),
        get_shortcuts_from_dir(quick_launch_dir, startmenu_ignored_links),
        get_shortcuts_from_dir(start_menu_dir, startmenu_ignored_links),
        get_shortcuts_from_dir(common_start_menu_dir, startmenu_ignored_links),
        iter(get_control_panel_applets()),
        get_special_folders(),
        get_shortcuts_from_dir(LEARN_AS_DIR)
    )

    return ShortcutsDict(((s.name, s) for s in shortcuts))




class OpenCommandImpl( AbstractOpenCommand ):

    def __init__(self):
        super(OpenCommandImpl, self).__init__()

    def _reload_shortcuts(self):
        return reload_shortcuts_map()

    def _is_application(self, shortcut):
        return shortcut.type == SHORTCUT_TYPE_EXECUTABLE

    def _save_shortcut(self, name, target):
        # Shortcut actual file goes to "Enso Learn As" directory. This is typically
        # different for each platform.
        shortcut_file_path = os.path.join(self._get_learn_as_dir(), name)

        if self._is_url(target):
            shortcut_file_path = shortcut_file_path + ".url"
            if os.path.isfile(shortcut_file_path):
                raise ShortcutAlreadyExistsError()
            s = win_shortcuts.PyInternetShortcut()
            s.set_url(target)
            s.save(shortcut_file_path)
        else:
            shortcut_file_path = shortcut_file_path + ".lnk"
            if os.path.isfile(shortcut_file_path):
                raise ShortcutAlreadyExistsError()
            s = win_shortcuts.PyShellLink()
            s.set_path(target)
            s.set_working_dir(os.path.dirname(target))
            s.set_icon_location(target, 0)
            s.save(shortcut_file_path)
        return Shortcut(
            name, self._get_shortcut_type(target), target, shortcut_file_path)

    def _remove_shortcut(self, shortcut):
        assert 0 == shortcut.flags & SHORTCUT_FLAG_CANTUNLEARN
        assert os.path.isfile(shortcut.shortcut_filename)
        os.remove(shortcut.shortcut_filename)

    def _get_shortcut_type(self, target):
        return get_file_type(target)


    def _run_shortcut(self, shortcut):
        try:
            if shortcut.type == SHORTCUT_TYPE_CONTROL_PANEL:
                target = shortcut.target
                logger.info("Executing '%s'", target)
                # os.startfile does not work with .cpl files,
                # ShellExecute have to be used.
                #FIXME: Replace with regexp, there will be probably more such things
                if target.startswith("mshelp://") or target.startswith("ms-help://"):
                    params = None
                    work_dir = None
                else:
                    target, params = utils.splitcmdline(target)
                    target = os.path.normpath(utils.expand_win_path_variables(target))
                    params = " ".join(
                        (
                            ('"%s"' % p if ' ' in p else p) for p in
                                (utils.expand_win_path_variables(p) for p in params)
                        )
                    )
                    work_dir = os.path.dirname(target)
                try:
                    _ = win32api.ShellExecute(
                        0,
                        'open',
                        target,
                        params,
                        work_dir,
                        win32con.SW_SHOWDEFAULT)
                except Exception, e: #IGNORE:W0703
                    logger.error(e)
                    try:
                        os.startfile(target)
                    except WindowsError, e:
                        logger.error("%d: %s", e.errno, e)
            else:
                target = os.path.normpath(utils.expand_win_path_variables(shortcut.shortcut_filename))
                logger.info("Executing '%s'", target)

                try:
                    os.startfile(target)
                except WindowsError, e:
                    #TODO: Why am I getting 'bad command' error on Win7 instead of 'not found' error?
                    if e.errno in (winerror.ERROR_FILE_NOT_FOUND, winerror.ERROR_BAD_COMMAND):
                        ensoapi.display_message(u"File has not been found. Please adjust the shortcut properties.")
                        logger.error("%d: %s", e.errno, e)
                        try:
                            _ = win32api.ShellExecute(
                                0,
                                'properties',
                                target,
                                None,
                                None,
                                win32con.SW_SHOWDEFAULT)
                        except Exception, e: #IGNORE:W0703
                            logger.error(e)
                    elif e.errno == winerror.ERROR_NO_ASSOCIATION:
                        # No application is associated with the specified file.
                        # Open system "Open with..." dialog:
                        try:
                            _ = win32api.ShellExecute(
                                0,
                                'open',
                                "rundll32.exe",
                                "shell32.dll,OpenAs_RunDLL %s" % target,
                                None,
                                win32con.SW_SHOWDEFAULT)
                        except Exception, e: #IGNORE:W0703
                            logger.error(e)
                    else:
                        logger.error("%d: %s", e.errno, e)
            return True
        except Exception, e: #IGNORE:W0703
            logger.error(e)
            return False

    def _open_with_shortcut(self, shortcut, targets):
        # User did not select any application. Offer system "Open with..." dialog
        if not shortcut:
            for file_name in targets:
                print file_name
                try:
                    _ = win32api.ShellExecute(
                        0,
                        'open',
                        "rundll32.exe",
                        "shell32.dll,OpenAs_RunDLL %s" % file_name,
                        None,
                        win32con.SW_SHOWDEFAULT)
                except Exception, e: #IGNORE:W0703
                    logger.error(e)
            return

        executable = utils.expand_win_path_variables(shortcut.target)
        workdir = os.path.dirname(executable)
        _, ext = os.path.splitext(executable)
        # If it is a shortcut, extract the executable info
        # for to be able to pass the command-line parameters
        if ext.lower() == ".lnk":
            sl = win_shortcuts.PyShellLink(executable)
            executable = sl.get_target()
            workdir = sl.get_working_dir()
            if not workdir:
                workdir = os.path.dirname(executable)
        #print executable, workdir

        params = u" ".join((u'"%s"' % file_name for file_name in targets))
        #print params

        try:
            win32api.ShellExecute(
                0,
                'open',
                "\"" + executable + "\"",
                params,
                workdir,
                win32con.SW_SHOWDEFAULT)
        except Exception, e: #IGNORE:W0703
            logger.error(e)

    def _get_learn_as_dir(self):
        return LEARN_AS_DIR


# vim:set ff=unix tabstop=4 shiftwidth=4 expandtab: