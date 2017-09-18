"""Keep track of when our dog goes outside. The LCD color will change
depending on how long it's been since he's been outisde and pooped.

"""

import time
import csv
from datetime import datetime as dt
import os

import numpy as np
import Adafruit_CharLCD as LCD
import RPi.GPIO as GPIO

from basestatus import BaseStatus, WHITE, RED, GREEN, BLUE, CYAN, MAGENTA, YELLOW

# Limits for when he should be outside
BEST_OUTSIDE = 6.
MAX_OUTSIDE = 10.
BEST_POOPING = 18.
MAX_POOPING = 28.

# Color selections
GOOD_COLOR = WHITE
PEE_COLOR = GREEN
POOP_COLOR = YELLOW
FLASH_COLOR =  WHITE
ERROR_COLOR = RED

DECIMALS = 1 # How many decimal places to round (eg. 3 decimals means 0.001 precision)
ALERT_FREQ = 1 # in flashes per second
SEC_PER_HOUR = 3600 # default: 3600

   
def severity(current, best, maxx):
    severity = (current - best) / (maxx - best)
    normed = min(max(severity, 0.), 1.)
    return normed

def color(outside, pooping):
    """Give a tuple of RGB based on time values."""
    if pooping >= BEST_POOPING:
        # Needs to poop
        out = POOP_COLOR
    elif outside >= BEST_OUTSIDE:
        # Needs to go outside (pooping optional)
        out = PEE_COLOR
    else:
        # We're all good
        out = GOOD_COLOR
    return out

class Dog(BaseStatus):
    last_pooping = dt.now()
    last_outside = dt.now()
    _status_pooping = None
    _status_outside = None
    flash_status = True
    logfile = "/home/mwolf/sheffield-bathroom-log.tsv"

    def __init__(self, lcd):
        self.lcd = lcd
        # Load the latest data from the log file
        self.load_datetimes()

    def pressed_select(self):
        """The dog has pooped."""
        self.register_trip(pooped=True)
    
    def pressed_left(self):
        """The dog has peed."""
        self.register_trip(pooped=True)
    
    def pressed_right(self):
        """The dog has peed."""
        self.register_trip(pooped=False)        

    def load_datetimes(self):
        """Read the latest datetime stamps from the log file."""
        if os.path.exists(self.logfile):
            last_poop = None
            last_out = None
            # Read the file
            with open(self.logfile) as tsvin:
                tsvin = csv.reader(tsvin, delimiter='\t')
                for line in tsvin:
                    last_out = line[0]
                    if line[1] == "True":
                        last_poop = line[0]
            self.last_outside = dt.strptime(last_out, self.datetime_fmt)
            self.last_pooping = dt.strptime(last_poop, self.datetime_fmt)

    def register_trip(self, pooped):
        self.last_outside = dt.now()
        if pooped:
            self.last_pooping = dt.now()
        # Logging
        with open(self.logfile, 'a') as f:
            line = '{timestamp}\t{pooped}\n'
            line = line.format(timestamp=dt.now().strftime(self.datetime_fmt), pooped=pooped)
            f.write(line)
        self.update_lcd(force=True)

    def elapsed_seconds(self, datetime_):
        out = datetime_.days * 3600 * 24 + datetime_.seconds + datetime_.microseconds / 1000000.
        return float(out)

    def update_lcd(self, force=False):
        outside_delta = self.elapsed_seconds(dt.now() - self.last_outside) / SEC_PER_HOUR
        pooping_delta = self.elapsed_seconds(dt.now() - self.last_pooping) / SEC_PER_HOUR
        # check if the LCD should be updated
        def isclose(a, b):
            if a is not None and b is not None:
                return abs(a - b) <= 10**(-DECIMALS)
            else:
                return False
        do_update = (not isclose(outside_delta, self._status_outside) or
                     not isclose(pooping_delta, self._status_pooping) or
                     force)
        # Check if it's a critical trip
        flashing = (outside_delta >= MAX_OUTSIDE or pooping_delta >= MAX_POOPING)
        if flashing:
            elapsed = (dt.now() - self.last_outside)
            elapsed_sec = self.elapsed_seconds(elapsed)
            even = bool(int(elapsed_sec * ALERT_FREQ * 2) % 2)
            # Flash two different colors if it's critical
            if even:
                c = FLASH_COLOR
            else:
                c = color(outside_delta, pooping_delta)
            self.lcd.set_color(*c)
        # Update the LCD with new times if necessary
        if do_update:
            self.write_lcd(outside_delta, pooping_delta)

    def write_lcd(self, outside, pooping):
        # Determine LCD color based on status values
        c = color(outside, pooping)
        self.lcd.set_color(*c)
        # Update the LCD
        self.lcd.clear()
        msg = 'Outside: {:.%df}h\n' % DECIMALS
        msg += 'Pooping: {:.%df}h' % DECIMALS
        msg = msg.format(outside, pooping)
        self.lcd.message(msg)
        # Reset status variables
        self._status_pooping = pooping
        self._status_outside = outside


        

