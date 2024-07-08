from machine import Pin, I2C
from bmp280 import *
import time
import onewire
import ds18x20
from lcd_api import LcdApi
from i2c_lcd import I2cLcd


t_correction = 0 #thermometer calibration correction, adjust for your device. 
p_correction = 0 #Barometer calibration correction in pascals, adjust for your device. 
elevation = 0 #your clinic elevation in meters. used for sea level corrected pressure on second page

button = Pin(13, Pin.IN, Pin.PULL_DOWN)
analog_in = machine.ADC(26)
screen = 0
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
bmp = BMP280(BMP280_i2c)

check_T1 = 27810 #These are the hard coded calibration values for the BMP280. See serial output below if not matching. Should only set these once.
check_T2 = 26205
check_T3 = -1000
check_P1 = 37758
check_P2 = -10928
check_P3 = 3024
check_P4 = 5037
check_P5 = 172
check_P6 = -7
check_P7 = 15500
check_P8 = -14600
check_P9 = 6000

bmp.use_case(BMP280_CASE_INDOOR)
bmp.print_calibration() #Print the BMP280 internal calibration values to allow for initial setup and error checking


if bmp._T1 == check_T1 and bmp._T2 == check_T2 and bmp._T3 == check_T3:#Check that the loaded cal values match the internal cal values. Can load incorrectly sometimes. 
    print("Temp cal values OK")
    global temp_cal_good
    temp_cal_good = True
else:
    temp_cal_good = False
    print("Temp cal values don't match!")

if bmp._P1 == check_P1 and bmp._P2 == check_P2 and bmp._P3 == check_P3 and bmp._P4 == check_P4 and bmp._P5 == check_P5 and bmp._P6 == check_P6 and bmp._P7 == check_P7 and bmp._P8 == check_P8 and bmp._P9 == check_P9:
    print("Pressure cal values OK") #Check that the loaded cal values match the internal cal values. Can load incorrectly sometimes.
    global press_cal_good
    press_cal_good = True

else:
    press_cal_good = False
    print("Pressure cal values don't match!")    



def getTemp():#Read in the temperature and apply the calibration offset correction.
    global temp
    ds.convert_temp()
    for device in devices:
        temp=ds.read_temp(device)+t_correction
    global temp_c
    temp_c="{:.1f}".format(temp)
    global temp_k
    temp_k="{:.1f}".format(temp+273.15)

def dispTemp():#Display the temperature
    lcd.move_to(0,0)
    lcd.putstr("T=")
    lcd.move_to(2,0)
    lcd.putstr(str(temp_c))
   
def getPressure():#Read raw pressure from BMP280, apply calibration offset correction, and do unit conversions.
    global pressure
    pressure=bmp.pressure + p_correction     
    global p_bar
    p_bar="{:.1f}".format(pressure/100)
    global p_mmHg
    p_mmHg="{:.1f}".format(pressure/133.3224)
    global p_inHg
    p_inHg=pressure/3386.43976
    
def dispPressure():#Display the pressure in hpa and mmHg
    lcd.move_to(0,1)
    lcd.putstr(str(p_bar))
    lcd.move_to(6,1)
    lcd.putstr("hp ")
    lcd.move_to(9,1)
    lcd.putstr(str(p_mmHg))
    lcd.move_to(14,1)
    lcd.putstr("mm")
    
def dispCtp():#Calculate and display the temperature and pressure correction factor
    lcd.move_to(6,0)
    lcd.putstr(" Ctp=")
    Ctp="{:.3f}".format((temp+273.15)/295.15*101325/pressure)
    lcd.move_to(11,0)
    lcd.putstr(str(Ctp))
    
def dispSLP():#Calculate and display the sea level corrected pressure
    lcd.move_to(0,0)
    lcd.putstr("SeaLvP=")
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
    global voltage
    global charge
    percent = raw_reading/65536*3.25*2.13*176.53-632.7#Linear fit to discharge curve
    voltage = "{:.2f}".format(raw_reading/65536*3.25*2.13)#divide by 16 bit full scale value, multiply by ADC reference voltage, and voltage divider factor.
    charge = "{:.0f}".format(percent)
    
def dispVoltage():  #Display the voltage and state of charge  
    lcd.move_to(0,0)
    lcd.putstr("Batt=")
    lcd.move_to(5,0)
    lcd.putstr(str(voltage))
    lcd.move_to(9,0)
    lcd.putstr(" volts")
    lcd.move_to(0,1)
    lcd.putstr("Charge= ")
    lcd.move_to(7,1)
    lcd.putstr(str(charge))
    lcd.move_to(10,1)
    lcd.putstr("%")
    
def page0():
    getTemp()
    dispTemp()
    getPressure()
    dispPressure()
    dispCtp()
    
def page1():
    getPressure()
    dispSLP()
    
def page2():
    getVoltage()
    dispVoltage()
        
        
while True:
    if press_cal_good == False or temp_cal_good == False:#May need to adjust calibration checking constants above if new BMP280 was installed. 
        lcd.move_to(0,0)
        lcd.putstr("Cal values bad  Please Reboot ")
        time.sleep(1000)
        
    for x in range(240): #Using normal sleep for first minute so serial port connects for programming. Hit stop to keep the connection live
        if button.value() == 0 and page == 0:
            page0()
            
        elif button.value() == 0 and page == 1:
            page1()
            
        elif button.value() == 0 and page == 2:
            page2()
            
        elif button.value() == 1:
            page += 1
            while button.value() ==1:
                lcd.move_to(0,0)
                lcd.putstr("                                ")
     
        if page >= 3:
            page = 0
           
        time.sleep_ms(250)
        
    for x in range(2400): #Using lightsleep for ten minutes out of every 11 to save power. This dissables the serial port among other things
        if button.value() == 0 and page == 0:
            page0()
            
        elif button.value() == 0 and page == 1:
            page1()
            
        elif button.value() == 0 and page == 2:
            page2()
            
        elif button.value() == 1:
            page += 1
            while button.value() ==1:
                lcd.move_to(0,0)
                lcd.putstr("                                ")
                
        if page >= 3:
            page = 0
           
        machine.lightsleep(250)            
