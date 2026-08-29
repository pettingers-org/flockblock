# flockblock.py
GPS-based hardware activation with real-time geofencing 

flockblock.py

A simple script to check current location against a CSV file of latitude  
and longitude waypoints.  A cicular geofence is created around each waypoint,   
and if the current location is inside the geofence, activate a relay.  Indicators   
(LED activation) is provided for: Valid GPS fix, blocking status, and learn mode.  

External hardware is three LEDs with current limiting resistors, a momentary   
(learn) switch, and a relay with selectable trigger logic (set to ACTIVE=HIGH).  
Optionally, an ON-OFF-ON (SPDT) switch can be added to override the relay input.  

Designed to run on a Raspberry Pi SBC with a USB or serial GPS receiver.  
Has been tested on RPi 1 (B+), RPi 2, and RPi 3 running 32-bit Pi OS Lite (Trixie)  
but should run on older distributions.  See below for modules and configuration.  
Should also work on RPi 4 but it is overkill.  Has been tested with Adafruit  
"Ultimate GPS" serial receiver, u-blox 7 chipset USB receiver, and u-blox 8 chipset  
USB receiver.  Should work with any GPS receiver than can be polled by gpsd.  

See baremetal file for step-by-step process from a fresh Pi OS install.  

Operational notes:  
The learn switch (momentary) should be held until the learn LED starts flashing,  
and then released.  This should, within a few seconds, trigger a blocked condition  
and the blocking LED should come on.  This is because your location is now within  
the geofence for the location you just saved with the learn button.  Unless your  
vehicle is moving at the speed of light.  

You will not be able to record another waypoint until you move away from the one  
you just added (outside any geofence location).  

Of course you can manually add lat/lon data to the CSV file.  You do not need to  
use only the learn button.  You can do this while the flockblock.py script is  
running.  Currently the only way to remove a waypoint is manually with a text  
editor.

#----- install required modules and (optional) helpers  
sudo apt install python3 gpsd gpsd-clients python-is-python3 python3-geopy python3-pandas locate vim python3-gps  

#
#----- Modify /etc/fstab to log to RAM  
tmpfs /var/log tmpfs defaults,noatime,mode=0755,size=20M 0 0  
tmpfs /tmp tmpfs defaults,noatime,mode=1777,size=6M 0 0  

#----- Executing on Pi 1 (aka B+) requires faking revision number:    

RPI_LGPIO_REVISION="800012" python flockblock.py  

#----- Executing on newer Raspberry Pi does not require passing environment  

python flockblock.py  

#----- Test GPS receiver with:  

cgps -s  

#-----#-----# Optional #-----#-----#  

#----- Set up as a Service to run on boot  

Define flockblock.service in /etc/systemd/system.  *ADJUST user and path appropriately.*  

[Unit]  
Description=Flock Blocking  
After=network.target  
[Service]  
Environment=RPI_LGPIO_REVISION="800012" # only for Pi 1  
ExecStart=/usr/bin/python3 /home/user/path/flockblock.py   
WorkingDirectory=/home/user/path/   
Restart=always  
User=user  
StandardOutput=syslog  
StandardError=syslog  
[Install]  
WantedBy=multi-user.target  

Enable and start the service  

sudo systemctl daemon-reload   
sudo systemctl enable flockblock.service   
sudo systemctl start flockblock.service  

