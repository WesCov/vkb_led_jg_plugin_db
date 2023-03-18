"""

Wesley Covalt

Joystick Gremlin plugin to control the three LEDs of a VKB Gladiator flightstick.

Please see the README file for directions, credits, and limitations.

version with db (event database)

"""

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


# uncomment to post to log
#log_filename = 'vkb_led_jg_plugin.log'
#current_dir = os.path.abspath(os.path.dirname(__file__))
#logging.basicConfig(filename=os.path.join(current_dir, log_filename), level=logging.DEBUG)



#
#    Joystick Gremlin UI
#    

buttonTrigger = PhysicalInputVariable(
	"Button to activate LED:",
	"Button that triggers the LED.",
	[gremlin.common.InputType.JoystickButton])

mode = ModeVariable("Mode:", "The mode in which to use this mapping")

changesMode = IntegerVariable(
	"Mode changes: 0 none, 1 toggles, 2 cycles:",
	"This button 0 does not change modes, 1 toggles a mode on/off, 2 cycles amoung 2+ modes",
	0)

modeTo = ModeVariable("Mode this button switchs to:", "What mode does this button switch to, if any")

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


# TO DO:
#   inputs
#   store mode (or modeTo), changes mode ("no", "toggle", "cycle")
#


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
    controlState.whilePressed = whilePressed.value
    # store the mode the button represents, not the one it is active in
    controlState.changesMode = changesmode.value
    if changesmode.value:
        contolState.mode = modeTo.value
    else:
        contolState.mode = mode.value
    controlState.LEDConfig = LEDClass(LED_id = LED_id)
    
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
        controlState.defaultLEDConfig = LEDClass(LED_id = controlState.LED_id,
                                                 colorMode = 0,
                                                 LEDMode = 1,
                                                 color1 = stringRGBToList(rgbStrColor3.value),
                                                 color2 = (0,0,0))
    else:
        controlState.defaultLEDConfig = LEDClass(LED_id = controlState.LED_id,
                                                 colorMode = 0,
                                                 LEDMode = 0,
                                                 color1 = (0,0,0),
                                                 color2 = (0,0,0))
   
    ### open a db file.  This will be called for each instance but there is only one file

    ### 

    gremlin.util.log(f"DB Location: {DB_LOCATION}")
             
    decorator_button = buttonTrigger.create_decorator(mode.value)

    @decorator_button.button(buttonTrigger.input_id)
    def button_action(event, vjoy):
        global controlState

        button_id =     "-".join([str(event.device_guid)[1:-1], str(event.identifier)])
    

        ############ GET THE ON STATE FROM THE STACK
        rowidForCurrentBtn = 99999
        maxRowId # for given led
        buttonStateOn = rowForCurrentBtn > 0
            
        
        #### org by (might combine later)
        
        #### BtnState    Pressed    WhilePressed   ChangesMode   ModeTo
        

        if not buttonStateOn and event.is_pressed and contorlState.changesMode == "no":     # normal button turn on

                """ PUSH EVENT with event.device_guid, event.identifier,
                    mode, changesMode, LEDConfig, & defaultLEDConfig
                """
                set_LEDs(controlState.vkbDevice, [controlState.LEDConfig])

        elif not buttonStateOn and event.is_pressed and contorlState.changesMode != "no":      # mode button turn on
        
            if controlState.changesMode == "toggle":

                x = 1
                ### if top, POP, set 2nd or default
                ### else delete(btn, LED) regardless of mode
                
            elif controlState.changesMode == "cycle":
                
                x=2
                ### push, set LEDConfig
                ### del (btn, LED) regarless of mode
    
        elif buttonStateOn and event.is_pressed and not controlState.whilePressed:              # normal button turn off
            
            x = 3
            ### if top, POP, set 2nd or default
            ### else delete(btn, LED, mode)
              
              
        elif buttonStateOn and not event.is_pressed and controlState.whilePressed:              # while pressed

            x = 4
            ### if top, POP, set 2nd or default ---- should be top
            ### else delete(btn, LED, mode) --- should not need to do







### find guid, btn, LED, mode combo in stack
### If top of stack for that LED & mode:
    ### pop off item (pull and delete from stack)
    ### if there is a new LED & mode in top spot use set it's LEDConfig
    ### else use the popped item's defaultLEDconfig
    ### set_led()
### else delete that item from stack (do not change LED)


