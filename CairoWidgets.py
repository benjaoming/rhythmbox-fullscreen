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

from math import pi
from cgi import escape

from gi.repository import GObject  # @UnresolvedImport
from gi.repository import Gtk  # @UnresolvedImport
from gi.repository import Gdk  # @UnresolvedImport
from gi.repository import PangoCairo  # @UnresolvedImport


# Create a GTK+ widget on which we will draw using Cairo
class RoundedButtonPangoCairoWidget(Gtk.DrawingArea):
    def __init__(self, upper=9, text=''):
        Gtk.DrawingArea.__init__(self)
        self.connect('draw', self.do_draw_cb)

    # Handle the expose-event by drawing
    def do_draw_cb(self, event, cr):

        cr.set_source_rgba(0, 0, 0, 1.0)  # Transparent

        # Draw the background
        cr.paint()

        self.draw(cr, self.get_allocated_width(), self.get_allocated_height())

    def draw(self, cr, width, height):
        pass

    def write(self, cr, markup="", x=0, y=0, vert_middle=True,
              adjust_widget_size=True
              ):
        '''Write some text on the context. Text must be valid Pango markup,
and font must be a valid Pango font. Current point is not changed by this
function.'''
        layout = PangoCairo.create_layout(cr)
        layout.set_markup(markup)
        cr.save()
        w, h = layout.get_pixel_size()
        if vert_middle:
            y2 = y - h / 2
        else:
            y2 = y
        if adjust_widget_size:
            self.set_size_request(w, h)

        cr.move_to(x, y2)
        PangoCairo.update_layout(cr, layout)
        PangoCairo.show_layout(cr, layout)
        cr.restore()

        return w, h

    def draw_rounded_rectangle(self, cr, x, y, width, height, radius=30):
        '''Draw a rounded rectangle path'''
        offset = radius / 3
        x0 = x + offset
        y0 = y + offset
        x1 = x + width - offset
        y1 = y + height - offset
        cr.new_path()
        cr.arc(x0 + radius, y1 - radius, radius, pi / 2, pi)
        cr.line_to(x0, y0 + radius)
        cr.arc(x0 + radius, y0 + radius, radius, pi, 3 * pi / 2)
        cr.line_to(x1 - radius, y0)
        cr.arc(x1 - radius, y0 + radius, radius, 3 * pi / 2, 2 * pi)
        cr.line_to(x1, y1 - radius)
        cr.arc(x1 - radius, y1 - radius, radius, 0, pi / 2)
        cr.close_path()


class FullscreenEntryButton(RoundedButtonPangoCairoWidget):
    HOVER_ICON_PLAY, HOVER_ICON_PAUSE, HOVER_ICON_SKIP = list(range(3))

    def __init__(self,
                 bg_color=(0.1, 0.1, 0.1, 1.0),
                 markup="",
                 width=-1, height=-1,
                 size1=24, size2=18,
                 has_progress_bar=False):

        super(FullscreenEntryButton, self).__init__()

        self.connect("enter_notify_event", self.pulsate)
        self.connect("leave_notify_event", self.pulsate_stop)
        self.pulsating = False
        self.pulse_lock = False
        self.set_sensitive(True)
        self.set_events(Gdk.EventMask.LEAVE_NOTIFY_MASK
                        | Gdk.EventMask.ENTER_NOTIFY_MASK
                        | Gdk.EventMask.BUTTON_PRESS_MASK)
        self.bg_color = (0.1, 0.1, 0.1, 1.0)
        self.original_bg = self.bg_color
        self.size1 = size1
        self.size2 = size2
        self.markup = markup
        self.width = width
        self.height = height
        self.has_progress_bar = has_progress_bar
        self.progress_event_id = None
        self.progress = 0.0
        self.paused = False
        self.icon = None
        self.icon_hover = None

        self.artist = ""
        self.album = ""
        self.track = ""
        self.duration = 0

    def set_track(self, artist, album, track, duration):
        self.artist = artist
        self.album = album
        self.track = track
        self.duration = duration

    def set_elapsed(self, elapsed=(False, 0.0)):
        elapsed = elapsed[1]
        if not elapsed == 0.0:
            self.progress = (elapsed * 1.0) / self.duration
        else:
            self.progress = 0.0

    def start_progress_bar(self, elapsed=(False, 0.0)):
        elapsed = elapsed[1]
        if not elapsed == 0.0:
            self.progress = (elapsed * 1.0) / self.duration
        else:
            self.progress = 0.0
        self.progress_bar_do()
        time_step = 100
        if self.progress_event_id:
            GObject.source_remove(self.progress_event_id)
        self.progress_event_id = GObject.timeout_add(time_step, self.progress_bar_do)

    def progress_bar_do(self):
        time_step = 100
        if self.progress <= 1 and not self.paused and not self.duration == 0:
            self.progress += (time_step / 1000.0) / self.duration
            GObject.idle_add(self.queue_draw)
            return True
        return not self.paused

    def pulsate(self, widget, event):
        self.icon = self.icon_hover
        # self.window.set_cursor(Gdk.Cursor(Gdk.HAND2))
        if not self.pulsating:
            self.pulsating = True
            self.pulsate_do()

    def pulsate_stop(self, widget, event):
        self.pulsating = False
        self.icon = None

    def pulsate_do(self, cnt=0, direction=1):
        # Just quit if we're already animating
        if self.pulse_lock:
            return
        self.pulse_lock = True
        pulse_steps = 20
        adjustment = 0.005

        def adjust(color, direction):
            return (
                color[0] + (adjustment * direction),
                color[1] + (adjustment * direction),
                color[2] + (adjustment * direction),
                1.0
            )

        if self.pulsating:
            self.bg_color = adjust(self.bg_color, direction)
            GObject.idle_add(self.queue_draw)
            cnt += 1
            if cnt == pulse_steps:
                cnt = 0
                direction *= -1
            self.pulse_lock = False
            GObject.timeout_add(20, self.pulsate_do, cnt, direction)

        # restore after a pulse
        if not self.pulsating and self.original_bg[0] <= self.bg_color[0]:
            direction = -1
            self.bg_color = adjust(self.bg_color, direction)
            GObject.idle_add(self.queue_draw)
            self.pulse_lock = False
            GObject.timeout_add(20, self.pulsate_do, cnt, direction)

        self.pulse_lock = False

    def set_hover_icon(self, icon):
        self.icon_hover = icon

    def draw(self, cr, width, height):

        # Create background rectangle
        self.draw_rounded_rectangle(cr, 0, 0, width, height, 5)
        cr.set_source_rgba(*self.bg_color)
        cr.fill()

        # Draw progress bar
        if self.has_progress_bar and not self.duration == 0:
            self.draw_rounded_rectangle(cr, 3, 3, (width - 15) * self.progress, height - 6, 4)
            ligten_factor = 1.5
            progress_bar_color = [x * ligten_factor for x in self.bg_color[:3]] + [1.0]
            cr.set_source_rgba(*progress_bar_color)
            cr.fill()

            # Draw icon
        #        cr.set_source_color (Gdk.color_parse("#000"))
        #        if self.icon == self.HOVER_ICON_PAUSE:
        #            cr.rectangle(width-26, 11, 5, 14)
        #            cr.rectangle(width-17, 11, 5, 14)
        #            cr.fill()
        #        if self.icon == self.HOVER_ICON_SKIP:
        #            cr.new_path()
        #            cr.line_to(width-26, 25)
        #            cr.line_to(width-19, 18)
        #            cr.line_to(width-26, 11)
        #            cr.close_path()
        #            cr.fill()
        #            cr.new_path()
        #            cr.line_to(width-17, 25)
        #            cr.line_to(width-10, 18)
        #            cr.line_to(width-17, 11)
        #            cr.close_path()
        #            cr.fill()

        def number_format(no):
            if no < 10:
                return "0" + str(int(no))
            else:
                return str(int(no))

        # Write text
        if self.has_progress_bar:
            track_time = " (%s:%s of %s:%s)" % (number_format(self.duration * self.progress / 60),
                                                number_format(self.duration * self.progress % 60),
                                                number_format(self.duration / 60),
                                                number_format(self.duration % 60))
        else:
            track_time = " (%s:%s)" % (number_format(self.duration / 60),
                                       number_format(self.duration % 60))
        cr.set_source_rgba(1, 1, 1, 1)
        m = ('<span font_family="Trebuchet MS, Liberation Sans, Sans">' + \
             '<span size="%d">%s\n</span>' + \
             '<span size="%d">%s\n</span>' + \
             '<span size="%d">%s%s</span>' + \
             '</span>') % (self.size1 * 1024, escape(self.artist),
                           self.size2 * 1024 * .8, escape(self.album),
                           self.size2 * 1024, escape(self.track),
                           track_time)
        text_width, text_height = self.write(cr, m, 10, height / 2, adjust_widget_size=False)

        # Scale widget to either fit text or fixed dimensions
        if self.width == -1:
            w = text_width + 20
        else:
            w = self.width
        if self.height == -1:
            h = text_height + 20
            self.height = h
        else:
            h = self.height

        self.set_size_request(w, h)
