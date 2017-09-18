from datetime import datetime as dt, timedelta

import pandas as pd

from basestatus import BaseStatus, WHITE, RED, GREEN, BLUE, CYAN, MAGENTA, YELLOW

class SmokeStatus(BaseStatus):
    target = 0.333
    logfile = '/home/mwolf/smoking-log.tsv'
    last_msg = None
    bad_color = YELLOW
    good_color = WHITE

    def update_lcd(self, force=False):
        curr_avg = self.running_average()
        msg = "{:.3f} per day\n(target={:.3f})".format(curr_avg, self.target)
        needs_update = (msg != self.last_msg)
        if needs_update or force:
            self.lcd.clear()
            if curr_avg > self.target:
                self.lcd.set_color(*self.bad_color)
            else:
                self.lcd.set_color(*self.good_color)
            self.lcd.message(msg)
            self.last_msg = msg

    def running_average(self):
        days = 7
        df = pd.read_csv(self.logfile, names=('Datetime',))
        dates = pd.to_datetime(df.Datetime)
        last_three = dates.iloc[-3]
        delta = dt.now() - last_three
        days = delta.days + delta.seconds / 24. / 3600.
        running_average = 3. / days 
        return running_average

    def pressed_left(self):
        self.register_smoke()

    def pressed_right(self):
        self.register_smoke()

    def pressed_select(self):
        self.register_smoke()

    def register_smoke(self):
        self.last_outside = dt.now()
        # Logging
        with open(self.logfile, 'a') as f:
            line = '{timestamp}\n'
            line = line.format(timestamp=dt.now().strftime(self.datetime_fmt))
            f.write(line)
        self.update_lcd(force=True)
