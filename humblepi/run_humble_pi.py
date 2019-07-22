#!/usr/bin/env python

import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow


from humblepi.puppy_status_view import PuppyStatusView
from humblepi.dogstatus import DogStatus

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    puppy_view = PuppyStatusView()
    dog_status = DogStatus()
    dog_status.load_datetimes()
    # Prepare UI
    puppy_view.load_ui()
    puppy_view.show()
    # Connect signals and slots
    puppy_view.connect_dog_status(dog_status)
    dog_status.connect_puppy_view(puppy_view)
    # Start the status monitors
    dog_status.start()
    # Execute the Qt app
    sys.exit(app.exec_())
