import os
import logging
from enum import Enum
import datetime as dt
import pytz

from PyQt5 import uic, QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal
# from PyQt5.QtWidgets import QMainWindow, QPushButton

from .dogstatus import DogAction


log = logging.getLogger(__name__)


class PuppyStatusView(QtCore.QObject):
    timezone = pytz.utc
    
    ui_root = os.path.dirname(__file__)
    ui_file = os.path.join(ui_root, './dog_status_window.ui')
    ui_file_manual = os.path.join(ui_root, './manual_addition_dialog.ui')
    icoPeeBlack = None
    
    pee_button_clicked = pyqtSignal(object) # Datetime for when the "click" took place
    poop_button_clicked = pyqtSignal(object) # Datetime for when the "click" took place
    
    states = DogAction.states
    
    btn_flasher = QtCore.QTimer(singleShot=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_ui()
    
    def show(self):
        self.btn_flasher.start(500)
        self.window.show()
        self.set_layout()
    
    def connect_dog_status(self, status):
        status.pooping.status_changed.connect(self.update_pooping_status)
        status.pooping.time_changed.connect(self.update_pooping_time)
        status.peeing.status_changed.connect(self.update_peeing_status)
        status.peeing.time_changed.connect(self.update_peeing_time)
        self.timezone = status.timezone
    
    def update_pooping_time(self, new_time):
        self.ui.btnPoop.setText(new_time)
    
    def update_peeing_time(self, new_time):
        self.ui.btnPee.setText(new_time)
    
    def update_pooping_status(self, new_status):
        if new_status == self.states.WARNING:
            self.disconnect_signal(self.btn_flasher.timeout, self.style_poop_button)
            self.style_poop_button(highlight=True)
        elif new_status == self.states.OVERDUE:
            self.btn_flasher.timeout.connect(self.style_poop_button)
        else:
            self.disconnect_signal(self.btn_flasher.timeout, self.style_poop_button)
            self.style_poop_button(highlight=False)
    
    def update_peeing_status(self, new_status):
        if new_status == self.states.WARNING:
            self.disconnect_signal(self.btn_flasher.timeout, self.style_pee_button)
            self.style_pee_button(highlight=True)
        elif new_status == self.states.OVERDUE:
            self.btn_flasher.timeout.connect(self.style_pee_button)
        else:
            self.disconnect_signal(self.btn_flasher.timeout, self.style_pee_button)
            self.style_pee_button(highlight=False)
    
    def disconnect_signal(self, signal, slot):
        try:
            signal.disconnect(slot)
        except TypeError:
            pass
    
    def load_ui(self):
        # Load the Qt Designer .ui files
        Ui_FrameWindow, QMainWindow = uic.loadUiType(self.ui_file)
        Ui_ManualWindow, QManualDialog = uic.loadUiType(self.ui_file_manual)
        log.debug("Built windows using uic") 
        # Create the UI elements
        self.window = QMainWindow()
        self.manual_dialog = QManualDialog()
        self.ui = Ui_FrameWindow()
        self.ui_manual = Ui_ManualWindow()
        self.ui.setupUi(self.window)
        self.ui_manual.setupUi(self.manual_dialog)
        # Load the button icons from disk
        self.icoPeeWhite = QtGui.QIcon(os.path.join(self.ui_root, 'dog-peeing-icon-white.svg'))
        self.icoPeeBlack = QtGui.QIcon(os.path.join(self.ui_root, 'dog-peeing-icon.svg'))
        self.icoPoopBlack = QtGui.QIcon(os.path.join(self.ui_root, 'dog-pooping-icon.svg'))
        self.icoPoopWhite = QtGui.QIcon(os.path.join(self.ui_root, 'dog-pooping-icon-white.svg'))
        # Set the default button states
        self.style_pee_button(highlight=False)
        self.style_poop_button(highlight=False)
        # Connect UI signals to view signals
        self.ui.btnPee.clicked.connect(self.pee_button_clicked.emit)
        self.ui.btnPoop.clicked.connect(self.poop_button_clicked.emit)
        # Connect signals for manually adding times
        self.ui.btnManualAdd.clicked.connect(self.show_manual_add_dialog)
        self.ui_manual.btnCancel.clicked.connect(self.manual_dialog.hide)
        self.ui_manual.btnOK.clicked.connect(self.add_manual_event)

    def add_manual_event(self, *args, **kwargs):
        # emit the selected datetime signals
        new_datetime = self.ui_manual.dteTarget.dateTime().toPyDateTime()
        new_datetime = self.timezone.localize(new_datetime)
        if self.ui_manual.chkPeed.isChecked():
            self.pee_button_clicked.emit(new_datetime)
        if self.ui_manual.chkPooped.isChecked():
            self.poop_button_clicked.emit(new_datetime)
        # Hide the dialog
        self.manual_dialog.hide()
    
    def show_manual_add_dialog(self, *args, **kwargs):
        # Set the default datetime value to now
        now = dt.datetime.now()
        now = QtCore.QDateTime(now.year, now.month, now.day, now.hour, now.minute)
        self.ui_manual.dteTarget.setDateTime(now)
        self.manual_dialog.showFullScreen()
    
    def style_pee_button(self, highlight=None):
        """Decide how to style the peeing button.
        
        If `highlight` is omitted, the button will be toggled.
        
        """
        if highlight is None:
            highlight = not getattr(self.ui.btnPee, 'highlighted', True)
        # Determine how to style the button
        if highlight:
            css = 'background-color: yellow;'
            icon = self.icoPeeBlack
        else:
            css = ''
            icon = self.icoPeeBlack
        # Update the UI elements
        self.ui.btnPee.highlighted = highlight
        self.ui.btnPee.setIcon(icon)
        self.ui.btnPee.setIconSize(QtCore.QSize(90, 90))
        self.ui.btnPee.setStyleSheet(css)
    
    def style_poop_button(self, highlight=None):
        """Decide how to style the pooping button.
        
        If `highlight` is omitted, the button will be toggled.
        
        """
        if highlight is None:
            highlight = not getattr(self.ui.btnPoop, 'highlighted', True)
        # Determine how to style the button
        if highlight:
            css = "background-color: brown; color: white;"
            icon = self.icoPoopWhite
        else:
            css = ''
            icon = self.icoPoopBlack
        # Update the UI elements
        self.ui.btnPoop.highlighted = highlight
        self.ui.btnPoop.setIcon(icon)
        self.ui.btnPoop.setIconSize(QtCore.QSize(90, 90))
        self.ui.btnPoop.setStyleSheet(css)        
    
    def set_layout(self):
        self.window.showFullScreen()
        # Hide the cursor when over the window
        self.window.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
        self.manual_dialog.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
