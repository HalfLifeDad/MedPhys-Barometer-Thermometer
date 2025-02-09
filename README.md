This code is designed to run on a pi pico based barometer/thermometer for medical physics T/P correction measurements.
The main file is my own work. The libraries are sourced from other sites.

BMP280.py from https://github.com/dafvid/micropython-bmp280/blob/master/bmp280.py

BMP390.py is adapted from https://github.com/DFRobot/DFRobot_BMP388

i2c_lcd.py from https://github.com/T-622/RPI-PICO-I2C-LCD/blob/main/pico_i2c_lcd.py

lcd_api.py https://github.com/T-622/RPI-PICO-I2C-LCD/blob/main/lcd_api.py

hardware files for circuit board and case can be found on thingiverse and printables

https://www.thingiverse.com/thing:6878454

https://www.printables.com/model/1113274-medical-physics-barometer-thermometer

The original  Onshape model for the barometer case is

https://cad.onshape.com/documents/0dcfc6b15f06f59bd1975578/w/a5ea05baecde1565a5c37df0/e/b4fa3ca8cff4c876b6499b67?renderMode=0&uiState=67a90291dea7165ea8ca3466

This is a python file designed to work on the raspberry pi pico with the micropython interpreter installed.
Once built the micropython needs to be loaded on the pi pico, then the firmware and libraries. First run will error out with calibration value mismatch.
Calibration values need to be entered into the firmware. The cal values will print in the serial box at the bottom of thonny if you run the main file. 
Then enter those constants into the firmware. 
