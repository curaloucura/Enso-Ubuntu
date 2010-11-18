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

import os
import ctypes
import win32api
import logging

from ctypes import wintypes


class ControlPanelInfo(object):
    CPL_INIT = 1
    CPL_GETCOUNT = 2
    CPL_INQUIRE = 3
    CPL_EXIT = 7
    CPL_NEWINQUIRE = 8

    class NEWCPLINFO(ctypes.Structure):
        class _NEWCPLINFO_UNION(ctypes.Union):
            class _NEWCPLINFO_A(ctypes.Structure):
                # ANSI version
                _fields_ = [
                    ('szName', ctypes.c_char * 32), # array [0..31] of CHAR short name
                    ('szInfo', ctypes.c_char * 64), # array [0..63] of CHAR long name (status line)
                    ('szHelpFile', ctypes.c_char * 128) # array [0..127] of CHAR path to help file to use
                    ]

            class _NEWCPLINFO_W(ctypes.Structure):
                # Unicode version
                _fields_ = [
                    ('szName', ctypes.c_wchar * 32), # array [0..31] of CHAR short name
                    ('szInfo', ctypes.c_wchar * 64), # array [0..63] of CHAR long name (status line)
                    ('szHelpFile', ctypes.c_wchar * 128) # array [0..127] of CHAR path to help file to use
                ]

            # Union of ANSI and Unicode version
            _fields_ = [
                ('szStringsW', _NEWCPLINFO_W),
                ('szStringsA', _NEWCPLINFO_A)
            ]

        _fields_ = [
            ('dwSize', wintypes.DWORD),
            ('dwFlags', wintypes.DWORD),
            ('dwHelpContext', wintypes.DWORD), # help context to use
            ('lData', ctypes.c_void_p), # LONG_PTR user defined data
            ('hIcon', wintypes.HANDLE), # icon to use, this is owned by CONTROL.EXE (may be deleted)
            ('u', _NEWCPLINFO_UNION)
        ]

    class CPLINFO(ctypes.Structure):
        _fields_ = [
            ('idIcon', wintypes.DWORD), # icon resource id, provided by CPlApplet()
            ('idName', wintypes.DWORD), # name string res. id, provided by CPlApplet()
            ('idInfo', wintypes.DWORD), # info string res. id, provided by CPlApplet()
            ('lData', ctypes.c_void_p) # user defined data
        ]

    class GetLibrary(object):
        def __init__(self, dll_filename):
            self._dll_handle = ctypes.windll.LoadLibrary(dll_filename)
            #self._dll_handle = win32api.LoadLibrary(dll_filename)
            #self._dll = ctypes.WinDLL(dll_filename)
            #self._dll_handle = self._dll._handle
            #self._handle = win32api.LoadLibrary(dll_filename)

        def __enter__(self):
            #return self._dll
            return self._dll_handle

        def __exit__(self, type, value, traceback):
            if self._dll_handle:
                #win32api.FreeLibrary(self._dll_handle)
                self._dll_handle = None
                #del self._dll
                #self._dll = None

    def get_cplinfo(self, filename):
        cpl_applet = None
        try:
            with self.GetLibrary(filename) as dll_handle:
                try:
                    cpl_applet = dll_handle.CPlApplet
                except Exception, e:
                    logging.error("%s : %s", filename, e)
                    return
                cpl_applet.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.LPARAM, ctypes.c_void_p]
                try:
                    if cpl_applet(0, self.CPL_INIT, 0, 0) == 0:
                        pass
                except Exception, e:
                    print "1:", filename, e

                try:
                    dialog_cnt = cpl_applet(0, self.CPL_GETCOUNT, 0, 0)
                except Exception, e:
                    print "2:", filename, e
                if dialog_cnt == 0:
                    return
                if not 0 < dialog_cnt <= 20:
                    logging.warning("Suspicious dialog count for %s: %d" % (filename, dialog_cnt))
                    return

            for dialog_i in range(0, dialog_cnt):
                newcplinfo = self.NEWCPLINFO()
                newcplinfo.dwSize = 0
                try:
                    cpl_applet(0, self.CPL_NEWINQUIRE, dialog_i, ctypes.byref(newcplinfo))
                except Exception, e:
                    print "3:", filename, e

                name = None
                info = None
                if newcplinfo.dwSize > 0:
                    if newcplinfo.dwSize == 244:
                        # Descriptions are in ANSI
                        name = unicode(newcplinfo.u.szStringsA.szName)
                        info = unicode(newcplinfo.u.szStringsA.szInfo)
                    else:
                        # Descriptions are in Unicode
                        name = newcplinfo.u.szStringsW.szName.decode("utf-8")
                        info = newcplinfo.u.szStringsW.szInfo.decode("utf-8")

                if not name and not info:
                    cplinfo = self.CPLINFO()
                    try:
                        cpl_applet(0, self.CPL_INQUIRE, dialog_i, ctypes.byref(cplinfo))
                    except Exception, e:
                        print "4:", filename, e

                    handle = None
                    result = None
                    try:
                        handle = win32api.LoadLibrary(filename)
                        name = win32api.LoadString(handle, cplinfo.idName).strip(" \n\0")
                        info = win32api.LoadString(handle, cplinfo.idInfo).strip(" \n\0")
                    finally:
                        if handle:
                            win32api.FreeLibrary(handle)

                result = (
                    os.path.basename(filename),
                    name,
                    info,
                    dialog_i)
                yield result
        except Exception, e:
            print e
            pass
        finally:
            if cpl_applet:
                try:
                    cpl_applet(0, self.CPL_EXIT, 0, 0)
                except Exception, e:
                    print "5:", filename, e


# vim:set tabstop=4 shiftwidth=4 expandtab:
