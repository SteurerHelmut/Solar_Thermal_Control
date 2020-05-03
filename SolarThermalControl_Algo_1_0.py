##############################################################################
#!/usr/bin/python3
# This program  contains the control logic of a solar thermal system with
#   2 redundant digital temperature sensors Dallas DS18B20 mounted to the
#     upper pipes in the solar fluid circle on the roof
#     TempUp1 - fixed to the upper part of the solar panel collector pipe
#     TempUp2 - fixed to the upper part of the solar panel collector pipe
#   1 digital temperature sensor Dallas DS18B20 mounted in the roof chamber
#     with the sun strip absorbers
#     TempUpAir - mounted inside the roof chamber with the solar panels
#   2 digital temperature sensors Dallas DS18B20 mounted at the hot water tank,
#     one at the lower end and one at the upper end of the hot water tank
#     in the cellar
#     TempHotWaterTank_down - mounted at the low side of the hot water tank
#     TempHotWaterTank_up - mounted at the upper side of the hot water tank
#   3 water pumps for the following fluid circle
#     PumpS - circle solar panels to the external heat exchanger - solar fluid
#     PumpW - circle hot water tank to the external heat exchanger - water
#     PumpF - circle hot water tank to the oil burner boiler - water
#
# Very important HW experience:
#   If only 3 dallas sensors were used, there was no detection problem.
#   Using a fourth sensor the 1-wire system collapsed. The solution was
#   to reduce the 4.7 kOhm resistor to the half, which was practically done
#   by using two 4.7 kOhm resistors in parallel. Now the system is working
#   quite robust. In a next step two additional sensor will be used.
#   If the problem appears again, then a next 4.7 kOhm resistor will be
#   used. This is a proposal found in the internet. There it is recommended
#   to lower the resistor down to 1.2 kOhm to be able to use up to 10 
#   1-wire sensors.
#
# General conditions of the program
# CycleTime = 10 seconds
#
# The control logic is following:
#     If both the temperature of the upper sensors are 8 degrees higher than
#     the temperature on the lower side of the hot water tank, then the pumps
#     to the external heat changer will start.
#     If both, the temeratures of the upper sensors are less than 5 degrees
#     higher than the temperature of the lower side of the hot water tank,
#     then the pumps to the external heat changer will stopp.
#     If the lower temperature sensor value is above 60 degrees the hot water
#     tank is fully loaded.
#     Now the load keep management and heat transfer has to work.
#     If the upper sensors show still higher temperatures, the pump from the
#     oil burner chamber starts regularily in 2 minute cycles to transport
#     energy from the hot water tank to the burner tank. During this time
#     also the other two pumps are working. After 30 seconds the all the
#     pumps are stopped. Starting the next 2 minute cycle all pumps start to
#     run again as long as the upper temperatures are 5 degrees higher than
#     the cellar sensors.
#
##############################################################################
import os, time

#--- Description -------------------------------------------------------------
# Every sensor in the system has its unique name. The name contains the
# location of the sensor.
# There are sensors on the roof in the thermal chamber, where the panels are
# mounted. Two sensors are fixed to the solar fuel pipe. The other one
# one measures the air in the thermal chamber on the roof.
# In the cellar there are two sensors fixed to the hot water tank.
# One is mounted near the buttom of hot water tank, the other one is fixed
# near the top of the tank.

#--- Sensor Definition -------------------------------------------------------
TEMP_PANEL_PIPE_01 = '/sys/bus/w1/devices/28-00000b55130f/w1_slave'
TEMP_PANEL_PIPE_02 = '/sys/bus/w1/devices/28-00000b56108d/w1_slave'
TEMP_PANEL_AIR = '/sys/bus/w1/devices/28-00000b55c049/w1_slave'
TEMP_WTANK_BOTTOM = '/sys/bus/w1/devices/28-00000b543dc1/w1_slave'
TEMP_WTANK_TOP = '/sys/bus/w1/devices/28-00000b55beea/w1_slave'

TEMP_SENSORS = ('/sys/bus/w1/devices/28-00000b55130f/w1_slave', \
                '/sys/bus/w1/devices/28-00000b56108d/w1_slave', \
                '/sys/bus/w1/devices/28-00000b55c049/w1_slave', \
                '/sys/bus/w1/devices/28-00000b543dc1/w1_slave', \
                '/sys/bus/w1/devices/28-00000b55beea/w1_slave')

#--- Activator Definition ----------------------------------------------------
PUMP_SOLAR = 1      # pump for the solar liquid circle
PUMP_EXCHANGER = 2  # pump for water from boiler to external heat exchanger 
PUMP_BOILER = 3     # pump for water from burner to boiler círcle
    
#--- Constants for Data Recording --------------------------------------------
DATA_FILE_PATH = "/home/pi/RPi_Projects/SolarThermalControl/Data/"
#DATA_FILE_PATH = "D:\Elektronik\Raspberry\Projects\SolarThermalControl"
#DATA_FILE_PATH += "\TemperaturMeasurement\Data\\"
DATA_FILE_BASE = "_SolarThermal_Data_"   # file name basis for recorded data

#--- Constants ---------------------------------------------------------------
SYS_CYCLE_TIME = 10             # main loop cycle time 

#--- Variable Definition and Initialisation ----------------------------------
val_Temp_Panel_Pipe_01 = 0.0    # temperature of the 1st copper pipe sensor
val_Temp_Panel_Pipe_02 = 0.0    # temperature of the 2nd copper pipe sensor
val_Temp_Panel_Air = 0.0        # air temperature value in the panel chamber
val_Temp_WTank_bottom = 0.0     # temperature at the bottom of the boiler
val_Temp_WTank_top = 0.0        # temperatrue at tht top of the boiler

str_Temp_Panel_Pipe_01 = ""
str_Temp_Panel_Pipe_02 = ""
str_Temp_Panel_Air = ""
str_Temp_WTank_down = ""
str_Temp_WTank_up = ""

data_File_Counter = 0           # file name counter for rec data  
data_File_Name = ""             # dynamic file name for rec data
sys_Cycle_Counter = 0;          # cycle counter, counts each measurement cycle

#-----------------------------------------------------------------------------

def initialize_recFile (file_Name):
    data_File = open(file_Name, "w")
    data_File.write("Datarecording with Raspberry in Solar Thermal System\n")
    data_File.write("by Helmut Steurer\n")
    data_File.write(file_Name + "\n")
    data_File.write("---------------------------------------------------\n")
    str_Headline = "PiDate; PiTime; Cycle; PiDateTime; TPPipe1;"
    str_Headline += "TPPipe2; TPAir; TTank_d; TTank_u"
    data_File.write(str_Headline +"\n")
    data_File.close()


def readTempSensor(sensor_Name):
    #--- get sensor info via 1-wire bus --------------------------------------
    sensor_Data = open(sensor_Name, 'r')
    sensor_Values = str(sensor_Data.readlines())
    sensor_Data.close()
    temp_Values = sensor_Values.strip().split(",")[1]
    t_start = temp_Values.rfind("t") + 2
    t_end = temp_Values.find("\n")
    str_temp = temp_Values[t_start:t_end]
    str_temp = temp_Values[t_start:-4]
    temperature = float(str_temp)/1000.0
    str_temp = str(temperature)
    str_temp = str_temp.replace(".",",")
    return str_temp

#--- Initialisation ----------------------------------------------------------
# hier GPIO als Input deklarieren

#--- Cyclic Routine ----------------------------------------------------------
while True:
    #--- read temperatures from the sensors ----------------------------------
    str_Temp_Panel_Pipe_01 = readTempSensor(TEMP_PANEL_PIPE_01)
    str_Temp_Panel_Pipe_02 = readTempSensor(TEMP_PANEL_PIPE_02)
    str_Temp_Panel_Air = readTempSensor(TEMP_PANEL_AIR)
    str_Temp_WTank_down = readTempSensor(TEMP_WTANK_BOTTOM)
    str_Temp_WTank_up = readTempSensor(TEMP_WTANK_TOP)

    #val_Temp_Panel_Pipe_01 = readTempSensor(Temp_Panel_Pipe_01)
    #val_Temp_Panel_Pipe_02 = readTempSensor(Temp_Panel_Pipe_02)
    #val_Temp_Panel_Air = readTempSensor(Temp_Panel_Air)
    #val_Temp_WTank_down = readTempSensor(Temp_WTank_down)
    #val_Temp_WTank_up = readTempSensor(TEMP_WTANK_TOP)
    
    sys_cycle_counter += 1
    if ((sys_cycle_counter%2000) == 1):
        data_filecounter += 1
        data_filename = data_filename_path
        data_filename += time.strftime('%d%m%Y_%H%M%S_')
        data_filename += str(data_filecounter) + ".csv"
        #data_filename += "Data_with_Timestamp_" + str(data_filecounter) + ".csv"
        initialize_recFile(data_filename)
    print("Filename: " + data_filename)

    data_file = open(data_filename, "a")
    TempLine = ""
    TempLine = time.strftime('%d.%m.%Y;')
    TempLine += time.strftime('%H:%M:%S;')
    TempLine += str(sys_cycle_counter) + ";"
    TempLine += time.strftime('%d.%m.%Y %H:%M:%S;')
    TempLine += str_Temp_Panel_Pipe_01 + ";"
    TempLine += str_Temp_Panel_Pipe_02 + ";"
    TempLine += str_Temp_Panel_Air + ";"
    TempLine += str_Temp_WTank_down + ";"
    TempLine += str_Temp_WTank_up + ";\n"
    #TempLine += str(val_Temp_Panel_Pipe_01) + ";"
    #TempLine += str(val_Temp_Panel_Pipe_02) + ";"
    #TempLine += str(val_Temp_Panel_Air) + ";"
    #TempLine += str(val_Temp_WTank_down) + ";"
    #TempLine += str(val_Temp_WTank_up) + ";\n"
    data_file.write(TempLine)
    data_file.close()    

#==============================================================================
#        1         2         3         4         5         6         7
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#==============================================================================

    print("==================================================================")
    print(time.strftime('%d.%m.%Y - %H:%M:%S'))
    #print("Temp_WTank_down: " + str(val_Temp_WTank_down))
    #print("Temp_Panel_Pipe_01: " + str(val_Temp_Panel_Pipe_01))
    #print("Temp_Panel_Pipe_02: " + str(val_Temp_Panel_Pipe_02))
    #print("Temp_Panel_Air: " + str(val_Temp_Panel_Air))
    print("Temp_WTank_down: " + str_Temp_WTank_down)
    print("Temp_Panel_Pipe_01: " + str_Temp_Panel_Pipe_01)
    print("Temp_Panel_Pipe_02: " + str_Temp_Panel_Pipe_02)
    print("Temp_Panel_Air: " + str_Temp_Panel_Air)
    print("==================================================================")

# --- Cycle Time is 10 seconds


    time.sleep(1)
    remainTime = 10 - int(time.strftime("%S")) % 10
    print(remainTime)
    time.sleep(remainTime)
                                                            
    #if sys_cycle_counter == 6:
    #    break
    
