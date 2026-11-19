=====================================================================
 PLEX NOW SHOWING - Raspberry Pi Poster Display
=====================================================================

WHAT IT DOES
------------
- Shuffles a random movie poster from your Plex "Movies" library
  every 30 seconds.
- When a movie starts PLAYING on your chosen player (for example an
  NVIDIA Shield), it shows that movie's poster under a sparkling
  "NOW SHOWING" banner.
- When the movie is paused or stopped, it goes back to shuffling.
- It restarts itself every 12 hours (and after any crash) so it never
  stays stuck.
- It is one Python file and needs nothing extra installed.


WHAT YOU NEED
-------------
- Raspberry Pi 3 Model B (or newer), microSD card (8 GB or larger),
  power supply, and a display connected to the Pi
- A Plex server on the same home network
- A Windows PC with:
    * Raspberry Pi Imager (to write the SD card)
    * PuTTY (to control the Pi; the PuTTY installer also includes
      "pscp", the tool used below to copy files)
- The files in this project:
    poster.py            the program
    install.sh           one-time installer for the Pi
    config.example.json  template for your settings
    README.txt           this file


=====================================================================
 STEP 1 - PUT THE OPERATING SYSTEM ON THE SD CARD
=====================================================================
1. Install and open Raspberry Pi Imager on your PC.
2. Choose Device:      Raspberry Pi 3
3. Choose OS:          Raspberry Pi OS (32-bit)
                       (the standard version WITH desktop - do NOT
                       pick "Lite", the display needs the desktop)
4. Choose Storage:     your SD card
5. When it offers to customize settings, set:
     - a username and password (write them down)
     - your Wi-Fi name and password
       (the Pi 3 Model B only supports 2.4 GHz Wi-Fi)
     - turn ON SSH (this is what PuTTY connects to)
6. Write the card, put it in the Pi, connect the display, and power
   it on. Wait 2-3 minutes for the first start.


=====================================================================
 STEP 2 - EDIT THE CONFIG FILE
=====================================================================
The program reads its settings from a file named config.json.

1. Make a copy of config.example.json and rename the copy to:
       config.json
2. Open config.json in Notepad and replace the placeholder values.
   Keep the quotation marks and commas exactly as they are.

   Example, filled in:

   {
     "plex_url": "http://192.168.1.30:32400",
     "plex_token": "paste-your-token-here",
     "player_name": "SHIELD",
     "player_machine_id": "",
     "libraries": ["Movies"],
     "rotate_seconds": 30,
     "poll_seconds": 2,
     "restart_hours": 12,
     "port": 8080
   }

   WHAT EACH SETTING MEANS
   plex_url           Address of your Plex server: http://, then the
                      server's IP address, then :32400
   plex_token         Your Plex token (see Step 3)
   player_name        Part of the player's name, e.g. SHIELD (not case
                      sensitive). Only this player triggers the banner.
   player_machine_id  Optional. If you have several similar players,
                      put the player's machine ID here instead.
   libraries          Names of your MOVIE libraries, spelled exactly as
                      in Plex. Example for two: ["Movies", "4K Movies"]
   rotate_seconds     Seconds between shuffled posters
   poll_seconds       How often it checks whether something is playing
   restart_hours      Auto-restart interval in hours (0 = never)
   port               Leave at 8080

   NEVER share your real config.json or put it on GitHub. It contains
   your Plex token.


=====================================================================
 STEP 3 - FIND YOUR PLEX TOKEN
=====================================================================
The token is a string of letters and numbers that lets the program
talk to your Plex server. Keep it private.

METHOD 1 (easiest)
1. In a browser go to  app.plex.tv  and sign in.
   (Use this address, not your server's IP address. Opening Plex by
   IP often leaves the token out of the web address.)
2. Open any movie.
3. Click the three dots (...) on the movie and choose "Get Info".
4. Click "View XML" at the bottom left of the window.
5. A new tab opens. Look at its address bar. It contains
       X-Plex-Token=XXXXXXXXXXXXXXXXXXXX
   The letters and numbers after the = sign (up to any & sign) are
   your token.

METHOD 2 (browser developer tools)
1. Open a movie in Plex Web and press F12.
2. Click the "Network" tab and refresh the page.
3. Click any request to your Plex server. In its Request URL or
   headers, find  X-Plex-Token=...

METHOD 3 (read it from the Plex server computer, Windows)
1. Press Windows key + R, type  regedit  and press Enter.
2. Go to
   HKEY_CURRENT_USER\Software\Plex, Inc.\Plex Media Server
3. Find the value named  PlexOnlineToken.

HOW TO FIND YOUR PLAYER NAME
1. Start any movie playing on the player (e.g. your Shield).
2. In a browser open (using your own address and token):
     http://YOUR-PLEX-IP:32400/status/sessions?X-Plex-Token=YOURTOKEN
3. Look for the "Player" part. Its title="..." and product="..."
   values show the player's name. Use a piece of it as player_name.
   The machineIdentifier there is the value for player_machine_id.


=====================================================================
 STEP 4 - FIND THE PI'S IP ADDRESS
=====================================================================
Any ONE of these works:
- Look in your router's list of connected devices for the Pi.
- Use the name you chose in Imager. In Windows Command Prompt:
       ping raspberrypi.local
  The numbers in the reply are the IP address. (Replace
  "raspberrypi" with your Pi's hostname if you changed it.)
- If the Pi has a keyboard attached, open a terminal and type:
       hostname -I


=====================================================================
 STEP 5 - CONNECT WITH PUTTY
=====================================================================
1. Open PuTTY.
2. Host Name:      the Pi's IP address (for example 192.168.1.60)
   Port:           22
   Connection type: SSH
3. Click Open.
4. The first time, a security alert appears. Click Accept.
5. "login as:" - type your Pi username and press Enter.
6. Type your password and press Enter. (Nothing shows while you
   type a password. That is normal.)
7. You are in when you see a prompt like:
       yourusername@raspberrypi:~ $

Test it by typing:
       hostname -I
It should print the Pi's IP address.


=====================================================================
 STEP 6 - COPY THE FILES TO THE PI (Windows Command Prompt)
=====================================================================
Put poster.py, install.sh and your config.json together in one
folder on your PC, for example your Downloads folder.

1. Click Start, type  cmd  and press Enter to open Command Prompt.
2. Go to the folder with the files:
       cd %USERPROFILE%\Downloads
   (If they are somewhere else, use that folder's path instead.)
3. Check the three files are there:
       dir poster.py install.sh config.json
4. Copy them to the Pi. Replace yourusername and the IP address with
   your own:

       pscp poster.py install.sh config.json yourusername@192.168.1.60:/home/yourusername/

5. The first time it asks whether to store the key - type  y  and
   press Enter. Then type your Pi password.
6. You will see each file listed as it copies.

If Command Prompt says "pscp is not recognized", use the full path:

       "C:\Program Files\PuTTY\pscp.exe" poster.py install.sh config.json yourusername@192.168.1.60:/home/yourusername/

Prefer clicking instead? WinSCP (free) lets you drag and drop the
same three files into your Pi home folder.


=====================================================================
 STEP 7 - INSTALL IT (PuTTY commands)
=====================================================================
In your PuTTY window, type these one at a time:

1. Make sure you are in your home folder and the files arrived:
       cd ~
       ls
   You should see poster.py, install.sh and config.json.

2. Run the installer:
       sudo bash install.sh
   It takes about 10 seconds and ends with the word "Done".

3. Restart the Pi:
       sudo reboot

PuTTY will disconnect. After about a minute the display opens on its
own and starts showing posters. No keyboard is needed from now on.

What the installer does:
- copies the files into  ~/poster
- sets up the poster program as a service that starts on every boot
  and restarts itself if it stops
- makes the Pi sign in to the desktop automatically
- turns off screen blanking
- opens the full-screen display (Chromium kiosk) on boot


=====================================================================
 STEP 8 - CHECK THAT IT IS WORKING
=====================================================================
Reconnect with PuTTY and type:

       systemctl status poster
You want to see "active (running)" in green. Press q to exit.

       journalctl -u poster -n 30
Look for a line like "Loaded 1500 posters". That means it reached your
Plex server and found your movies.

Then start a movie on your player. Within a few seconds the NOW
SHOWING banner and that movie's poster should appear. Pause or stop
the movie and it returns to shuffling.


=====================================================================
 USEFUL COMMANDS (type these in PuTTY)
=====================================================================
Is it running?                     systemctl status poster
Recent log messages                journalctl -u poster -n 50
Watch the log live (Ctrl+C stops)  journalctl -u poster -f
Restart the program                sudo systemctl restart poster
Stop the program                   sudo systemctl stop poster
Start the program                  sudo systemctl start poster
Restart the Pi                     sudo reboot
Shut the Pi down                   sudo shutdown now
Show the Pi's IP address           hostname -I

CHANGING SETTINGS LATER
1. Edit the config on the Pi:
       nano ~/poster/config.json
   Save with Ctrl+O then Enter. Exit with Ctrl+X.
2. Apply the change:
       sudo systemctl restart poster

UPDATING THE PROGRAM LATER
1. In Windows Command Prompt, in the folder with the new poster.py:
       pscp poster.py yourusername@192.168.1.60:/home/yourusername/poster/
2. In PuTTY:
       sudo systemctl restart poster
   The screen reloads by itself.


=====================================================================
 SCREEN ORIENTATION
=====================================================================
The display page is rotated for a screen mounted on its side. It is
set in the page styles inside poster.py, in the "#wrap" rule:

   top: 0;
   left: 100vw;
   transform: rotate(90deg);

- Upside down? Change those three lines to:
       top: 100vh;
       left: 0;
       transform: rotate(-90deg);
- Screen mounted normally (no rotation)? Replace the whole #wrap rule
  with:
       #wrap { position: absolute; inset: 0; display: flex;
               flex-direction: column; }

After editing, copy poster.py to the Pi again (see "Updating the
program") and restart it.


=====================================================================
 TROUBLESHOOTING
=====================================================================
"Loaded 0 posters" in the log
  - Check plex_url. From a PC on the same network, open it in a
    browser: http://YOUR-PLEX-IP:32400/web
  - Check plex_token is correct.
  - Check "libraries" matches the Plex library name exactly. The log
    lists the library names it found when there is no match.
  - Only movie-type libraries are used. TV libraries are ignored.

Posters shuffle but the banner never appears
  - Check player_name. Run the player-name steps in Step 3.
  - Only MOVIES trigger the banner. TV episodes are ignored.
  - Paused or stopped movies do not show the banner.

Black screen or nothing on the display
  - Check the status command in Step 8.
  - Reboot with  sudo reboot  and wait a full minute.
  - Make sure you installed Raspberry Pi OS WITH desktop (not Lite).

Cannot connect with PuTTY
  - Check the Pi is powered and on the network (router device list).
  - Check SSH was turned on in Imager (Step 1).
  - The Pi 3 Model B needs a 2.4 GHz Wi-Fi network.

"Permission denied" when copying files
  - Check the username and password, and that the destination path
    uses your own username.

Wrong file name on the Pi
  - The settings file must be named exactly  config.json  (not
    config.example.json and not config.json.txt). In Windows turn on
    "File name extensions" in File Explorer's View menu to check.


=====================================================================
 NOTES
=====================================================================
- Only movies are shown. TV shows and music are ignored.
- Your Plex token gives full access to your server. Do not post it
  online or commit config.json to GitHub. The .gitignore file in this
  project keeps it out automatically.
