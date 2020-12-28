# Rhythmbox Fullscreen Plugin

![fullscreen](http://i216.photobucket.com/albums/cc33/benjaoming/Screenshotfrom2013-02-10195009_zps3f50706d.png)

### What does it do?

This python plugin gives you a stylish full screen window usable for parties etc.:

 - Pulsating hover effect
 - Album art
 - Smoothly animated progress bar
 - Control: Play/pause/skip
 - Scrolling by cursor position
 - Queued tracks merged
 - Full screen - or maximized window via the plugin preferences 
    
Then activate it and press the new Full Screen button
appearing at Rhythmbox's toolbar.

### Ubuntu package

Fossfreedom is maintaining a PPA on Launchpad with the latest release.
Click the link below to read instructions about adding PPA.

[ppa:fossfreedom/rhythmbox-plugins](https://launchpad.net/~fossfreedom/+archive/rhythmbox-plugins)

### Local-User installation:

First, run this:

<pre>
git clone https://github.com/benjaoming/rhythmbox-fullscreen
cd rhythmbox-fullscreen
</pre>

Then, run the install script according to your Rhythmbox version.

For rhythmbox versions 2.96 to 2.99.1:

<pre>
./install.sh --rb2
</pre>

For rhythmbox version 3.0.1 and later:

<pre>
./install.sh
</pre>


### Global-User (all-users) installation:

First, run this:

<pre>
git clone https://github.com/benjaoming/rhythmbox-fullscreen
cd rhythmbox-fullscreen
</pre>

Then, run the install script according to your Rhythmbox version.

For rhythmbox versions 2.96 to 2.99.1:

<pre>
./install.sh -g --rb2
</pre>

For rhythmbox version 3.0.1 and later:

<pre>
./install.sh -g
</pre>


### Known issues

Reports say that using Compiz on a 64-bit Virtualbox will trouble the progress bars and scrolling. However, using windowed mode (via the plugin preferences) should fix this. 

### Usage

 - Activate the plugin.
 - To enter full screen mode, find the menu item **View->Full Screen**.
 - ...or simply hit **F12**

### Technical stuff

The plugin uses custom drawn Cairo widgets in a DrawableArea and idle callbacks for animations. Everything is therefore vector graphics. 

If you find an error, please run Rhythmbox from terminal with the following option:

    rhythmbox -D RhythmboxFullscreen

### Credits

Thanks to [fossfreedom](https://github.com/fossfreedom/) for restructuring the plugin, packaging for Debian and tracking down bugs.
