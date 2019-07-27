import unittest
import sys

from PyQt5 import QtWidgets

from humblepi.puppy_status_view import PuppyStatusView

class PuppyStatusViewTestCase(unittest.TestCase):
    def setUp(self):
        self.app = QtWidgets.QApplication(sys.argv)
    
    def test_window_init(self):
        view = PuppyStatusView()
        self.assertTrue(view.window.isFullScreen)
