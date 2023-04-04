'''

vkb_led_jg_plugin_lib_db.py

Wesley Covalt

Functions for a Joystick Gremlin plugin to control the three LEDs of a VKB Gladiator flightstick.

Please see the vkb_led_jg_plugin_db.pdf for directions and credits.


LEDClass, set_LEDs, and _LED_conf_checksum are from the pyvkb package by ventorvar.
These have been modified to limit RGB values to 0 to 7 and open and close the VKB device. 

The following is from ventorvar:
    
Setting the LEDs consists of a possible 30 LED configs each of which is a 4 byte structure as follows:

byte 0:  LED ID
bytes 2-4: a 24 bit color config as follows::

    000 001 010 011 100 101 110 111
    clm lem  b2  g2  r2  b1  g1  r1

color mode (clm):
    0 - color1
    1 - color2
    2 - color1/2
    3 - color2/1
    4 - color1+2

led mode (lem):
    0 - off
    1 - constant
    2 - slow blink
    3 - fast blink
    4 - ultra fast

Colors:
    VKB uses a simple RGB color configuration for all LEDs. Non-rgb LEDs will not light if you set their primary
    color to 0 in the color config. The LEDs have a very reduced color range due to VKB using 0-7 to determine the
    brightness of R, G, and B.

'''

import os
import pywinusb.hid as hid

import struct
import bitstruct as bs

import sqlite3


LED_REPORT_ID = 0x59
LED_REPORT_LEN = 129
LED_SET_OP_CODE = bytes.fromhex("59a50a")
LED_CONFIG_COUNT = 4    # plus a dummy


class LEDClass:
    def __init__(self,
                 LED_id = 0,
                 colorMode = 0,
                 LEDMode = 0,
                 color1 = [0, 0, 0],
                 color2 = [0, 0, 0]):

        self.LED_id = int(LED_id)
        self.colorMode = colorMode
        self.LEDMode = LEDMode
        self.color1 = color1
        self.color2 = color2

    def __repr__(self):
        return (f"<LED_id:{self.LED_id} colorMode:{self.colorMode} LEDMode:{self.LEDMode} "
                f"color1:{self.color1} color2:{self.color2}>")

    def __bytes__(self):
        return struct.pack(">B", self.LED_id) + bs.byteswap("3",
                                                            bs.pack("u3" * 8,
                                                                    self.colorMode,
                                                                    self.LEDMode,
                                                                    *self.color2[::-1],
                                                                    *self.color1[::-1],),)

def set_LEDs(dev, LED_configs):
    LED_configs.append(LEDClass(LED_id=99))
    num_configs = len(LED_configs)
    if num_configs > LED_CONFIG_COUNT:
        raise ValueError(f"Can only set a maximum of {LED_CONFIG_COUNT} LED configs")
    LED_configs = b"".join(bytes(_) for _ in LED_configs)
    LED_configs = os.urandom(2) + struct.pack(">B", num_configs) + LED_configs
    chksum = _LED_conf_checksum(num_configs, LED_configs)
    cmd = LED_SET_OP_CODE + chksum + LED_configs
    cmd = cmd + b"\x00" * (LED_REPORT_LEN - len(cmd))
    dev.open()
    LED_report = [_ for _ in dev.find_feature_reports() if _.report_id == LED_REPORT_ID][0]
    LED_report.send(cmd)
    dev.close()


def _LED_conf_checksum(num_configs, buf):
    
    def conf_checksum_bit(chk, b):
        chk ^= b
        for i in range(8):
            _ = chk & 1
            chk >>= 1
            if _ != 0:
                chk ^= 0xA001
        return chk

    chk = 0xFFFF
    for i in range((num_configs + 1) * 3):
        chk = conf_checksum_bit(chk, buf[i])
    return struct.pack("<H", chk)


class controlStateClass:
    
    def __init__(self,
                 vkbDevice = None,
                 mode = "Default",
                 whilePressed = False,
                 LEDConfig = None,
                 defaultLEDConfig = None,
                 dbName = None):
        
        self.vkbDevice = vkbDevice
        self.mode = mode
        self.whilePressed = whilePressed
        self.LEDConfig = LEDConfig
        self.defaultLEDConfig = defaultLEDConfig
        self.dbName = dbName


def LEDNameToId(s):
    if s.upper() == "BASE":
        return 0
    elif s.upper() == "HAT":
        return 11
    elif s.upper() == "RGB":
        return 10
    else:
        return None

# used for interface
def stringRGBToList(s):
    result = (0,0,0)
    if len(s) == 5 and s.count(',') == 2:
        if (0 <= int(s[0]) <= 7) and (0 <= int(s[2]) <= 7) and (0 <= int(s[4]) <= 7):
            result = (int(s[0]), int(s[2]), int(s[4]))
    return result

def getUSBDevice(vendor_id, product_id):
    theDevice = hid.HidDeviceFilter(vendor_id=vendor_id, product_id=product_id).get_devices()
    if len(theDevice)==0:
        return None
    else:
        return theDevice[0] 


### Database functions

def createLEDStack(dbName):
    the_db = sqlite3.connect(dbName)
    the_db.execute("DROP TABLE IF EXISTS LEDStack;")
    the_db.execute('''CREATE TABLE IF NOT EXISTS LEDStack(button_id TEXT,
                                                          LED_id INT,
                                                          mode TEXT,
                                                          colorMode INT,
                                                          LEDMode INT,
                                                          color1 TEXT,
                                                          color2 TEXT);''')
    the_db.commit()
    the_db.close()

def pushButtonLEDEvent(dbName, button_id, LEDConfig, mode):
    the_db = sqlite3.connect(dbName)
    the_db.execute("INSERT INTO LEDStack VALUES(?, ?, ?, ?, ?, ?, ?);", 
                   [button_id,
                    LEDConfig.LED_id,
                    mode,
                    LEDConfig.colorMode,
                    LEDConfig.LEDMode,
                    ",".join(map(str, LEDConfig.color1)),
                    ",".join(map(str, LEDConfig.color2))])
    the_db.commit()
    the_db.close()


# pull the LEDConfig for the last LED id
def pullLastLEDConfig(dbName, LED_id):
    the_db = sqlite3.connect(dbName)
    cursor = the_db.cursor()
    cursor.execute(f"SELECT * FROM LEDStack WHERE rowid = (SELECT MAX(rowid) FROM LEDStack WHERE LED_id = {LED_id});")    
    result = cursor.fetchone()
    the_db.close()
    if result == None:
        return None
    else:
        LEDConfig = LEDClass(result[1], result[3], result[4], list(map(int, result[5].split(","))), list(map(int, result[6].split(","))))
        return LEDConfig

# return the row id of a given btn, LED, & optional mode
def getRowidButtonLEDModeEvent(dbName, button_id, LED_id, mode=None):
    the_db = sqlite3.connect(dbName)
    cursor = the_db.cursor()
    if mode == None:
        cursor.execute(f"SELECT rowid FROM LEDStack WHERE button_id='{button_id}' AND LED_id={LED_id};")        
    else:
        cursor.execute(f"SELECT rowid FROM LEDStack WHERE button_id='{button_id}' AND LED_id={LED_id} AND mode='{mode}';")
    result = cursor.fetchone()
    the_db.close()
    if result == None:
        return 0
    else:
        return result[0]

# return the last row if for given LED
def getLastRowidLEDEvent(dbName, LED_id):
    the_db = sqlite3.connect(dbName)
    cursor = the_db.cursor()
    cursor.execute(f"SELECT rowid FROM LEDStack WHERE rowid = (SELECT MAX(rowid) FROM LEDStack WHERE LED_id = {LED_id});")        
    result = cursor.fetchone()
    the_db.close()
    if result == None:
        return 0
    else:
        return result[0]

# delete a given row
def deleteRowid(dbName, rowid):
    the_db = sqlite3.connect(dbName)
    cursor = the_db.cursor()
    cursor.execute(f"DELETE FROM LEDStack WHERE rowid = {rowid};")
    the_db.commit()
    the_db.close()

