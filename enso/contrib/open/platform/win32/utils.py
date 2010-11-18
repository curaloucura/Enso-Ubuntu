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

import re
import os
import win32api


def expand_win_path_variables(file_path):
    re_env = re.compile(r'%\w+%')

    def expander(mo):
        return os.environ.get(mo.group()[1:-1], 'UNKNOWN')

    return os.path.expandvars(re_env.sub(expander, file_path))


def platform_windows_vista():
    #FIXME: Replace with proper test as soon as this issue is fixed in Python dist
    #See http://bugs.python.org/issue7863
    maj, min, buildno, plat, csd = win32api.GetVersionEx()
    return maj == 6 and min == 0


def platform_windows_7():
    #FIXME: Replace with proper test as soon as this issue is fixed in Python dist
    #See http://bugs.python.org/issue7863
    maj, min, buildno, plat, csd = win32api.GetVersionEx()
    return maj == 6 and min == 1


def splitcmdline(cmdline):
    """
    Parses the command-line and returns the tuple in the form
    (command, [param1, param2, ...])

    >>> splitcmdline('c:\\someexecutable.exe')
    ('c:\\\\someexecutable.exe', [])

    >>> splitcmdline('C:\\Program Files\\Internet Explorer\\iexplore.exe')
    ('C:\\\\Program Files\\\\Internet Explorer\\\\iexplore.exe', [])

    >>> splitcmdline('c:\\someexecutable.exe "param 1" param2')
    ('c:\\\\someexecutable.exe', ['param 1', 'param2'])

    >>> splitcmdline(r'c:\\program files\\executable.exe')
    ('c:\\\\program', ['files\\\\executable.exe'])

    >>> splitcmdline(r'"c:\\program files\\executable.exe" param1 param2   ')
    ('c:\\\\program files\\\\executable.exe', ['param1', 'param2'])
    """

    # Replace tabs and newlines with spaces
    cmdline = cmdline.strip(' \r\n\t').replace('\t', ' ').replace('\r', ' ').replace('\n', ' ')

    # Handle special cases first
    if " " not in cmdline:
        # Nothing to parse if there is no space, it's filename only
        return cmdline, []
    elif "\"" not in cmdline:
        # There are spaces but no quotes
        # Handle special cases of long filename not enclosed in quotes
        if os.path.isfile(expand_win_path_variables(cmdline)):
            return cmdline, []
        else:
            # otherwise split it by spaces
            parts = cmdline.split(" ")
            return parts[0], [part for part in parts[1:] if len(part) > 0]
    else:
        # Spaces and quotes are present so parse it carefully
        part = ""
        parts = []
        between_quotes = False

        for c in cmdline:
            if c == "\"":
                between_quotes = not between_quotes
                if not between_quotes:
                    # Just ended quotes, append part
                    parts.append(part)
                    part = ""
            elif c in (" ", "\t", "\n") and not between_quotes:
                if part:
                    parts.append(part)
                    part = ""
            else:
                part += c

        if part:
            parts.append(part)

        return parts[0], [part for part in parts[1:] if len(part) > 0]



if __name__ == "__main__":
    import doctest
    doctest.testmod()

# vim:set ff=unix tabstop=4 shiftwidth=4 expandtab: