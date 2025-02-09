#Written by Bryan Jackson V1.2 completed 1-7-2025
#Load along with libraries onto pi pico with MicroPython interpreter

from machine import Pin, I2C
from bmp280 import *
from bmp390 import *
import time
import onewire
import ds18x20
from lcd_api import LcdApi
from i2c_lcd import I2cLcd


t_correction = 0 #thermometer calibration correction, adjust for your device.
p280_correction = 0 #Barometer calibration correction in pascals, adjust for your device. 
p390_correction = -0 #Barometer calibration correction in pascals, adjust for your device. 
elevation = 0 #your clinic elevation in meters. used for sea level corrected pressure on second page

check_T1 = 28140 #These are the hard coded internal calibration values for the BMP280. 
check_T2 = 26926 #Enter the correct values here for new hardware
check_T3 = -1000 #See serial output below if not matching. Should only set these once.
check_P1 = 36568
check_P2 = -10700
check_P3 = 3024
check_P4 = 1761
check_P5 = 106
check_P6 = -7
check_P7 = 15500
check_P8 = -14600
check_P9 = 6000

bmp280_connected = True
bmp390_connected = True

button = Pin(13, Pin.IN, Pin.PULL_DOWN)
analog_in = machine.ADC(26)
page = 0

ow = onewire.OneWire(Pin(22)) #thermometer input pin
ds = ds18x20.DS18X20(ow)
devices = ds.scan()


LCD_I2C_ADDR     = 0x27
LCD_I2C_NUM_ROWS = 2
LCD_I2C_NUM_COLS = 16

LCD_i2c = I2C(1, sda=machine.Pin(14), scl=machine.Pin(15), freq=400000)
lcd = I2cLcd(LCD_i2c, LCD_I2C_ADDR, LCD_I2C_NUM_ROWS, LCD_I2C_NUM_COLS)

BMP280_i2c = I2C(0,sda=machine.Pin(16), scl=machine.Pin(17), freq=400000)

try:
    bmp280 = BMP280(BMP280_i2c)
except:
    bmp280_connected = False
else:
    bmp280.use_case(BMP280_CASE_INDOOR)
    bmp280.print_calibration() #Print the BMP280 internal calibration values to allow for initial cal setup

# Create I2C object for BMP390
bmp390_i2c = I2C(0,sda=machine.Pin(16), scl=machine.Pin(17), freq=400000)

# Create a bmp388 object to communicate with IIC.
try: 
    bmp390 = DFRobot_BMP390_I2C(bmp390_i2c) 
except:
    bmp390_connected = False
else:    
    bmp390.set_config()
    bmp390.IIRConfig()

def getTemp():#Read in the temperature and apply the calibration offset correction.
    try:
        ds.convert_temp()
    except:
        temp = 0
    else:
        for device in devices:
            temp=ds.read_temp(device)+t_correction
    return temp

def dispTemp():#Display the temperature
    lcd.move_to(0,0)
    lcd.putstr("T=")
    lcd.move_to(2,0)
    temp_c="{:.1f}".format(getTemp())
    lcd.putstr(str(temp_c))

def checkP280Cal():
    if bmp280._T1 == check_T1 and bmp280._T2 == check_T2 and bmp280._T3 == check_T3:#Check that the loaded cal values match the internal cal values. Can load incorrectly sometimes. 
        global temp_cal_good
        temp_cal_good = True
    else:
        temp_cal_good = False

    if bmp280._P1 == check_P1 and bmp280._P2 == check_P2 and bmp280._P3 == check_P3 and bmp280._P4 == check_P4 and bmp280._P5 == check_P5 and bmp280._P6 == check_P6 and bmp280._P7 == check_P7 and bmp280._P8 == check_P8 and bmp280._P9 == check_P9:
        global press_cal_good
        press_cal_good = True
    else:
        press_cal_good = False
        
    if press_cal_good and temp_cal_good:
        return True
    else:
        return False
    
def getP280():
    if bmp280_connected and checkP280Cal():
        pressure280=bmp280.pressure + p280_correction
        return pressure280/100 #convert to hpa
    else:
        return 0

def getP390():
    if bmp390_connected:
        pressure390 = bmp390.readPressure() + p390_correction
        return pressure390/100 #convert to hpa
    else:
        return 0

def getPressure():
    if bmp280_connected and bmp390_connected:
        pressure280 = getP280()
        pressure390 = getP390()
        p_ave = (pressure280+pressure390*2)/3 #weighted average because bmp390 is a better sensor
        p_diff = abs(pressure280-pressure390)*100 #pressure sensor difference in pa
        
    elif bmp280_connected and not bmp390_connected:
        p_ave = getP280()
        p_diff = 0
    elif not bmp280_connected and bmp390_connected:
        p_ave = getP390()
        p_diff = 0
    else:
        p_ave = 0
        p_diff = 0
    return p_ave, p_diff


def dispPressure():#Display the pressure in hpa and mmHg
    
    p_ave, p_diff = getPressure()
    
    if p_diff < 200  and checkP280Cal():#check agreement between sensors, if diff is less than 200 pa then display pressure
        lcd.move_to(0,1)
        p_bar="{:.1f}".format(p_ave)
        lcd.putstr(str(p_bar))
        lcd.move_to(6,1)
        lcd.putstr("hp ")
        lcd.move_to(9,1)
        p_mmHg = "{:.1f}".format(p_ave/1.333224)
        lcd.putstr(str(p_mmHg))
        lcd.move_to(14,1)
        lcd.putstr("mm")
        
    elif p_diff >= 200 and checkP280Cal():#if pressure sensor agreement is poor direct user to pg 4 with raw readings
        lcd.move_to(0,1)
        lcd.putstr("PDiff Err SeePg4")

    elif not checkP280Cal(): #if p280 calibration check fails print error message
        lcd.move_to(0,1)
        lcd.putstr("P280Cal failure ") 
        
def dispCtp():#Calculate and display the temperature and pressure correction factor
    lcd.move_to(6,0)
    lcd.putstr(" Ctp=")
    p_ave, p_diff = getPressure()
    Ctp="{:.3f}".format((getTemp()+273.15)/295.15*1013.25/p_ave)
    lcd.move_to(11,0)
    lcd.putstr(str(Ctp))
    
def dispSLP():#Calculate and display the sea level corrected pressure
    lcd.move_to(0,0)
    lcd.putstr("SeaLvP=")
    p_ave, p_diff =getPressure()
    p_inHg = p_ave/33.8643976
    p_sea="{:.2f}".format(p_inHg*(1-0.0000225577*elevation)**-5.257)
    lcd.move_to(7,0)
    lcd.putstr(str(p_sea))
    lcd.move_to(12,0)
    lcd.putstr("inHg")
    lcd.move_to(0,1)
    lcd.putstr("If elev=")
    lcd.move_to(9,1)
    lcd.putstr(str(elevation))
    lcd.move_to(14,1)
    lcd.putstr(" m")

def getVoltage():#Read in the analog voltage input pin and convert to real voltage
    raw_reading = analog_in.read_u16()
    voltage = raw_reading/65536*3.25*2.13 #divide by 16 bit full scale value, multiply by ADC reference voltage, and voltage divider factor.
    return voltage

def dispVoltage():  #Display the voltage and state of charge  
    lcd.move_to(0,0)
    lcd.putstr("Batt=")
    lcd.move_to(5,0)
    volt = "{:.2f}".format(getVoltage())
    lcd.putstr(str(volt))
    lcd.move_to(9,0)
    lcd.putstr(" volts")
    lcd.move_to(0,1)
    lcd.putstr("Charge= ")
    lcd.move_to(7,1)
    charge = getVoltage()*176.53-632.7#Linear fit to discharge curve. (volts to percent charge)
    percent = "{:.0f}".format(charge)
    lcd.putstr(str(percent))
    lcd.move_to(10,1)
    lcd.putstr("%")
    
def dispSensors():    
    lcd.move_to(0,0)
    p280="{:.2f}".format(getP280())
    lcd.putstr(str(p280))
    lcd.move_to(8,0)
    p390="{:.2f}".format(getP390())
    lcd.putstr(str(p390))
    lcd.move_to(0,1)
    TRaw = "{:.2f}".format(getTemp())
    lcd.putstr(TRaw)
    
def page0():
    dispTemp()
    dispPressure()
    dispCtp()
    
def page1():
    dispSLP()
    
def page2():
    dispVoltage()
        
def page3():
    dispSensors()


while True:
        
    for x in range(240): #Using normal sleep for first minute so serial port connects for programming. Hit stop to keep the connection live
        if button.value() == 0 and page == 0:
            page0()
            
        elif button.value() == 0 and page == 1:
            page1()
            
        elif button.value() == 0 and page == 2:
            page2()
            
        elif button.value() == 0 and page == 3:
            page3()
            
        elif button.value() == 1:
            page += 1
            while button.value() ==1:
                lcd.move_to(0,0)
                lcd.putstr("                                ")
     
        if page >= 4:
            page = 0
        t=getTemp()    
        print("%s, %s, %s" %(getP280(), getP390(), t))   
        time.sleep_ms(250)
        
    for x in range(2400): #Using lightsleep for ten minutes out of every 11 to save power. This dissables the serial port among other things
        if button.value() == 0 and page == 0:
            page0()
            
        elif button.value() == 0 and page == 1:
            page1()
            
        elif button.value() == 0 and page == 2:
            page2()
            
        elif button.value() == 0 and page == 3:
            page3()
            
        elif button.value() == 1:
            page += 1
            while button.value() ==1:
                lcd.move_to(0,0)
                lcd.putstr("                                ")
     
        if page >= 4:
            page = 0   
           
        machine.lightsleep(250)            
