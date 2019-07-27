import sys
import datetime as dt
import time

import unittest
from unittest import mock
from PyQt5 import QtWidgets
from PyQt5.QtTest import QSignalSpy

from humblepi.dogstatus import DogStatus, DogAction


class DogActionTest(unittest.TestCase):
    def test_time(self):
        action = DogAction()
        action.reset_time()
        self.assertEqual(action.seconds(), 0)
        self.assertEqual(action.time_string(), '0:00')
        # Now try with an arbitrary time
        now = dt.datetime.now()
        target_dt = now - dt.timedelta(seconds=522)
        action.reset_time(new_time=target_dt)
        self.assertEqual(action.seconds(), 522)
        self.assertEqual(action.time_string(), '0:08')
        # Now try with a time more than an hour
        now = dt.datetime.now()
        target_dt = now - dt.timedelta(seconds=4300)
        action.reset_time(new_time=target_dt)
        self.assertEqual(action.seconds(), 4300)
        self.assertEqual(action.time_string(), '1:11')
        # Now try with a time more than a day
        now = dt.datetime.now()
        target_dt = now - dt.timedelta(seconds=29 * 3600 + 60 * 24)
        action.reset_time(new_time=target_dt)
        self.assertEqual(action.seconds(), 105840)
        self.assertEqual(action.time_string(), '29:24')
    
    def test_pee_status(self):
        action = DogAction(seconds_warning=100, seconds_overdue=200)
        self.assertEqual(action.status(), action.states.NORMAL)
        # Check a warning status
        warning_time = dt.datetime.now() - dt.timedelta(seconds=105)
        action.reset_time(new_time=warning_time)
        self.assertEqual(action.status(), action.states.WARNING)
        # Check an overdue status
        overdue_time = dt.datetime.now() - dt.timedelta(seconds=205)
        action.reset_time(new_time=overdue_time)
        self.assertEqual(action.status(), action.states.OVERDUE)


class DogStatusTest(unittest.TestCase):
    def test_monitor_times(self):
        app = QtWidgets.QApplication(sys.argv)
        status = DogStatus()
        status_spy = QSignalSpy(status.pooping.status_changed)
        time_spy = QSignalSpy(status.pooping.time_changed)
        status.start()
        self.assertEqual(len(time_spy), 0)
        status_emitted = status_spy.wait(1)
        self.assertTrue(status_emitted)
        self.assertEqual(len(time_spy), 1)
    
    def test_update_mqtt(self):
        status = DogStatus()
        client = mock.MagicMock()
        status.update_mqtt(client=client)
        client.reconnect.assert_called_with()
        client.publish.assert_called_with(topic='dogstatus/sheffield/outside', payload='NORMAL')
