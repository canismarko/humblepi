import unittest
import sys
import datetime as dt

from PyQt5 import QtWidgets, QtCore

from humblepi.puppy_status_view import PuppyStatusView

class PuppyStatusViewTestCase(unittest.TestCase):
    def setUp(self):
        self.app = QtWidgets.QApplication(sys.argv)
    
    def test_window_init(self):
        view = PuppyStatusView()
        self.assertTrue(view.window.isFullScreen)
    
    def test_status_indicators(self):
        """Test indicators for connection with the internet and MQTT
        server.
        
        """
        view = PuppyStatusView()
        status_bar = view.ui.statusbar
        self.assertIn(view.ui.lblMQTTStatus, status_bar.children())
        self.assertIn(view.ui.lblWifiStatus, status_bar.children())


class ManualAdditionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = QtWidgets.QApplication(sys.argv)
    
    def test_manual_window_init(self):
        view = PuppyStatusView()
        self.assertTrue(view.manual_dialog)

    def test_show_manual_dialog(self):
        view = PuppyStatusView()
        view.show_manual_add_dialog()
        now = dt.datetime.now()
        now = QtCore.QDateTime(now.year, now.month, now.day, now.hour, now.minute)
        self.assertEqual(view.ui_manual.dteTarget.dateTime(), now)

    def test_submit_button(self):
        view = PuppyStatusView()
        view.show_manual_add_dialog()
        view.ui_manual.btnOK.click()
        self.assertFalse(view.manual_dialog.isVisible())
