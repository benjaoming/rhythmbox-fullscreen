# -*- coding: utf-8 -*-
import mimetypes

from gi.repository import GObject, Gio, Gtk, Peas, RB, GLib, GdkPixbuf

import os

from FullscreenWindow import *

from os import path, listdir
from urllib import url2pathname

ui_str = \
"""<ui>
  <menubar name="MenuBar">
    <menu name="ViewMenu" action="View">
      <placeholder name="ViewMenuModePlaceholder">
        <menuitem name="ViewMenuToggleFullscreen" action="ToggleFullscreen"/>
      </placeholder>
    </menu>
  </menubar>
  <toolbar name="ToolBar">
    <placeholder name="ToolBarPluginPlaceholder">
      <toolitem name="Fullscreen" action="ToggleFullscreen"/>
    </placeholder>
  </toolbar>
</ui>"""

class FullscreenView (GObject.Object, Peas.Activatable):

    object = GObject.property(type=GObject.Object)

    def __init__(self):
        super(FullscreenView, self).__init__()
        #self.settings = Gio.Settings("")
                
    def find_file(self, fname):
        my_path = os.path.abspath(os.path.split(__file__)[0])
        return os.path.join(my_path, fname)
    
    def do_activate(self):
        shell = self.object
        data = {}
        self.shell = shell
        # Add "view-fullscreen" icon.
        icon_file_name = self.find_file("view-fullscreen.svg")
        iconsource = Gtk.IconSource()
        iconsource.set_filename(icon_file_name)
        iconset = Gtk.IconSet()
        iconset.add_source(iconsource)
        iconfactory = Gtk.IconFactory()
        iconfactory.add("view-fullscreen", iconset)
        iconfactory.add_default()
        action = Gtk.Action("ToggleFullscreen", "Full Screen",
                            "Full Screen Mode",
                            "view-fullscreen");
        action.connect("activate", self.show_fullscreen, shell)
        
        data['action_group'] = Gtk.ActionGroup('FullscreenPluginActions')
        data['action_group'].add_action(action)
        
        uim = shell.props.ui_manager
        uim.insert_action_group(data['action_group'], 0)
        data['ui_id'] = uim.add_ui_from_string(ui_str)
        uim.ensure_update()

        shell.set_data('FullscreenPluginInfo', data)

    def do_deactivate(self):
        shell = self.object
        data = shell.get_data('FullscreenPluginInfo')
        uim = shell.props.ui_manager
        uim.remove_ui(data['ui_id'])
        uim.remove_action_group(data['action_group'])
        uim.ensure_update()

    def show_fullscreen(self, event, shell):
        self.window = FullscreenWindow(fullscreen=True,
                                       path=self.find_file("."),
                                       backend=self)
        
        # Receive notification of song changes
        self.player = shell.props.shell_player
        self.player.connect("playing-song-changed", self.reload_playlist)
        self.player.connect("playing-changed", self.reload_play_pause)

        db = shell.get_property("db")
        db.connect_after ("entry-extra-metadata-notify::rb:coverArt", 
                          self.notify_metadata)

        # Load current state
        self.reload_playlist(self.player, self.player.get_playing_entry())

    def playpause(self):
        try:
            self.player.playpause()
        except:
            self.play_entry(0)
        
    def play_entry(self, index):
        if len(self.tracks) > index:
            print dir(self.shell.props)
            self.player.play_entry(self.tracks[index]["entry"], self.shell.get_property("library-source"))

    def reload_play_pause(self, player, playing):
        if not self.window.track_widgets:
            return
        if playing:
            elapsed = player.get_playing_time()
            self.window.track_widgets[0].paused=False
            self.window.track_widgets[0].start_progress_bar(elapsed)
            self.window.current_info = "Now playing..."
            self.window.track_infos[0] = FullscreenWindow.INFO_STATUS_PAUSE
        else:
            self.window.track_widgets[0].paused=True
            self.window.current_info = FullscreenWindow.INFO_STATUS_IDLE
            self.window.track_infos[0] = FullscreenWindow.INFO_STATUS_PLAY

    def get_entries(self, player, entry, cnt):
        """Gets the next entries to be played from both active source and queue
        
        Uses each source's query-model.
        player = player to use
        entry = entry to start from (as a kind of offset)
        cnt = number of entries to return
        """

        if not entry:
            return []

        entries = [entry]
        
        queue = player.get_property("queue-source")
        if queue:
            querymodel = queue.get_property("query-model")
            l = querymodel.get_next_from_entry(entry)
            while l and len(entries) <= cnt:
                entries.append(l)
                l = querymodel.get_next_from_entry(l)
        source = player.get_property("source")
        if source:
            querymodel = source.get_property("query-model")
            l = querymodel.get_next_from_entry(entry)
            while l and len(entries) <= cnt:
                entries.append(l)
                l = querymodel.get_next_from_entry(l)

        return entries

    def get_track_info(self, entry):
        db = self.shell.props.db
        artist = entry.get_string(RB.RhythmDBPropType.ARTIST).replace('&', '&amp;')
        album = entry.get_string(RB.RhythmDBPropType.ALBUM).replace('&', '&amp;')
        title = entry.get_string(RB.RhythmDBPropType.TITLE).replace('&', '&amp;')
        duration = entry.get_ulong(RB.RhythmDBPropType.DURATION)
        track = {"artist":artist,
                 "album":album,
                 "title":title,
                 "duration":duration,
                 "entry":entry}
        return track
    
    def notify_metadata(self, db, entry, field=None,metadata=None):
        """Subscribe to metadata changes from database"""
        if entry != self.object.props.shell_player.get_playing_entry():
            self.set_cover_art(entry)
    
    def set_cover_art(self, entry):
        if entry:
            self.window.set_artwork(self.get_cover(entry))

    def get_cover(self, entry):
        if entry:
            
            # TODO: Get both pixbufs, compare them and use the largest one?
            # TODO: Make prettier
            # Try to find an album cover in the folder of the currently playing track
            cover_dir = path.dirname(url2pathname(entry.get_playback_uri()).replace('file://', ''))
            # TODO: use os.walk()
            # TODO: just pick any picture in the directory
            if path.isdir(cover_dir):
                for f in listdir(cover_dir):
                    file_name = path.join(cover_dir, f)
                    mt = mimetypes.guess_type(file_name)[0]
                    if mt and mt.startswith('image/'):
                        #if path.splitext(f)[0].lower() in ['cover', 'album', 'albumart', '.folder', 'folder']:
                        # TODO: Use proportions from configuration
                        return GdkPixbuf.Pixbuf.new_from_file_at_size (file_name, 800, 800)

            # Otherwise use what's found by the album art plugin
            db = self.shell.get_property("db")
            cover_art = db.entry_request_extra_metadata(entry, "rb:coverArt")
            return cover_art
    
    def reload_playlist(self, player, entry):

        db = self.shell.props.db
        
        # If nothing is playing then use current play order
        # to move to the next track.
        if not entry:
            try:
                # TODO: Fix getting the next playing song
                playorder = player.get_property("play-order-instance")
                entry = playorder.get_next()
            except:
                print "play-order-instance not available"
                return
        
        # Set cover art
        self.set_cover_art(entry)
        
        entries = self.get_entries(player, entry, 20)
        self.tracks = []
        
        for entry in entries:
            self.tracks.append(self.get_track_info(entry))
        
        self.window.set_tracks(self.tracks)
        try:
            elapsed = player.get_playing_time()
        except:
            elapsed = 0.0

        if player.get_playing():
            self.window.track_widgets[0].start_progress_bar(elapsed)
            self.window.current_info = "Now playing..." # TODO
        else:
            self.window.track_widgets[0].set_elapsed(elapsed)
            self.window.current_info = FullscreenWindow.INFO_STATUS_IDLE
        
        self.window.show_info()