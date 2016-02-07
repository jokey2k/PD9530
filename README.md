Library to use Datalogic(r) PowerScan(r) PD-9530 with USB-COM or RS232 on Windows(r) and UNIXes

The package depends on pySerial for communication and pywin32 for sending keystrokes.

To see if the scanner is detected properly::

	scanner = PD9530("COM6")
	scanner.attach()
	print(scanner.get_device_id())
    scanner.close()

To just read a code, call::

	scanner = PD9530("COM6")
    scanner.attach()

    for code in scanner.readlines():
    	print(code)

    scanner.close()

To take a picture of the scanner view::

	scanner = PD9530("COM6")
	scanner.attach()
    image, content_type = scanner.get_picture()
    if image is None:
        print("Fetching image failed, maybe resetting scanner helps")
    else:
        print("Got %s picture of %s bytes, saving..." % (content_type, len(image)))
        with open("test.%s" % content_type.lower(), "wb") as imagefile:
            for byte in image:
                imagefile.write(byte)
            print("Image is in test.%s" % content_type.lower())

The pd9530.py can also be called to get both functions shown above from command line.

PowerScan and DataLogic are registered trademarks of Datalogic ADC. in many countries, including the U.S.A. and the E.U.
Windows is a registered trademark by Microsoft Corporation
