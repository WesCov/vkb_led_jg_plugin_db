"""

Wesley Covalt

Joystick Gremlin plugin to control the three LEDs of a VKB Gladiator flightstick.

Please see the README file for directions, credits, and limitations.

"""

import os
import gremlin
from gremlin.user_plugin import *

from vkb_led_jg_plugin_lib import *


# hard code the vendor and product ids
# VKBsim Gladiator EVO R
vendor_id=0x231d 
product_id=0x0200


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

LEDName = StringVariable("Which LED - Base, Hat, or RGB:", "LED to be activated", "RGB")

whilePressed = BoolVariable(
	"Only while button is pressed:",
	"Keep LED activated only while the button is pressed; otherwise toggle on/off with press.",
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
controlState.vkbDevice = getUSBDevice(vendor_id, product_id)

if controlState.vkbDevice is None:
    
    #gremlin.util.log(f"VKB Device not active. Vendor ID: {hex(vendor_id)} Product ID {hex(product_id)}")
    pass

else:
    
    #gremlin.util.log(f"VKB Device found. Vendor ID: {vendor_id} Product ID {product_id}")

    # packup the UI inputs into the controlState variable

    controlState.LED_id = LEDNameToId(LEDName.value)
    controlState.buttonStateOn = False
    controlState.whilePressed = whilePressed.value    
    controlState.LEDConfig = LEDClass(LED_id = controlState.LED_id)
    
    # color1 & color2 have different uses depending on the LED id
    if controlState.LED_id == 0:        # Base
        
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
    
    elif controlState.LED_id == 11:     # Hat    
        controlState.LEDConfig.LEDMode = hatBlinkMode.value
        controlState.LEDConfig.colorMode = 0 
        controlState.LEDConfig.color1 = [hatRedBrightness.value, 0, 0]
        controlState.LEDConfig.color2 = [0, 0, 0]
    
    elif controlState.LED_id == 10:     # RGB
        
        controlState.LEDConfig.LEDMode = rgbBlinkMode.value
        controlState.LEDConfig.colorMode = rgbColorMode.value - 1
        controlState.LEDConfig.color1 = stringRGBToList(rgbStrColor1.value)
        controlState.LEDConfig.color2 = stringRGBToList(rgbStrColor2.value)    
    
    # set up the led configuration to go back to
    if controlState.LED_id == 10:
        controlState.defaultLED = LEDClass(LED_id = controlState.LED_id,
                                           colorMode = 0,
                                           LEDMode = 1,
                                           color1 = stringRGBToList(rgbStrColor3.value),
                                           color2 = (0,0,0))
    else:
        controlState.defaultLED = LEDClass(LED_id = controlState.LED_id,
                                           colorMode = 0,
                                           LEDMode = 0,
                                           color1 = (0,0,0),
                                           color2 = (0,0,0))
   

             
    decorator_button = buttonTrigger.create_decorator(mode.value)

    @decorator_button.button(buttonTrigger.input_id)
    def button_action(event, vjoy):
        global controlState

        # the USB Lighting Usage report acts as interface between code and LED
        deviceLEDUsage = get_LED_configs(controlState.vkbDevice)        
        
        LEDIndex = getLEDIndex(controlState.LED_id, deviceLEDUsage)
        if LEDIndex is not None:
            currentConfig = deviceLEDUsage[LEDIndex]
        else:
            currentConfig = None
            
        if event.is_pressed and not controlState.buttonStateOn:

            controlState.buttonStateOn = True
            
            if controlState.whilePressed:
                controlState.priorLED = currentConfig
            else:
                controlState.priorLED = None
                
            if LEDIndex is None:
                 deviceLEDUsage.append(controlState.LEDConfig)
            else:
                deviceLEDUsage[LEDIndex] = controlState.LEDConfig

        elif controlState.buttonStateOn:

            if event.is_pressed and not controlState.whilePressed:

                controlState.buttonStateOn = False
                if LEDIndex is not None:

                    if deviceLEDUsage[LEDIndex] == controlState.LEDConfig:
                        deviceLEDUsage[LEDIndex] = controlState.defaultLED

            elif not event.is_pressed and controlState.whilePressed:
                
                controlState.buttonStateOn = False
                if LEDIndex is not None:
                    if controlState.priorLED is None:
                        deviceLEDUsage[LEDIndex] = controlState.defaultLED
                    else:
                        deviceLEDUsage[LEDIndex] = controlState.priorLED

        set_LEDs(controlState.vkbDevice, deviceLEDUsage)
