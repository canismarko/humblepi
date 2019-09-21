import sys
import os
import datetime as dt
import pytz
import time

import unittest
from unittest import mock
from PyQt5 import QtWidgets
from PyQt5.QtTest import QSignalSpy

from humblepi.dogstatus import DogStatus, DogAction


chicago = pytz.timezone('America/Chicago')


class DogActionTest(unittest.TestCase):
    def test_time(self):
        action = DogAction()
        action.reset_time()
        self.assertEqual(action.seconds(), 0)
        self.assertEqual(action.time_string(), '0:00')
        # Now try with an arbitrary time
        now = chicago.localize(dt.datetime.now())
        target_dt = now - dt.timedelta(seconds=522)
        action.reset_time(new_time=target_dt)
        self.assertEqual(action.seconds(), 522)
        self.assertEqual(action.time_string(), '0:08')
        # Now try with a time more than an hour
        now = dt.datetime.now(chicago)
        target_dt = now - dt.timedelta(seconds=4300)
        action.reset_time(new_time=target_dt)
        self.assertEqual(action.seconds(), 4300)
        self.assertEqual(action.time_string(), '1:11')
        # Now try with a time more than a day
        now = dt.datetime.now(chicago)
        target_dt = now - dt.timedelta(seconds=29 * 3600 + 60 * 24)
        action.reset_time(new_time=target_dt)
        self.assertEqual(action.seconds(), 105840)
        self.assertEqual(action.time_string(), '29:24')
    
    def test_pee_status(self):
        action = DogAction(seconds_warning=100, seconds_overdue=200)
        self.assertEqual(action.status(), action.states.NORMAL)
        # Check a warning status
        warning_time = dt.datetime.now(chicago) - dt.timedelta(seconds=105)
        action.reset_time(new_time=warning_time)
        self.assertEqual(action.status(), action.states.WARNING)
        # Check an overdue status
        overdue_time = dt.datetime.now(chicago) - dt.timedelta(seconds=205)
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
        status.peeing.reset_time()
        status.pooping.reset_time()
        client = mock.MagicMock()
        status.update_mqtt(client=client)
        client.reconnect.assert_called_with()
        client.publish.assert_called_with(topic='dogstatus/sheffield/outside', payload='NORMAL')
    
    def test_load_datetimes(self):
        # Prepare a test file
        test_file = 'test-file.tsv'
        t0 = chicago.localize(dt.datetime(2019, 8, 4, 19, 55, 46))
        t1 = chicago.localize(dt.datetime(2019, 8, 5, 2, 59, 42))
        with open(test_file, mode='w') as fp:
            fp.writelines([
                f'{t0.isoformat()}	True\n',
                f'{t1.isoformat()}	False\n',
            ])
        # Load the datetimes from the file
        status = DogStatus()
        try:
            last_out, last_poop = status.load_datetimes(fpath=test_file)
        finally:
            os.remove(test_file)
        # Validate the retrieved datetimes
        self.assertEqual(last_out, t1)
        self.assertEqual(last_poop, t0)
    
    def test_load_old_datetimes(self):
        # Prepare a test file
        test_file = 'test-file.tsv'
        t0 = chicago.localize(dt.datetime(2019, 8, 4, 19, 55, 46))
        t1 = chicago.localize(dt.datetime(2019, 8, 5, 2, 59, 42))
        with open(test_file, mode='w') as fp:
            fp.writelines([
                '2019-08-04 19:55:46	True\n',
                '2019-08-05 02:59:42	False\n',
            ])
        # Load the datetimes from the file
        status = DogStatus()
        try:
            last_out, last_poop = status.load_datetimes(fpath=test_file)
        finally:
            os.remove(test_file)
        # Validate the retrieved datetimes
        self.assertEqual(last_out, t1)
        self.assertEqual(last_poop, t0)
    
    def test_log_action(self):
        status = DogStatus()
        log_file = 'test_file.tsv'
        # Make sure not stale files exist
        if os.path.exists(log_file):
            os.remove(log_file)
        # Call the code under test
        t = chicago.localize(dt.datetime(2019, 9, 21, 13, 38, 35))
        try:
            status.log_action(fpath=log_file, pooped=False, when=t)
            status.log_action(fpath=log_file, pooped=True, when=t)
            # Check the resulting log file
            with open(log_file, mode='r') as fp:
                line0, line1 = fp.readlines()
                self.assertEqual(line0, f'{t.isoformat()}\tFalse\n')
                self.assertEqual(line1, f'{t.isoformat()}\tTrue\n')
        finally:
            os.remove(log_file)
