#!/usr/bin/env python3

import sys
import logging
from pathlib import Path
import argparse

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow


from humblepi.puppy_status_view import PuppyStatusView
from humblepi.dogstatus import DogStatus

log = logging.getLogger(__name__)


def main():
    # Parse command line arguments
    args = parse_args()
    # Prepare logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logfile = Path("~/humlepi.log").expanduser()
        logging.basicConfig(filename=logfile, level=logging.INFO)
    # Create the Qt objections
    app = QtWidgets.QApplication(sys.argv)
    puppy_view = PuppyStatusView()
    dog_status = DogStatus()
    dog_status.load_datetimes()
    # Connect signals and slots
    puppy_view.connect_dog_status(dog_status)
    dog_status.connect_puppy_view(puppy_view)
    # Start the status monitors
    dog_status.prepare_mqtt()
    dog_status.start()
    # Prepare UI
    puppy_view.load_ui()
    puppy_view.show()
    # Execute the Qt app
    sys.exit(app.exec_())


def parse_args():
    parser = argparse.ArgumentParser(description='Show a UI about when the dog last peed/pooped.')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='provide additional logging')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
