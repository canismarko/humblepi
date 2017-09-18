import socket

from basestatus import BaseStatus

class IPStatus(BaseStatus):
    last_addr = None

    def update_lcd(self, force=False):
        curr_addr = self.ipaddr()
        if curr_addr != self.last_addr or force:
            self.lcd.set_color(1, 1, 1)
            # Update the LCD
            self.lcd.clear()
            msg = "IP Address:\n{}".format(curr_addr)
            self.lcd.message(msg)
            self.last_addr = curr_addr

    def ipaddr(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        addr = s.getsockname()[0]
        s.close()
        return addr
