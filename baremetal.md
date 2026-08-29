Instructions for take a bare metal (unconfigured) Raspberry Pi from nothing to fully  
functional flockblocker. A Pi B+ has plenty of horsepower to function, but it is slow  
to boot with the latest (bloated) Raspberry Pi OS.  It will work fine though.  

See the Python source code for some set-up details.  Most of those details will be  
repeated here.

Using Raspberry Pi Imager, or other suitable image burning tool, burn the SD card with  
the latest 32-bit Raspberry Pi OS Lite.  The Lite version has none of the desktop GUI  
which is unused, but should not hurt anything if you want to load it for some reason.  
As of August 2026, The latest version of Pi OS is based on Trixie.  Older (and newer)  
versions should work also.  

You can do it in the Imager tool, or do it through firstboot, but you will need to set  
up a username password for your Pi.  The default pi user no longer exists.  

<b>  
sudo raspi-config  
</b>  
<br>
<br>

Go into System Options and enable wireless LAN if you need it.  
Go into Interface Options and enable SSH.  
Within Interface Options, select Serial Port, and chose Login Disable.  This will prevent  
interference with a serial GPS unit if you ever use one.  
If you desire overclocking (not required) you can enable that under Performance Options.  
Under Advanced Options, it is recommended to make logging Volatile which will log to memory.  

REBOOT the Raspberry Pi  
  
<b>  
sudo apt update  
  <br>
sudo apt upgrade  
  
</b>  
<br>
<br>
  
REBOOT the Raspberry Pi  

<b>
sudo apt install python3 gpsd gpsd-clients python-is-python3 python3-geopy python3-pandas locate vim python3-gps  
  
</b>
<br>
<br>
If you want to make sure your Pi logs to memory and does not fill up the SD card (not sure if  
this is actually a problem) you can modify /etc/fstab as follows  
<br>
<br>
<b>
tmpfs /var/log tmpfs defaults,noatime,mode=0755,size=20M 0 0  
<br>
tmpfs /tmp tmpfs defaults,noatime,mode=1777,size=6M 0 0  
  
</b>
<br>
<br>
REBOOT the Raspberry Pi  
<br>
<br>
Attach your GPS receiver and execute the following while ensuring your antenna has at least  
some clear view of the sky.  
<br>
<br>
<b>
cgps -s  
  
</b>
<br>
<br>
You should see inputs from your GPS receiver, and also a list of satellites it is tracking.  
Do NOT panic if it fails to show a fix (valid latitude and longitude).  Many receivers take  
a minute or more to obtain "first fix" on satellites.  

Once you are sure your receiver is working, you can create a dummy file for the lat/lon waypoints.  
You can put one, two, or ten waypoints in this file.  These should be coordinates that will NOT  
trigger the flock block. They are simply placeholders.  Format is lat,lon using negative numbers  
for south latitude and west longitude.  

1.234567,2.222222  
2.345678,-1.234567  

Load the flockblock Python script and modify two variables to suit your situation.  They are located  
below the functions (def) and separated with hash marks.

<b>
##############################################################  

lllist = '/home/user/latlon.csv' # Path to lat,lon list  
flockradius = 0.2 # Radius to block (km)  

</b>
<br>
<br>
Execute it from the command line (Ctrl-C to bail out).  
<br>
<br>
<b>
python flockblock.py  
  
</b>
<br>
<br>
IMPORTANT: for a first(ish) generation Pi (aka B+) you need to pass an environment variable  
when executing the code.
<br>
<br>
<b>
RPI_LGPIO_REVISION="800012" python flockblock.py  
  
</b>
<br>
<br>
You should see checks against the latlon waypoint file scrolling up the screen.  If all you see  
is Latitude: None Longitude: None, that means your GPS does not have a 2D or 3D fix.  Once you  
get a fix, you should see it comparing coordinates to each line of the waypoint file.  Your flockblock  
is working.  Once the hardware is set up, you will be able to add waypoints with the push of a  
button, and of course activate the relay when you are within radius of a waypoint.  
<br>
<br>
If you want flockblock to start automatically, you need to create a systemd service.  This will  
obviate the need to have a keyboard/monitor attached, or an SSH connection.  

Define flockblock.service in /etc/systemd/system.  ADJUST user and path appropriately.  
<br>
<b>    
[Unit]  
Description=Flock Blocking  
After=network.target  
[Service]  
Environment=RPI_LGPIO_REVISION="800012" # Only needed for Pi 1  
ExecStart=/usr/bin/python3 /home/user/path/flockblock.py  
WorkingDirectory=/home/user/path/  
Restart=always  
User=user  
StandardOutput=syslog  
StandardError=syslog  
[Install]  
WantedBy=multi-user.target  
  
</b>  

Enable and start service  
<br>
<b>  
sudo systemctl daemon-reload  
sudo systemctl enable flockblock.service   
sudo systemctl start flockblock.service  
</b>   

