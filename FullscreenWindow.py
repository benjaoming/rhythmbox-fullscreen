# -*- coding: utf-8 -*-
import sys, rb

from gi.repository import GObject, Gio, Gtk, Peas, RB, GLib, Gdk, GdkPixbuf

from CairoWidgets import FullscreenEntryButton
from RhythmboxFullscreenPrefs import GSetting

_track1Bg = "#222"
_track2Bg = "#111"
_track3Bg = "#111"
_track1Fg = "#FFF"
_track2Fg = "#888"
_track3Fg = "#666"

_albumCoverHeight = 300 #pixels
_albumCoverWidth  = 300 #pixels

class FullscreenWindow(Gtk.Window):
    
    INFO_STATUS_IDLE  = "Player idle"
    INFO_STATUS_PAUSE = "Pause playing track"
    INFO_STATUS_PLAY  = "Resume playback"
    INFO_STATUS_SKIP  = "Skip to this track"
    
    def __init__(self, plugin):
        
        gs=GSetting()
        settings = gs.get_setting(gs.Path.PLUGIN)
        fullscreen = settings[gs.PluginKey.USE_WINDOW] == False
        
        self.backend = plugin #FullscreenView instance
        Gtk.Window.__init__(self)
        self.connect("delete_event", self.delete_event)
        self.connect("key_press_event", self.key_press)
        self.set_border_width(100)
        self.modify_bg(Gtk.StateFlags.NORMAL,Gdk.Color(0,0,0))
        try:
            icon_theme = Gtk.icon_theme_get_default()
            self.set_icon(icon_theme.load_icon("view-fullscreen", Gtk.ICON_SIZE_DIALOG, Gtk.ICON_LOOKUP_FORCE_SVG))
        except:
            pass
        self.set_title("Rhythmbox Fullscreen View")

        self.table = Gtk.Table(3,3)
        self.table.set_row_spacings(4)
        self.table.set_col_spacings(10)
        
        from RhythmboxFullscreen import find_plugin_file
        self.no_artwork = GdkPixbuf.Pixbuf.new_from_file_at_size (find_plugin_file("img/rhythmbox-missing-artwork.svg"),
                                                                _albumCoverWidth,
                                                                _albumCoverHeight)
        self.album_widget = Gtk.Image()
        self.set_artwork()
        
        # INFO AREA WHEN HOVERING TRACKS
        self.info_label = Gtk.Label()
        self.info_label.set_alignment(1,0)
        self.current_info = FullscreenWindow.INFO_STATUS_IDLE
        self.show_info(self.current_info)

        #Layout containing vbox with tracks
        self.track_layout = Gtk.Layout()
        self.track_layout.set_size(500,300)
        self.track_layout.set_size_request(500,300)
        self.track_layout.modify_bg(Gtk.StateFlags.NORMAL, Gdk.Color(0,0,0))
        self.track_layout.set_events( Gdk.EventMask.LEAVE_NOTIFY_MASK
                                      | Gdk.EventMask.POINTER_MOTION_MASK )
        self.track_layout.connect("motion_notify_event", self.track_layout_scroll)

        self.scroll_event_id = None
        self.scroll_y = 0
        
        # Number of tracks to display
        self.track_count = 0
        # Remember track widget points in array
        self.vbox = None
        self.track_widgets = []
        self.reload_track_widgets()

        self.table.attach(self.album_widget,0,1,0,1)
        self.table.attach(self.track_layout,1,2,0,1)
        self.table.attach(self.info_label,0,2,2,4)
        self.table2 = Gtk.Table(1,1)
        self.table2.attach(self.table,0,1,0,1,xoptions=Gtk.AttachOptions.EXPAND,yoptions=Gtk.AttachOptions.EXPAND)
        
        self.add(self.table2)

        # Hover text for tracks
        self.track_infos = []
        
        self.show_all()
        if fullscreen:
            self.fullscreen()
        else:
            self.maximize()

    def destroy_track_widgets(self):
        for w in self.track_widgets:
            w.destroy()
        self.track_widgets = []

    def reload_track_widgets(self, current_track=0):
        
        self.current_track = current_track
        
        self.destroy_track_widgets()
        if self.vbox:
            self.vbox.destroy()
        self.vbox = Gtk.VBox(spacing=4)
        self.vbox.set_size_request(500,300)

        for i in range(self.track_count):
            if i == current_track:
                t = FullscreenEntryButton(bg_color=_track1Bg,
                                          width=500,
                                          size1=24, size2=18,
                                          has_progress_bar = True)
                #t.set_hover_icon(FullscreenEntryButton.HOVER_ICON_PAUSE)
                self.track_infos.append(self.INFO_STATUS_PAUSE)
            elif i == current_track+1:
                t = FullscreenEntryButton( bg_color=_track2Bg,
                                          width=500, size1=18, size2=14 )
                self.track_infos.append(self.INFO_STATUS_SKIP)
                #t.set_hover_icon(FullscreenEntryButton.HOVER_ICON_SKIP)
            else:
                t = FullscreenEntryButton( bg_color=_track3Bg,
                                          width=500, size1=14, size2=12 )
                self.track_infos.append(self.INFO_STATUS_SKIP)
                #t.set_hover_icon(FullscreenEntryButton.HOVER_ICON_SKIP)
            self.track_widgets.append(t)
            self.vbox.pack_start(t, False, False, 0)
            t.connect("button_press_event", self.track_click)
            t.connect("enter_notify_event", self.track_hover_on)
            t.connect("leave_notify_event", self.track_hover_out)

        self.scroll_y = 0
        self.track_layout.put(self.vbox,0,0)
        self.track_layout.show_all()

    def track_hover_on(self, widget, event):
        index = self.track_widgets.index(widget)
        self.show_info(self.track_infos[index])

    def track_hover_out(self, widget, event):
        self.show_info(self.current_info)
        
    def track_click(self, widget, event):
        if self.scroll_event_id:
            GObject.source_remove(self.scroll_event_id)
        index = self.track_widgets.index(widget)
        if index==0:
            self.backend.playpause()
            self.show_info(self.track_infos[index])
        else:
            self.backend.play_entry(index)
    
    def track_layout_scroll_stop(self, widget, event):
        if self.scroll_event_id:
            GObject.source_remove(self.scroll_event_id)
        
    def track_layout_scroll(self, widget, event):
        time_step = 5 #msecs
        ycoord = event.y
        accel_factor = 4 #how many pixels to scroll at the edge
        edge_distance = 100.0 #pixels
        layout_size = self.track_layout.get_size()
        top_dist = edge_distance - ycoord
        bot_dist = edge_distance - layout_size[1] + ycoord
        
        if top_dist > 0:
            accel = -1 - (top_dist / edge_distance) * accel_factor
        elif bot_dist > 0:
            accel =  1 + (bot_dist / edge_distance) * accel_factor
        else:
            accel = 0.0

        if self.scroll_event_id:
            GObject.source_remove(self.scroll_event_id)
        
        if not accel == 0.0:
            self.scroll_event_id = GObject.timeout_add(time_step, self.do_scrolling, accel)
    
    def do_scrolling(self, accel):
        step = int(1*accel)
        if step == 0:
            return
        vbox_size = self.vbox.size_request()
        layout_size = self.track_layout.get_size()
        scroll_height = vbox_size.height - layout_size[1]
        if self.scroll_y + step < 0:
            self.scroll_y = 0
        elif self.scroll_y + step > scroll_height:
            self.scroll_y = scroll_height
        else:
            self.scroll_y += step
        
        self.track_layout.move(self.vbox, 0, -self.scroll_y)
        return self.scroll_y > 0 and self.scroll_y < scroll_height
        
        
    # Renew queue
    def set_tracks(self, tracks, current_track=0):
        self.track_count = len(tracks)
        self.reload_track_widgets(current_track=current_track)
        i=0
        for w in self.track_widgets:
            if i<self.track_count:
                t=tracks[i]
                w.set_track(t["artist"],t["album"],t["title"],t["duration"])
                w.queue_draw()
            else:
                w.set_track("","","",0)
                w.queue_draw()
            i+=1
        
    def show_info(self, str_info=None):
        if not str_info:
            str_info = self.current_info
        self.info_label.set_markup('<span color="#FFF">%s</span>' % str_info)
        self.info_label.queue_draw()

    def delete_event(self, widget, event, data=None):
        return False

    def set_artwork(self, pixbuf=None):
        if not pixbuf:
            self.albumPixbuf = self.no_artwork
        else:
            # Keep aspect ratios
            h = pixbuf.get_height()
            w = pixbuf.get_width()
            if h == 0 or w == 0:
                self.albumPixbuf = self.no_artwork
            else:
                scaled_w = w/(h/float(_albumCoverHeight)) if h > w else _albumCoverWidth
                scaled_h = h/(w/float(_albumCoverWidth))  if w > h else _albumCoverHeight
                pixbuf = pixbuf.scale_simple(int(scaled_w), int(scaled_h),
                                             GdkPixbuf.InterpType.BILINEAR)
                self.albumPixbuf = pixbuf
        
        self.album_widget.set_from_pixbuf(self.albumPixbuf)
        self.album_widget.show_all()

    def key_press(self, widget, event, data=None):
        
        # Quit on ESC key press
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()

