"""
    pd9530
    ~~~~~~

    Library to interact with a PD9530 handheld scanner

    To get a demo, just run "python pd9530.py COM6"

    :copyright: 02.2016 by Markus Ullmann, mail@markus-ullmann.de
    :license: BSD-3
"""

__version__ = "1.0.3"

import array
import io
import logging
import sys
import time

import serial

serial_logger = logging.getLogger('serialComm')

CMD_MODE_PICTURE_AUTO = "00"
CMD_MODE_PICTURE_TRIGGER = "11"
CMD_MODE_PICTURE_CODEREAD = "21"

CMD_MODE_PICTURE_BMP = 0
CMD_MODE_PICTURE_JPEG = 1
CMD_MODE_PICTURE_JPEG2000 = 2
CMD_MODE_PICTURE_TIFF = 3

class PD9530(object):
    """Interface to interact with Datalogic PD9530 in USB-COM or RS232 mode"""

    def __init__(self, com_port="COM1", baudrate=115200):
        super(PD9530, self).__init__()
        self.serial = serial.serial_for_url(
                com_port,
                baudrate,
                parity="N",
                rtscts=False,
                xonxoff=False,
                timeout=0,
                do_not_open=True)
        self.sio = None
        self.unhandled_messages = []
        self.model = "Unknown"
        self.timeout = 5

        self.pending_line = []

    def attach(self):
        """Attaches to scanner"""

        for i in range(self.timeout*5):
            try:
                if not self.serial.isOpen():
                    self.serial.open()
                serial_logger.debug("Port open!")
                break
            except serial.SerialException as e:
                if "31" in str(e):
                    serial_logger.debug("Scanner not active yet")
                    time.sleep(0.2)
                else:
                    raise

        # Go for it once again, possibly explode to pass it along
        if not self.serial.isOpen():
            self.serial.open()

        self.sio = io.BufferedRWPair(self.serial, self.serial)

    def close(self):
        """Closes stream if open"""

        if self.serial.isOpen():
            self.serial.close()

    def send_command(self, cmd):
        """Sends given command, opens com if needed"""

        if not self.serial.isOpen():
            self.attach()

        cmd += '\r'
        serial_logger.debug("sending command: %s" % cmd)
        self.sio.write(cmd.encode('utf-8'))
        self.sio.flush()

    def read_non_blocking(self):
        """Performs a non-blocking read call on serial"""

        line = []
        lines = []

        if self.serial.in_waiting > 0:
            buf = self.sio.read(self.serial.in_waiting)
            for byte in buf:
                self.pending_line.append(byte)
                if byte == 13:
                    finalized_line = array.array("B", self.pending_line).tostring().decode("utf-8")
                    serial_logger.debug("Completed line: %s" % finalized_line)
                    lines.append(finalized_line)
                    self.pending_line = []

        return lines

    def readlines(self, timeout=5, return_on_completed_newline=True):
        """Reading response from reader with timeout"""

        lines = []

        for i in range(timeout*10):
            done = False
            read_lines = self.read_non_blocking()
            if read_lines:
                lines.extend(read_lines)
                if return_on_completed_newline:
                    break

            time.sleep(0.1)

        return lines

    def get_device_id(self):
        """Returns device ID"""

        self.send_command("$+$!")
        self.model = self.readlines()[0]

        return self.model

    def set_config_mode_start(self):
        """Switches device to config mode"""

        self.send_command("$S")

    def set_config_mode_end(self):
        """Switches device out of config mode"""

        self.send_command("$s")

    def set_picture_mode_start(self, capture_start=CMD_MODE_PICTURE_TRIGGER, contrast=0, brightness=0):
        """Switch to picture mode"""

        if contrast < -255 or contrast > 255:
            raise ValueError("contrast out of range, allowed from -255 to 255")
        if brightness < -255 or brightness > 255:
            raise ValueError("brightness out of range, allowed from -255 to 255")

        cmd = "x0"
        cmd += str(capture_start).zfill(2)
        cmd += "0"

        cmd += ("%x" % brightness).zfill(2)
        cmd += ("%x" % contrast).zfill(2)
        cmd = cmd.replace("-", "")

        if brightness < 0:
            cmd += "01"
        else:
            cmd += "00"

        if contrast < 0:
            cmd += "01"
        else:
            cmd += "00"

        self.send_command(cmd)

    def set_picture_mode_fetch(self):
        """Sets transmit mode if a picture is available on device"""

        self.send_command("x030000000000")

    def set_picture_mode_end(self):
        """Exits / resets picture mode"""

        self.send_command("x040000000000")

    def get_picture(self, capture_start=CMD_MODE_PICTURE_TRIGGER, contrast=0, brightness=0):
        """Switches to picture mode, captures one, switches to normal mode and returns picture (and code if requested)"""

        self.set_picture_mode_start(capture_start, contrast, brightness)

        content_length = 0
        content_type = -1

        photo_ready = False
        while not photo_ready:
            for line in self.readlines():
                if not line.startswith("$i"):
                    self.unhandled_messages.append(line)
                    continue
                else:
                    content_type = int(line[3:4], 16)
                    content_length = int(line[4:12], 16)
                    photo_ready = True

        if not content_length:
            return (None, None)

        if content_type == CMD_MODE_PICTURE_BMP:
            content_type_name = "BMP"
        elif content_type == CMD_MODE_PICTURE_JPEG:
            content_type_name = "JPEG"
        elif content_type == CMD_MODE_PICTURE_JPEG2000:
            content_type_name = "JPEG2K"
        elif content_type == CMD_MODE_PICTURE_TIFF:
            content_type_name = "TIFF"
        else:
            serial_logger.warn("Unhandled picture type %s" % content_type)
            content_type_name = "unknown"

        serial_logger.debug("Image ready, length: %i, type: %s" % (content_length, content_type_name))
        self.set_picture_mode_fetch()

        imagedata = []
        while len(imagedata) < content_length:
            imagedata.append(self.sio.read())

        serial_logger.debug("Completed fetching image")
        self.set_picture_mode_end()
        for line in self.readlines():
            if line and not line.startswith("$b"):
                self.unhandled_messages.append(line)

        return imagedata, content_type_name


def _flush_input():
    """clears input buffer so we don't spit stuff to terminal"""

    import msvcrt
    while msvcrt.kbhit():
        msvcrt.getch()


def endless_code_scanning(com_port, echo):
    """Use this as stub if you just want to use the scanner to send keys"""

    scanner = PD9530(com_port)
    print("Please move scanner within %s secs to wake it up, checking on %s" % (scanner.timeout, scanner.serial.port))
    print("-"*70)

    try:
        scanner.attach()
    except serial.SerialException:
        print("Did not detect scanner. Wrong port?")
        sys.exit(1)

    print("OK, port open. Connected device:")
    print(scanner.get_device_id())
    print("-"*70)
    print("Now scanning codes and sending them as keystrokes")
    print("Press CTRL-C to exit")

    import win32com.client as comclt
    wsh = comclt.Dispatch("WScript.Shell")
    while True:
        try:
            lines = scanner.readlines()
            for line in lines:
                for char in line:
                    if echo:
                        print("Received code: %s" % char)
                    serial_logger.info("Received code: %s" % char)
                    if char == '{':
                        char = char.replace("{", "{{}")
                    elif char == '}':
                        char = char.replace("}", "{}}")
                    wsh.SendKeys(char)
        except KeyboardInterrupt:
            break

    scanner.close()
    _flush_input()


def feature_demo(com_port):
    print("-"*70)
    print("PD9530 Library feature demo")
    print("")

    print("-"*70)
    scanner = PD9530(com_port)

    print("Please move scanner within %s secs to wake it up, checking on %s" % (scanner.timeout, scanner.serial.port))
    try:
        scanner.attach()
    except serial.SerialException:
        print("Did not detect scanner. Wrong port?")
        sys.exit(1)

    device = scanner.get_device_id()
    print("Device is:")
    print(device)

    print("-"*70)
    print("Please activate an application we can send keystrokes to and scan something")

    import win32com.client as comclt
    wsh = comclt.Dispatch("WScript.Shell")
    while True:
        lines = scanner.readlines()
        if lines:
            code = lines[0]
            print("Received code: %s" % code)
            break
    wsh.SendKeys(code)

    print("-"*70)
    print("Make photo by pressing trigger")
    image, content_type = scanner.get_picture()
    if image is None:
        print("Fetching image failed, maybe resetting scanner helps")
    else:
        print("Got %s picture of %s bytes, saving..." % (content_type, len(image)))
        with open("test.%s" % content_type.lower(), "wb") as imagefile:
            for byte in image:
                imagefile.write(byte)
            print("Image is in test.%s" % content_type.lower())

    print("-"*70)
    print("Closing sanner port")
    scanner.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("com_port", help="COM port to use, set it to 115200 8N1")
    parser.add_argument("--endless", action="store_true", help="just endlessly scans codes and sends them as keystrokes")
    parser.add_argument("--echo", action="store_true", help="logs codes to terminal")
    parser.add_argument("--debug", action="store_true", help="reconfigures logging to show debug level")

    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.endless:
        endless_code_scanning(args.com_port, args.echo)
    else:
        feature_demo(args.com_port)
