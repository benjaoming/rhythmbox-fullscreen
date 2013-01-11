#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import rhythmdb, rb
import threading, thread, time
import gtk, gobject
from FullscreenWindow import *
#from RbFullscreenModel import *
#from RbFullscreenEvents import *

class FullscreenTest(object):
    """
    Please note that this is NOT a complete module test. This is simply for
    playing around with the plugin outside of Rhythmbox.
    """
    
    def __init__(self):
        pass

    # Has to be in a thread of its own like a normal Rhythmbox plugin
        # Create a model that also controls the window
        #model = RbFullscreenModel(window)
        # Handle events upon user input or callbacks from Rhythmbox
        #event_handler = RbFullscreenEvents(model,rb,window)

if __name__ == '__main__':
    w = FullscreenWindow(fullscreen = True)
    #w.track1.start_progress_bar()
    w.connect("delete_event", gtk.main_quit)
    
    gtk.main()
