"""
flockblock.py

A simple script to check current location against a CSV file of latitude 
and longitude waypoints.  A cicular geofence is created around each waypoint, 
and if the current location is inside the geofence, pull a relay.  Indicators 
(LED activation) is provided for: Valid GPS fix, blocking status, and learn mode.

External hardware is three LEDs with current limiting resistors, a momentary 
(learn) switch, and a relay with selectable trigger logic (set to ACTIVE=LOW).
Optionally an ON-OFF-ON SPDT switch can be added for relay override.


#----- install required modules and (optional) helpers
sudo apt install python3 gpsd gpsd-clients python-is-python3 python3-geopy python3-pandas locate vim python3-gps

#
#----- Modify /etc/fstab to log to RAM
tmpfs /var/log tmpfs defaults,noatime,mode=0755,size=20M 0 0
tmpfs /tmp tmpfs defaults,noatime,mode=1777,size=6M 0 0

#----- Executing on Pi 1 requires faking revision number:  

RPI_LGPIO_REVISION="800012" python flockblock.py

#----- Test GPS receiver with: 

cgps -s

#----- Set up as a Service to run on boot

     Define flockblock.service in /etc/systemd/system.  ADJUST user and path appropriately.

[Unit]
Description=Flock Blocking
After=network.target
[Service]
# Environment=RPI_LGPIO_REVISION="800012" # for Pi 1
ExecStart=/usr/bin/python3 /home/pi/path 
WorkingDirectory=/home/pi/path/ 
Restart=always
User=pi
StandardOutput=syslog
StandardError=syslog
[Install]
WantedBy=multi-user.target

     Enable and start service

sudo systemctl daemon-reload 
sudo systemctl enable flockblock.service 
sudo systemctl start flockblock.service

"""

import gps # For manipulation of gpsd data
import csv # For parsing lat/lon data file
import time
import RPi.GPIO as GPIO # For GPIO inpt and output manipulation
from geopy.distance import great_circle # For computation of geofence great circle distance
##############################################


def is_inside_geofence(point, center, radius_km):
    """
    Check if a point is inside a circular geofence.
    
    :param point: Tuple of (latitude, longitude) for the point to check.
    :param center: Tuple of (latitude, longitude) for the geofence center.
    :param radius_km: Radius of the geofence in kilometers.
    :return: Boolean indicating if the point is inside the geofence.
    """
    distance = great_circle(center, point).kilometers
    print(f"Distance: {round((distance * 1000), 2)} m\n")
    return distance <= radius_km



def scanlist(latlonlist, currentlat, currentlon, radius):
    """
    Scan through a list of waypoints and compare them to the current position.  Stop and return if waypoint is close.

    :param latlonlist: The CSV list of waypoints.  Should be a valid path
    :param currentlat: Current latitude to be saved.
    :param currentlon: Current longituude to be saved.
    :param radiuus: radius in km from the waypoint for positive result
    :return: A Boolean indicating the waypoint is within [radiuus] of the current position.
   
    """
    with open(latlonlist, newline='', encoding='utf-8') as f: # Open the CSV file for reading
    
        reader = csv.reader(f, quoting=csv.QUOTE_NONNUMERIC)
        for row in reader:
        
            print (row)
            check_point = (currentlat, currentlon)
            # radius from call
            center = row
        
            is_inside = is_inside_geofence(check_point, center, radius)
            print(f"Is inside geofence: {is_inside}")
            print("-----------------------------------------")
            if is_inside:
                return is_inside
    return is_inside



def learnbutton(latlonlist, currentlat, currentlon):
    """
    Upon activation of a switch, save the current location to the database as a waypoint.
    :param latlonlist: The CSV list of waypoints.  Should be a valid path
    :param currentlat: Current latitude to be saved.
    :param currentlon: Current longituude to be saved.
    :return: A Boolean indicating the lat/lon was written to the file.
    """
    iswritten = False

    with open(latlonlist, 'a', newline='', encoding='utf-8') as f: # Open the file for writing

        f.write(f"{currentlat},{currentlon}\n") # Write the tuple
        iswritten = True

    return iswritten

##############################################################

lllist = '/home/charlie/latlon.csv' # Path to lat,lon list
flockradius = 0.1 # Radius to block (km)

GPIO.setmode(GPIO.BCM) # Set to Broadcom numbers (not pin numbers)
# REMEMBER: Raspberry Pi GPIO is 3v3, not 5V
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Learn button with pulldown
GPIO.setup(18, GPIO.OUT) # Learn LED output
GPIO.setup(27, GPIO.OUT) # Currently blocking LED
GPIO.setup(22, GPIO.OUT) # Relay output
GPIO.setup(23, GPIO.OUT) # GPS valid LED output
GPIO.output(18, GPIO.LOW) # Learn LED default to off
GPIO.output(27, GPIO.LOW) # Currenly blocking LED default to off
GPIO.output(22, GPIO.LOW) # Relay default to off (active when high)
GPIO.output(23, GPIO.LOW) # GPS valid LED default to off (valid when high)

##############################################################

#main()

while True:

    gpsd = gps.gps()
    gpsd.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

    for report in gpsd:
        if report['class'] == 'TPV':
            print(f"          Latitude: {report.get('lat')}")
            print(f"          Longitude: {report.get('lon')}\n")
            clat = report.get('lat')
            clon = report.get('lon')
            if clat is not None: # GPS has >= 2D fix
                GPIO.output(23, GPIO.HIGH) # Set GPS valid LED
                clat = round(clat, 6)
                clon = round(clon, 6)
            else: # No valid position fix
                GPIO.output(23, GPIO.LOW) # Turn off GPS valid LED
            break



    if clat is not None: # Valid 2D or 3D fix

        checkresult = scanlist(lllist, clat, clon, flockradius) # Check current position against geofence of lot/lon list waypoints

        print(f"Current verdict is: {checkresult}")
        if checkresult: #Some relays are initially sticky
            GPIO.output(22, GPIO.HIGH) # Kick blocking relay
            time.sleep(0.1)
            GPIO.output(22, GPIO.LOW) # Kick blocking relay

        while checkresult: # Inside the geofence boundary
            GPIO.output(27, GPIO.HIGH) # Turn on blocking LED
            GPIO.output(22, GPIO.HIGH) # Turn on blocking relay
            time.sleep(2)
            checkresult = scanlist(lllist, clat, clon, flockradius) # Do not proceed outside loop until we are OUTSIDE the geofence boundary

        GPIO.output(27, GPIO.LOW) # Outside the geofence.  Turn off blocking LED
        GPIO.output(22, GPIO.LOW) # outside the geofence.  Turn off relay 
        time.sleep(0.5)


        print("=================================================================\n")

        if GPIO.input(17): # Learn button has been pressed
            for i in range(10): # Blink learn LED
                GPIO.output(18, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(18, GPIO.LOW)
                time.sleep(0.2)

            print(f"Saving LAT/LON {clat},{clon}\n")
            iswritten = learnbutton(lllist, clat, clon) # Write the current lat/lon to the list
            print(f"    {iswritten}\n")
        time.sleep(2)

# END
