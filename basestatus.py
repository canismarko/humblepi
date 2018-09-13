# Color definitions
WHITE = (1., 1., 1.)
RED = (1., 0., 0.)
GREEN = (0., 1., 0.)
BLUE = (0., 0., 1.)
CYAN = (0., 1., 1.)
MAGENTA = (1., 0., 1.)
YELLOW = (1., 1., 0.)


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
    datetime_fmt = "%Y-%m-%d %H:%M:%S"
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
