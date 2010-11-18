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

import os
import re
from xml.sax.saxutils import escape as xml_escape

from enso.contrib.open import utils
from enso.contrib.open.shortcuts import ShortcutsDict


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

_RE_URL_FINDERS = [
    re.compile(r"""
        (   # hostname / IP address
            [0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}     # IP address
            |    # or
            (
                ((news|telnet|nttp|file|http|ftp|https)://)    # Protocol
                |
                (www|ftp)[-A-Za-z0-9]*\.
            )[-A-Za-z0-9\.]+                                   # Rest of hostname / IP
        )
        (:[0-9]*)?/[-A-Za-z0-9_\$\.\+\!\*\(\),;:@&=\?/~\#\%]*[^]'\.}>\),\\"]"
        """, re.VERBOSE),
    re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?"),
    re.compile("(~/|/|\\./)([-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]|\\\\)+"),
    re.compile(r"(mailto:)?[-_\.\d\w]+@[-_\.\d\w]+", re.IGNORECASE),
]


# ----------------------------------------------------------------------------
# Decorators
# ----------------------------------------------------------------------------

def abstractMethod(func):
    """ Decorator to mark abstract functions """
    def func_wrap(*args): #IGNORE:W0613
        raise NotImplementedError(
            "Abstract method '%s' must be overriden in subclass."
            % func.__name__)
    return func_wrap


# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------

def display_xml_message(msg):
    import enso.messages
    enso.messages.displayMessage("<p>%s</p>" % msg)

def is_url(text):
    """
    >>> is_url("mailto:aks12kjACd.ka-0a_0@alsksk.com")
    True
    >>> is_url("<aks12kjACd.ka-0a_0@alsksk.com>")
    True
    """
    for urltest in _RE_URL_FINDERS:
        if urltest.search(text, re.I):
            return True

    return False

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------

class ShortcutAlreadyExistsError( Exception ):
    pass


class IOpenCommand( object ):
    """ Open command interface """

    def __init__(self):
        pass

    def get_shortcuts(self):
        """ Return shortcuts dictinary
        dictionary of Shortcut objects
        """
        raise NotImplementedError()

    def is_application(self, shortcut_name):
        """
        Returns True if the shortcut represents runnable file that could
        open another files.
        This is used to identify correct shortcuts for 'open with' command.
        """
        raise NotImplementedError()

    def add_shortcut(self, shortcut_name, target):
        """
        Register shortcut.
        """
        raise NotImplementedError()

    def remove_shortcut(self, shortcut_name):
        """
        Unregister shortcut.
        This method also implements undo.
        """
        raise NotImplementedError()

    def undo_remove_shortcut(self):
        """
        Undo of last unregistering shortcut.
        """
        raise NotImplementedError()

    def run_shortcut(self, shortcut_name):
        """
        Run the program/document represented by the shortcut
        """
        raise NotImplementedError()

    def open_with_shortcut(self, shortcut_name, targets):
        """
        Open files with the application represented by the shortcut.
        """
        raise NotImplementedError()



class AbstractOpenCommand( IOpenCommand ):


    def __init__(self):
        super(AbstractOpenCommand, self).__init__()
        with utils.Timer("Reloading shortcuts dict"):
            shortcuts = self._reload_shortcuts()
            if not isinstance(shortcuts, ShortcutsDict):
                shortcuts = ShortcutsDict(shortcuts)
            self.shortcuts_map = shortcuts
        self._unlearn_open_undo = []

    def get_shortcuts(self):
        # Lazy initialization
        if self.shortcuts_map is None:
            with utils.Timer("Reloading shortcuts dict"):
                shortcuts = self._reload_shortcuts()
                if not isinstance(shortcuts, ShortcutsDict):
                    shortcuts = ShortcutsDict(shortcuts)
                self.shortcuts_map = shortcuts
        return self.shortcuts_map

    def is_application(self, shortcut_name):
        return self._is_application(
            self.shortcuts_map[shortcut_name])

    def add_shortcut(self, shortcut_name, target):
        # Cleanup name
        shortcut_name = shortcut_name.replace(":", "").replace("?", "").replace("\\", "")

        try:
            shortcut = self._save_shortcut(
                shortcut_name, target)
        except ShortcutAlreadyExistsError:
            return None

        self.shortcuts_map[shortcut_name] = shortcut

        return shortcut

    def remove_shortcut(self, shortcut_name):
        shortcut = self.shortcuts_map[shortcut_name]
        self._unlearn_open_undo.append(shortcut)
        self._remove_shortcut(shortcut)
        del self.shortcuts_map[shortcut_name]

    def undo_remove_shortcut(self):
        if len(self._unlearn_open_undo) > 0:
            shortcut = self._unlearn_open_undo.pop()
            return self.add_shortcut(shortcut.name, shortcut.target)
        else:
            return None

    def run_shortcut(self, shortcut_name):
        self._run_shortcut(self.shortcuts_map[shortcut_name])

    def open_with_shortcut(self, shortcut_name, targets):
        # User did not select any application. Offer system "Open with..." dialog
        if not shortcut_name:
            self._open_with_shortcut(None, targets)
            return

        display_xml_message(u"Opening selected %s with <command>%s</command>..."
            % ("files" if len(targets) > 1 else "file" if os.path.isfile(targets[0]) else "folder",
                xml_escape(shortcut_name)))

        self._open_with_shortcut(self.shortcuts_map[shortcut_name], targets)
        #print file, application


    def _is_url(self, text):
        return is_url(text)


    @abstractMethod
    def _reload_shortcuts(self):
        """
        Return dictionary of application/document shortcuts.
        Items in the dictionary must be of shortcuts.Shortcut type.

        Example:

            shortcuts_dict = shortcuts.ShortcutsDictionary()
            shortcuts_dict['internet explorer'] = shortcuts.Shortcut(
                'internet explorer',
                shortcuts.SHORTCUT_TYPE_EXECUTABLE,
                'iexplore.exe')
            return shortcuts_dict
        """
        pass

    @abstractMethod
    def _get_learn_as_dir(self):
        """
        Return directory for storing of "Enso learn as" shortcuts.
        Implement this in platform specific class.
        """
        pass

    @abstractMethod
    def _save_shortcut(self, name, target):
        """
        Return directory for storing of "Enso learn as" shortcuts.
        Implement this in platform specific class.
        """
        pass

    @abstractMethod
    def _remove_shortcut(self, shortcut):
        pass

    @abstractMethod
    def _run_shortcut(self, shortcut):
        """
        Return directory for storing of "Enso learn as" shortcuts.
        Implement this in platform specific class.
        """
        pass

    @abstractMethod
    def _get_shortcut_type(self, file_name):
        """
        Return directory for storing of "Enso learn as" shortcuts.
        Implement this in platform specific class.
        """
        pass

    @abstractMethod
    def _is_application(self, shortcut):
        """
        Return directory for storing of "Enso learn as" shortcuts.
        Implement this in platform specific class.
        """
        pass

    @abstractMethod
    def _open_with_shortcut(self, name, file_names):
        """
        Return directory for storing of "Enso learn as" shortcuts.
        Implement this in platform specific class.
        """
        pass


# vim:set ff=unix tabstop=4 shiftwidth=4 expandtab:
