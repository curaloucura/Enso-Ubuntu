'''
Created on Mar 3, 2010

@author: pavel
'''
import os
import re
import time
import logging


class Timer():
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = time.clock()

    def __exit__(self, *args):
        print u"%s: %0.4Fs" % (self.name, time.clock() - self.start)



if __name__ == "__main__":
    import doctest
    doctest.testmod()

# vim:set ff=unix tabstop=4 shiftwidth=4 expandtab: