The main file is my own work. The libraries are sourced from other sites. Each library has its own header from the author.
This is a python file designed to work on the raspberry pi pico with the micropython interpreter installed.
Once built the micropython needs to be loaded on the pi pico, then the firmware and libraries. First run will error out with calibration value mismatch.
Calibration values need to be entered into the firmware. The cal values will print in the serial box at the bottom of thonny if you run the main file. Then copy those to the constants in firmware. 