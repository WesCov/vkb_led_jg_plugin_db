"""

Wesley Covalt

Joystick Gremlin plugin to control the three LEDs of a VKB Gladiator flightstick.

Please see the README file for directions, credits, and limitations.

version with db (event database)

"""

#import sys

import os
import gremlin
from gremlin.user_plugin import *

from vkb_led_jg_plugin_db_lib import *


# hard code the vendor and product ids
# VKBsim Gladiator EVO R
VENDOR_ID = 0x231d 
PRODUCT_ID = 0x0200

# event database name and location
DB_FILENAME = 'vkb_led_jg_plugin.db'
DB_DIR = os.path.abspath(os.path.dirname(__file__))
DB_LOCATION = DB_DIR + "\\" + DB_FILENAME


# a db will be created where the plugin resides (not where the library is)
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
DB_NAME = CURRENT_DIR + "\\" + "VKB_LED_event_stack.db"

# uncomment to post to log
#log_filename = 'vkb_led_jg_plugin.log'
#logging.basicConfig(filename=os.path.join(current_dir, log_filename), level=logging.DEBUG)



#
#    Joystick Gremlin UI
#    

buttonTrigger = PhysicalInputVariable(
	"Button to activate LED:",
	"Button that triggers the LED.",
	[gremlin.common.InputType.JoystickButton])

mode = ModeVariable("The Mode in which the button is activated:", "The Mode in which to use this mapping.")

changesMode = BoolVariable(
	"This button changes the Mode",
	"This button has been assigned the Switch Mode action.",
	False)

modeTo = ModeVariable("If checked, this button switches to ", "What Mode does this button switch to, if any")

LEDName = StringVariable("Which LED - Base, Hat, or RGB:", "LED to be activated", "RGB")

whilePressed = BoolVariable(
	"Only while button is pressed:",
	"Keep LED activated only while the button is pressed; otherwise toggle on/off with press. Does not apply to buttons than change modes.",
	False)

header1 = StringVariable("---------- Base LED Settings ----------","","-------------------------------------")

baseColorMode = IntegerVariable(
    "Base Color mode:",
    "1 = Blue | 2 = Red | 3 = Blue/Red | 4 = Red/Blue | 5 = Blue & Red",
    1, 1, 5)

baseBlinkMode = IntegerVariable(
    "Base Blink mode:",
    "1 = Constant | 2 = Slow | 3 = Fast | 4 = Ultra fast",
    1, 1, 4)

baseBlueBrightness = IntegerVariable("Base Blue brightness level (1-7):", "", 7, 1, 7)
baseRedBrightness = IntegerVariable("Base Red brightness level (1-7):", "", 7, 1, 7)


header2 = StringVariable("---------- Hat LED Settings -----------", "", "-------------------------------------")

hatBlinkMode = IntegerVariable(
    "Hat Blink mode:",
    "1 = Constant | 2 = Slow | 3 = Fast | 4 = Ultra fast",
    1, 1, 4)

hatRedBrightness = IntegerVariable("Hat Red brightness level (1-7):", "", 7, 1, 7)


header3 = StringVariable("---------- RGB LED Settings -----------", "", "-------------------------------------")

rgbColorMode = IntegerVariable(
    "RGB Color mode:",
    "1 = Color 1 | 2 = Color 2 | 3 = Color 1->2 | 4 = Color 2->1",
    1, 1, 4)

rgbBlinkMode = IntegerVariable(
    "RGB Blink mode:",
    "1 = Constant | 2 = Slow | 3 = Fast | 4 = Ultra fast",
    1, 1, 4)

rgbStrColor1 = StringVariable(
			"RGB Color 1 Red,Green,Blue (range 0-7):",
			"Comma-separated RGB values in VKB 0-7 range",
            "0,0,0")

rgbStrColor2 = StringVariable(
			"RGB Color 2 Red,Green,Blue (range 0-7):",
			"Comma-separated RGB values in VKB 0-7 range",
            "0,0,0")

rgbStrColor3 = StringVariable(
			"RGB Default Color Red,Green,Blue (range 0-7):",
			"Comma-separated RGB values in VKB 0-7 range of the color to go back to",
            "0,3,5")



controlState = controlStateClass()


# get the vkb device, if connected
controlState.vkbDevice = getUSBDevice(VENDOR_ID, PRODUCT_ID)

if controlState.vkbDevice is None:
    
    #gremlin.util.log(f"VKB Device not active. Vendor ID: {hex(VENDOR_ID)} Product ID {hex(PRODUCT_ID)}")
    pass

else:
    
    #gremlin.util.log(f"VKB Device found. Vendor ID: {VENDOR_ID} Product ID {PRODUCT_ID}")

    # packup the UI inputs into the controlState variable

    LED_id = LEDNameToId(LEDName.value)
    controlState.LEDConfig = LEDClass(LED_id = LED_id)
    if changesMode.value:
        controlState.whilePressed = False
    else:
        controlState.whilePressed = whilePressed.value
    # store the mode the button is activated in
    controlState.mode = mode.value
    controlState.dbName = DB_NAME
         
    # color1 & color2 have different uses depending on the LED id
    if LED_id == 0:        # Base
        
        controlState.LEDConfig.LEDMode = baseBlinkMode.value 
        if baseBlinkMode.value == 1 and (baseColorMode.value == 3 or baseColorMode.value == 4):
            controlState.LEDConfig.colorMode = 4
        else:
            controlState.LEDConfig.colorMode = baseColorMode.value - 1
            
        if controlState.LEDConfig.colorMode == 0:
            controlState.LEDConfig.color1 = [baseBlueBrightness.value, 0, 0]
            controlState.LEDConfig.color2 = [0, 0, 0]
        elif controlState.LEDConfig.colorMode == 1:
            controlState.LEDConfig.color1 = [baseRedBrightness.value, 0, 0]
            controlState.LEDConfig.color2 = [0, 0, 0]
        elif controlState.LEDConfig.colorMode > 1:
            controlState.LEDConfig.color1 = [baseBlueBrightness.value, 0, 0]
            controlState.LEDConfig.color2 = [baseRedBrightness.value, 0, 0]
    
    elif LED_id == 11:     # Hat    
        controlState.LEDConfig.LEDMode = hatBlinkMode.value
        controlState.LEDConfig.colorMode = 0 
        controlState.LEDConfig.color1 = [hatRedBrightness.value, 0, 0]
        controlState.LEDConfig.color2 = [0, 0, 0]
    
    elif LED_id == 10:     # RGB
        
        controlState.LEDConfig.LEDMode = rgbBlinkMode.value
        controlState.LEDConfig.colorMode = rgbColorMode.value - 1
        controlState.LEDConfig.color1 = stringRGBToList(rgbStrColor1.value)
        controlState.LEDConfig.color2 = stringRGBToList(rgbStrColor2.value)    
    
    # set up the led configuration to go back to
    if LED_id == 10:
        controlState.defaultLEDConfig = LEDClass(LED_id = controlState.LEDConfig.LED_id,
                                                 colorMode = 0,
                                                 LEDMode = 1,
                                                 color1 = stringRGBToList(rgbStrColor3.value),
                                                 color2 = (0,0,0))
    else:
        controlState.defaultLEDConfig = LEDClass(LED_id = controlState.LEDConfig.LED_id,
                                                 colorMode = 0,
                                                 LEDMode = 0,
                                                 color1 = (0,0,0),
                                                 color2 = (0,0,0))
   
    ### open a db file.  This will be called for each instance but there is only one file
    ### create an empty LEDStack table
    createLEDStack(controlState.dbName)

    
    decorator_button = buttonTrigger.create_decorator(mode.value)
    
    @decorator_button.button(buttonTrigger.input_id)
    def button_action(event, vjoy):
        global controlState

        button_id = "-".join([str(event.device_guid)[1:-1], str(event.identifier)])
    
        ### if the button is on the stack then it is in the on state
        rowidCurrentBtn = getRowidButtonLEDModeEvent(controlState.dbName, button_id, controlState.LEDConfig.LED_id, controlState.mode)
        buttonStateOn = rowidCurrentBtn > 0
           
        if not buttonStateOn and event.is_pressed:

            # push, set LEDConfig
            pushButtonLEDEvent(controlState.dbName, button_id, controlState.LEDConfig, controlState.mode)
            set_LEDs(controlState.vkbDevice, [controlState.LEDConfig])
    
        elif ((buttonStateOn and     event.is_pressed and not controlState.whilePressed) or      # normal button turn off
              (buttonStateOn and not event.is_pressed and     controlState.whilePressed)):       # while pressed turn off

            # x = is #1?            
            rowidLastLED = getLastRowidLEDEvent(controlState.dbName, controlState.LEDConfig.LED_id)
            # delete btn, led, mode
            deleteRowid(controlState.dbName, rowidCurrentBtn)
            if rowidCurrentBtn == rowidLastLED:
                # get LEDConfig of next LED in stack -- if any
                resultLED = pullLastLEDConfig(controlState.dbName, controlState.LEDConfig.LED_id)
                if resultLED == None:
                    set_LEDs(controlState.vkbDevice, [controlState.defaultLEDConfig])
                else:
                    set_LEDs(controlState.vkbDevice, [resultLED])
            
    
    # this function is called only in the MoveTo mode and removes the prior mode if on.
    if changesMode.value:
        
        decorator_button = buttonTrigger.create_decorator(modeTo.value)
        
        @decorator_button.button(buttonTrigger.input_id)
        def button_action(event, vjoy):
            global controlState
    
            button_id = "-".join([str(event.device_guid)[1:-1], str(event.identifier)])
        
            ### if the button is on the stack then it is in the on state
            rowidCurrentBtn = getRowidButtonLEDModeEvent(controlState.dbName, button_id, controlState.LEDConfig.LED_id)
            buttonStateOn = rowidCurrentBtn > 0

            if buttonStateOn and event.is_pressed:
                
                # x = is #1?            
                rowidLastLED = getLastRowidLEDEvent(controlState.dbName, controlState.LEDConfig.LED_id)
                # delete btn, led, NO mode
                deleteRowid(controlState.dbName, rowidCurrentBtn)
                if rowidCurrentBtn == rowidLastLED:
                    # get LEDConfig of next LED in stack -- if any
                    resultLED = pullLastLEDConfig(controlState.dbName, controlState.LEDConfig.LED_id)
                    if resultLED == None:
                        set_LEDs(controlState.vkbDevice, [controlState.defaultLEDConfig])
                    else:
                        set_LEDs(controlState.vkbDevice, [resultLED])








