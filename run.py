#!/usr/bin/python

import time
from contextlib import contextmanager

import Adafruit_CharLCD as LCD

from dogstatus import Dog, ERROR_COLOR
from ipstatus import IPStatus
from smokestatus import SmokeStatus

TICK = 0.1 # sleep time in seconds to prevent excessive button presses

def show_exception(e, lcd):
    # Notify user of exception
    lcd.set_color(*ERROR_COLOR)
    lcd.clear()
    # Prepare message for LCD display
    name = e.__class__.__name__
    CHARS = 16
    if len(name) >= CHARS:
        name = "{}\n{}".format(name[:CHARS], name[CHARS:])
    lcd.message(name)
    raise

@contextmanager
def wait_for_button(lcd):
    lcd.set_backlight(0)
    try:
        yield
    except NotImplementedError:
        backlight_off = True
        lcd.set_backlight(0)
    else:
        backlight_off = False
    # Wait for user to release buttons
    btns = [LCD.SELECT, LCD.LEFT, LCD.UP, LCD.DOWN, LCD.RIGHT]
    while True:
        pressed = False
        for btn in btns:
            if lcd.is_pressed(btn):
                pressed = True
        if not pressed:
            if backlight_off:
                lcd.set_backlight(1)
            break


def button_loop(lcd, statuses):
    """Start looping and wait for user input."""
    # Default to first status
    active_status = statuses[0]
    while True:
        # Have statuses respond to button presses
        if lcd.is_pressed(LCD.LEFT):
            with wait_for_button(lcd):
                active_status.pressed_left()
        elif lcd.is_pressed(LCD.RIGHT):
            with wait_for_button(lcd):
                active_status.pressed_right()
        elif lcd.is_pressed(LCD.SELECT):
            with wait_for_button(lcd):
                active_status.pressed_select()
        # Change active status on "up" or "down" buttons
        elif lcd.is_pressed(LCD.UP) or lcd.is_pressed(LCD.DOWN):
            with wait_for_button(lcd):
                old_idx = statuses.index(active_status)
                if lcd.is_pressed(LCD.UP):
                    new_idx = (old_idx + 1) % len(statuses)
                if lcd.is_pressed(LCD.DOWN):
                    new_idx = (old_idx - 1) % len(statuses)                
                active_status = statuses[new_idx]
                active_status.update_lcd(force=True)
        else:
            # Update the LCD display based on current dog status
            active_status.update_lcd()


def main(lcd):
    ## Prepare the list of statuses that will respond to commands
    # Sheffield the dog
    statuses = []
    sheffield = Dog(lcd=lcd)
    # For showing the current IP address
    statuses.append(sheffield)
    ipstatus = IPStatus(lcd=lcd)
    statuses.append(ipstatus)
    smokestatus = SmokeStatus(lcd=lcd)
    statuses.append(smokestatus)

    # Begin a loop that responds to button presses and updates LCD
    button_loop(lcd, statuses)                    

if __name__ == '__main__':
    # Prepare the LCD display
    lcd = LCD.Adafruit_CharLCDPlate()
    try:
        main(lcd)
    except BaseException as e:
        show_exception(e, lcd)
