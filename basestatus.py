class BaseStatus():
    """An abstract status stub responding to LCD events.

    The up and down buttons are reserved for menu cycling, but by
    implementing the ``pressed_right``, ``pressed_left``,
    ``pressed_select`` methods one can respond to user input.

    Parameters
    ----------
    lcd : LCD
      A physical display adapter that allows control of a display.

    """
    def __init__(self, lcd):
        self.lcd = lcd

    def pressed_right(self):
        """Respond to the "right" button."""
        raise NotImplementedError()

    def pressed_left(self):
        """Respond to the "left" button."""
        raise NotImplementedError()

    def pressed_select(self):
        """Respond to the "select" button."""
        raise NotImplementedError()

    def update_lcd(self, force=False):
        """Update the screen with info."""
        raise NotImplementedError()
