"""Keep track of when our dog goes outside. The LCD color will change
depending on how long it's been since he's been outisde and pooped.

"""

import time
import csv
import datetime as dt
import os
from typing import Optional
import enum
import configparser
import logging

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from paho.mqtt import client as mqtt_client

from basestatus import BaseStatus, WHITE, RED, GREEN, BLUE, CYAN, MAGENTA, YELLOW

log = logging.getLogger(__name__)

# Limits for when he should be outside
BEST_OUTSIDE = 6.
MAX_OUTSIDE = 8.
BEST_POOPING = 18.
MAX_POOPING = 24.

# Color selections
GOOD_COLOR = WHITE
PEE_COLOR = GREEN
POOP_COLOR = YELLOW
FLASH_COLOR =  WHITE
ERROR_COLOR = RED

DECIMALS = 1 # How many decimal places to round (eg. 3 decimals means 0.001 precision)
ALERT_FREQ = 1 # in flashes per second
SEC_PER_HOUR = 3600 # default: 3600

STATUS_FILE = '/tmp/dogstatus' # A file in which to write the current state

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


class DogAction(QtCore.QObject):
    last_time = dt.datetime.now() # type: dt.datetime
    _last_status = 0
    _last_time = '--:--'
    seconds_warning = 3600
    seconds_overdue = 3600
    time_speedup = 1
    
    # Signals
    status_changed = pyqtSignal(int)
    time_changed = pyqtSignal(str)
    
    # Possible states
    class states(enum.IntEnum):
        UNKNOWN = 0
        NORMAL = 1
        WARNING = 2
        OVERDUE = 3
    
    def __init__(self, seconds_warning: int=3600, seconds_overdue: int=3600, *args, **kwargs):
        self.last_time = dt.datetime.now()
        self.seconds_warning = seconds_warning
        self.seconds_overdue = seconds_overdue
        return super().__init__(*args, **kwargs)
    
    def reset_time(self,
                   new_time: Optional[dt.datetime]=None):
        """Set the current time as the last action time.
        
        Parameters
        ==========
        new_time :
          The new datetime to set. If ommitted, the current time will
          be used.
        
        """
        if new_time is None:
            new_time = dt.datetime.now()
        self.last_time = new_time
    
    def seconds(self) -> int:
        """Return the time (in seconds) since puppy has taken this action."""
        now = dt.datetime.now()
        elapsed_time = now - self.last_time
        seconds = int(elapsed_time.total_seconds() * self.time_speedup)
        return seconds
    
    def time_string(self) -> str:
        """Prepare a string of how long it's been since puppy went outside."""
        seconds = self.seconds()
        days = int(seconds / (24 * 3600))
        hours = int((seconds % (24 * 3600)) / 3600)
        minutes = int((seconds % 3600) / 60)
        # Prepare the formatted string
        if days:
            fmt = '{days}:{hours:02d}:{minutes:02d}'
        else:
            fmt = '{hours}:{minutes:02d}'
        time_str = fmt.format(days=days, hours=hours, minutes=minutes)
        return time_str
    
    def status(self) -> int:
        """Determine whether this action is overdue or not.
        
        Returns
        =======
        status
          A member of self.states enum showing the current status
          (eg. self.states.NORMAL).
        
        """
        seconds = self.seconds()
        if 0 <= seconds < self.seconds_warning:
            status = self.states.NORMAL
        elif self.seconds_warning <= seconds < self.seconds_overdue:
            status = self.states.WARNING
        elif self.seconds_overdue <= seconds:
            status = self.states.OVERDUE
        else:
            status = self.states.UNKNOWN
        return status
    
    def check_status_change(self):
        """Compare current and last seen status, and emit a signal if it
        changed."""
        # Check overdue status
        new_status = self.status()
        if new_status != self._last_status:
            self.status_changed.emit(new_status)
            self._last_status = new_status
        # check time string
        new_time = self.time_string()
        if new_time != self._last_time:
            self.time_changed.emit(new_time)
            self._last_time = new_time


def load_config():
    config = configparser.ConfigParser()
    config['MQTT'] = {
        'username': '',
        'password': '',
        'hostname': 'localhost',
        'port': 8883,
        'use_tls': True,
    }
    config.read(os.path.expanduser('~/.humblepirc'))
    return config


class DogStatus(QtCore.QThread):
    dog_name = 'sheffield'
    peeing = DogAction(seconds_warning=6*3600, seconds_overdue=8*3600)
    pooping = DogAction(seconds_warning=18*3600, seconds_overdue=24*3600)
    # peeing = DogAction(seconds_warning=6*60, seconds_overdue=8*60)
    # pooping = DogAction(seconds_warning=18*60, seconds_overdue=24*60)
    logfile = "/home/mwolf/sheffield-bathroom-log.tsv"
    datetime_fmt = "%Y-%m-%d %H:%M:%S"
    mqtt_client = None
    
    def prepare_mqtt(self):
        config = load_config()['MQTT']
        # Log into the MQTT client
        self.mqtt_client = mqtt_client.Client()
        if config.getboolean('use_tls'):
            self.mqtt_client.tls_set()
            log.debug("TLS enabled for MQTT")
        self.mqtt_client.username_pw_set(
            username=config['username'],
            password=config['password'])
        log.debug("Connecting to MQTT server '%s:%d'",
                  config['hostname'], config.getint('port'))
        self.mqtt_client.connect(host=config['hostname'],
                                 port=config.getint('port'))
        # Connect signals for MQTT client
        self.peeing.status_changed.connect(self.update_mqtt)
        self.pooping.status_changed.connect(self.update_mqtt)
    
    def run(self):
        # Start loop waiting for status changes
        while True:
            self.pooping.check_status_change()
            self.peeing.check_status_change()
            time.sleep(1)
    
    def log_poop(self):
        self.log_action(pooped=True)
    
    def log_pee(self):
        self.log_action(pooped=False)
    
    def log_action(self, pooped=True):
        # Logging
        with open(self.logfile, 'a') as f:
            line = '{timestamp}\t{pooped}\n'
            line = line.format(timestamp=dt.datetime.now().strftime(self.datetime_fmt), pooped=pooped)
            f.write(line)
    
    def load_datetimes(self):
        """Read the latest datetime stamps from the log file."""
        if os.path.exists(self.logfile):
            last_poop = None
            last_out = None
            # Read the file
            with open(self.logfile) as tsvin:
                tsvin = csv.reader(tsvin, delimiter='\t')
                for line in tsvin:
                    if line[0][0] == '#':
                        pass
                    elif line[1] == "True":
                        last_poop = line[0]
                    else:
                        last_out = line[0]
            if last_out is not None:
                self.peeing.reset_time(dt.datetime.strptime(last_out, self.datetime_fmt))
            if last_poop is not None:
                self.pooping.reset_time(dt.datetime.strptime(last_poop, self.datetime_fmt))
    
    def connect_puppy_view(self, view):
        view.pee_button_clicked.connect(self.peeing.reset_time)
        view.pee_button_clicked.connect(self.peeing.check_status_change)
        view.pee_button_clicked.connect(self.log_pee)
        view.poop_button_clicked.connect(self.pooping.reset_time)
        view.poop_button_clicked.connect(self.pooping.check_status_change)
        view.poop_button_clicked.connect(self.log_poop)
    
    def update_mqtt(self, new_state=None, client=None):
        # Determine the most severe state
        max_state = max(self.pooping.status(), self.peeing.status())
        # Send the message to the MQTT server
        topic = 'dogstatus/{}/outside'.format(self.dog_name)
        payload = max_state.name
        if client is None:
            client = self.mqtt_client
        client.reconnect()
        msg = client.publish(topic=topic, payload=payload)
        if msg.is_published():
            log.debug("Message successfully published.")
        else:
            log.warning("MQTT message not published.")
