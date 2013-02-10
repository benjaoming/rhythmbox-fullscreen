#Rhythmbox Fullscreen Plugin

![fullscreen](http://i216.photobucket.com/albums/cc33/benjaoming/Screenshotfrom2013-02-10195009_zps3f50706d.png)

###What does it do?

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

###Local-User installation:

<pre>
git clone https://github.com/benjaoming/rhythmbox-fullscreen
cd rhythmbox-fullscreen
./install.sh
</pre>

###Global-User (all-users) installation:

<pre>
git clone https://github.com/benjaoming/rhythmbox-fullscreen
cd rhythmbox-fullscreen
./install.sh -g
</pre>

###Known issues

Reports say that using Compiz on a 64-bit Virtualbox will trouble the progress bars and scrolling. However, using windowed mode (via the plugin preferences) should fix this. 

###Technical stuff

The plugin uses custom drawn Cairo widgets in a DrawableArea and idle callbacks for animations. Everything is therefore vector graphics. 

if you find an error, please run Rhythmbox from terminal with the following option:

    rhythmbox -D RhythmboxFullscreen
