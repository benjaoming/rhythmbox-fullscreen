# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# Copyright (C) 2013 - Benjamin Bach <benjamin@overtag.dk>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

from gi.repository import GObject  # @UnresolvedImport
from gi.repository import Gtk  # @UnresolvedImport
from gi.repository import Gdk  # @UnresolvedImport
from gi.repository import GdkPixbuf  # @UnresolvedImport

import rb  # @UnresolvedImport
from CairoWidgets import FullscreenEntryButton
from RhythmboxFullscreenPrefs import GSetting

_track1Bg = "#222"
_track2Bg = "#111"
_track3Bg = "#111"
_track1Fg = "#FFF"
_track2Fg = "#888"
_track3Fg = "#666"

class FullscreenWindow(Gtk.Window):
    INFO_STATUS_IDLE = "Player idle"
    INFO_STATUS_PAUSE = "Pause playing track"
    INFO_STATUS_PLAY = "Resume playback"
    INFO_STATUS_SKIP = "Skip to this track"

    _albumCoverHeight = 300  # pixels
    _albumCoverWidth = 300  # pixels

    def __init__(self, plugin):

        gs = GSetting()
        settings = gs.get_setting(gs.Path.PLUGIN)
        fullscreen = settings[gs.PluginKey.USE_WINDOW] == False

        self.backend = plugin  # FullscreenView instance
        Gtk.Window.__init__(self)
        self.connect("delete_event", self.delete_event)
        self.connect("key_press_event", self.key_press)
        self.set_border_width(100)


        w = self
        s = w.get_screen()
        # Using the screen of the Window, the monitor it's on can be identified
        m = s.get_monitor_at_window(s.get_active_window())
        # Then get the geometry of that monitor
        monitor = s.get_monitor_geometry(m)
        # This is an example output
        print("Heigh: %s, Width: %s" % (monitor.height, monitor.width))
        if monitor.height < monitor.width:
            self._albumCoverHeight = monitor.height / 2
            self._albumCoverWidth = monitor.height / 2
        else:
            self._albumCoverHeight = monitor.width / 2
            self._albumCoverWidth = monitor.width / 2

        self.modify_bg(Gtk.StateFlags.NORMAL, Gdk.Color(0, 0, 0))
        try:
            icon_theme = Gtk.icon_theme_get_default()
            self.set_icon(icon_theme.load_icon("view-fullscreen",
                                               Gtk.ICON_SIZE_DIALOG, Gtk.ICON_LOOKUP_FORCE_SVG))
        except:
            pass
        self.set_title("Rhythmbox Fullscreen View")
        self.set_events(Gdk.EventMask.ENTER_NOTIFY_MASK)
        self.connect('enter-notify-event', self.track_layout_scroll_stop)

        self.table = Gtk.Table(3, 3)
        self.table.set_row_spacings(4)
        self.table.set_col_spacings(10)

        self.no_artwork = GdkPixbuf.Pixbuf.new_from_file_at_size(
            rb.find_plugin_file(self.backend, "img/rhythmbox-missing-artwork.svg"),
            self._albumCoverWidth,
            self._albumCoverHeight
        )

        self.album_widget = Gtk.Image()
        self.set_artwork()

        # INFO AREA WHEN HOVERING TRACKS
        self.info_label = Gtk.Label()
        self.info_label.set_alignment(1, 0)
        self.current_info = FullscreenWindow.INFO_STATUS_IDLE
        self.show_info(self.current_info)

        # Layout containing vbox with tracks
        self.track_layout = Gtk.Layout()
        self.track_layout.set_size(self._albumCoverWidth + 200, self._albumCoverHeight)
        self.track_layout.set_size_request(self._albumCoverWidth + 200, self._albumCoverHeight)
        self.track_layout.modify_bg(Gtk.StateFlags.NORMAL, Gdk.Color(0, 0, 0))
        self.track_layout.set_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.track_layout.connect('motion_notify_event', self.track_layout_scroll)

        self.current_track = 0

        self.scroll_event_id = None
        self.scroll_y = 0

        # Number of tracks to display
        self.track_count = 0
        # Remember track widget points in array
        self.track_table = None
        self.track_widgets = []
        self.reload_track_widgets()

        self.table.attach(self.album_widget, 0, 1, 0, 1)
        self.table.attach(self.track_layout, 1, 2, 0, 1)
        self.table.attach(self.info_label, 0, 2, 2, 4)
        self.table2 = Gtk.Table(1, 1)
        self.table2.attach(self.table, 0, 1, 0, 1,
                           xoptions=Gtk.AttachOptions.EXPAND, yoptions=Gtk.AttachOptions.EXPAND)

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
        self.track_widget_heights = []
        self.track_widgets = []

    def change_playing_track(self, current_track=0):
        if not self.track_widgets:
            return self.reload_track_widgets(current_track=current_track)
        old_track = self.current_track
        self.current_track = current_track
        self.track_table.remove(self.track_widgets[old_track])
        self.track_table.remove(self.track_widgets[current_track])
        self.track_widgets[old_track].destroy()
        self.track_widgets[current_track].destroy()

        current_widget = self.get_track_widget(active=True)
        old_widget = self.get_track_widget(active=False)

        self.track_widgets[current_track] = current_widget
        self.track_widgets[old_track] = old_widget

        t = self.tracks[current_track]
        current_widget.set_track(t.artist, t.album, t.title, t.duration)
        t = self.tracks[old_track]
        old_widget.set_track(t.artist, t.album, t.title, t.duration)

        self.track_table.attach_defaults(
            current_widget,
            0, 1, current_track, current_track + 1
        )
        self.track_table.attach_defaults(
            old_widget,
            0, 1, old_track, old_track + 1
        )
        self.track_table.show_all()

    def reload_track_widgets(self, current_track=0):

        self.current_track = current_track

        self.destroy_track_widgets()
        if self.track_table:
            self.track_table.destroy()
        if self.track_count == 0:
            return
        self.track_table = Gtk.Table(self.track_count, 1)
        self.track_table.set_row_spacings(4)
        self.track_table.set_size_request(self._albumCoverWidth + 195, self._albumCoverHeight)

        for i in range(self.track_count):
            w = self.get_track_widget(active=(i == current_track))
            if i == current_track:
                self.track_infos.append(self.INFO_STATUS_PAUSE)
            else:
                self.track_infos.append(self.INFO_STATUS_PAUSE)
            self.track_widgets.append(w)
            self.track_table.attach_defaults(w, 0, 1, i, i + 1)

        self.scroll_y = 0
        self.track_layout.put(self.track_table, 0, 0)
        self.track_layout.show_all()
        for i, w in enumerate(self.track_widgets):
            if i < self.track_count:
                t = self.tracks[i]
                w.set_track(t.artist, t.album, t.title, t.duration)
                w.queue_draw()
            else:
                w.set_track("", "", "", 0)
                w.queue_draw()
            i += 1
        GObject.idle_add(self.scroll_to_current)

    def get_track_widget(self, active=False):
        if active:
            w = FullscreenEntryButton(
                bg_color=_track1Bg,
                width=self._albumCoverWidth + 200, size1=24, size2=18,
                has_progress_bar=True)
            # w.set_hover_icon(FullscreenEntryButton.HOVER_ICON_PAUSE)
        else:
            w = FullscreenEntryButton(bg_color=_track2Bg,
                                      width=self._albumCoverWidth + 200, size1=18, size2=14)
            # w.set_hover_icon(FullscreenEntryButton.HOVER_ICON_SKIP)
        w.connect("button_press_event", self.track_click)
        w.connect("enter_notify_event", self.track_hover_on)
        w.connect("leave_notify_event", self.track_hover_out)
        return w

    def track_hover_on(self, widget, event):
        try:
            index = self.track_widgets.index(widget)
            self.show_info(self.track_infos[index])
        except ValueError:
            pass

    def track_hover_out(self, widget, event):
        self.show_info(self.current_info)

    def track_click(self, widget, event):
        if self.scroll_event_id:
            GObject.source_remove(self.scroll_event_id)
        index = self.track_widgets.index(widget)
        if index == self.current_track:
            self.backend.playpause()
            self.show_info(self.track_infos[index])
        else:
            self.backend.play_entry(index)

    def track_layout_scroll_stop(self, widget, event):
        if self.scroll_event_id:
            GObject.source_remove(self.scroll_event_id)
            self.scroll_event_id = None

    def track_layout_scroll(self, widget, event):
        time_step = 5  # msecs
        ycoord = event.y
        accel_factor = 4  # how many pixels to scroll at the edge
        edge_distance = 100.0  # pixels
        layout_size = self.track_layout.get_size()
        top_dist = edge_distance - ycoord
        bot_dist = edge_distance - layout_size[1] + ycoord

        if top_dist > 0:
            accel = -1 - (top_dist / edge_distance) * accel_factor
        elif bot_dist > 0:
            accel = 1 + (bot_dist / edge_distance) * accel_factor
        else:
            accel = 0.0

        if self.scroll_event_id:
            GObject.source_remove(self.scroll_event_id)

        if not accel == 0.0:
            self.scroll_event_id = GObject.timeout_add(time_step, self.do_scrolling, accel)
        else:
            self.scroll_event_id = GObject.timeout_add(10 * 1000, self.scroll_to_current)

    def do_scrolling(self, accel):
        step = int(1 * accel)
        if step == 0:
            return
        if not self.track_table:
            # Scroll event called when no track_table
            return
        track_table_size = self.track_table.size_request()
        layout_size = self.track_layout.get_size()
        scroll_height = track_table_size.height - layout_size[1]
        if self.scroll_y + step < 0:
            self.scroll_y = 0
        elif self.scroll_y + step > scroll_height:
            self.scroll_y = scroll_height
        else:
            self.scroll_y += step

        self.track_layout.move(self.track_table, 0, -self.scroll_y)

        continue_scrolling = self.scroll_y > 0 and self.scroll_y < scroll_height
        if not continue_scrolling:
            self.scroll_event_id = GObject.timeout_add(10 * 1000, self.scroll_to_current)

        return continue_scrolling

    def scroll_to_current(self):
        if self.scroll_event_id:
            GObject.source_remove(self.scroll_event_id)
            self.scroll_event_id = None

        try:
            current_widget = self.track_widgets[self.current_track]
        except IndexError:
            return False

        allocation = current_widget.get_allocation()

        time_step = 2  # msecs

        if allocation.y > self.scroll_y:
            self.scrollto_direction = 1
        else:
            self.scrollto_direction = -1

        self.scrollto_step_size = 3

        self.scrollto_steps = abs((self.scroll_y - allocation.y) // self.scrollto_step_size)

        self.scroll_event_id = GObject.timeout_add(
            time_step,
            self.do_scroll_to,
        )

    def do_scroll_to(self):
        self.scroll_y += self.scrollto_step_size * self.scrollto_direction
        self.track_layout.move(self.track_table, 0, -self.scroll_y)
        self.scrollto_steps -= 1
        return self.scrollto_steps > 0

    # Renew queue
    def set_tracks(self, tracks, current_track=0):
        self.track_count = len(tracks)
        self.tracks = tracks
        self.reload_track_widgets(current_track=current_track)

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
                scaled_w = w / (h / float(self._albumCoverHeight)) if h > w else self._albumCoverWidth
                scaled_h = h / (w / float(self._albumCoverWidth)) if w > h else self._albumCoverHeight
                pixbuf = pixbuf.scale_simple(int(scaled_w), int(scaled_h),
                                             GdkPixbuf.InterpType.BILINEAR)
                self.albumPixbuf = pixbuf

        self.album_widget.set_from_pixbuf(self.albumPixbuf)
        self.album_widget.show_all()

    def key_press(self, widget, event, data=None):

        # Quit on ESC key press
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
