'''
Python Script for Juniper EX3300 & QFX5100 Testing
Dev: Hugo Wilson 
1/23/2023
v2.05
'''

import time
import serial
import sys 
import re

'''
THIS SCRIPT WILL NOT BE ABLE TO HANDLE PASSWORD RESETS FOR NOW
Commmand line inputs are: script.py COM# Device### LPN### 
'''
def main():
    #get the  number of arguments input into the cmd line
    numArg = len(sys.argv)

    #error check the number of arguments
    if numArg != 4:
        print("Invalid arguments. Expected 3. Commmand line format is: script.py COM# QFX5100/EX3300 LPN###")
        exit(-1)

    #error check the arguments to make sure they are valid. 
    connNum = sys.argv[1]
    devID = sys.argv[2]
    lpn = sys.argv[3]

    if connNum[:3] != 'COM'and connNum[3:].isdigit() is False:
        print("Invalid Serial Console ID. Terminating program.")
        exit(-1)
    
    #check that there is a valid LPN, need to add in check that the first 3 indexes are chars 
    if len(lpn) == 6:
        if lpn[:3].isalpha() and lpn[3:].isdigit() is False:
            print("Invalid LPN. Terminating program.")
            exit(-1)
    else:
        print("Invalid LPN. Terminating program.")
        exit(-1)

    #Check that there is a valid device ID
    if devID.upper() != 'EX3300' and devID.upper() != 'QFX5100':
        print("Invalid device ID. Use QFX5100 or EX3300. Terminating program.")
        exit(-1)

    #https://semfionetworks.com/blog/establish-a-console-connection-within-a-python-script-with-pyserial/
    #Open the serial connection 
    try:
        serObj = serial.Serial(connNum)
    except:
        print("Unable to open serial connection. Serial connection does not exist or may be busy. Check COM number. Terminating program.")
        exit(-1)

    serObj.baudrate = 9600  # set Baud rate to 9600
    serObj.bytesize = 8     # Number of data bits = 8
    serObj.parity   ='N'    # No parity
    serObj.stopbits = 1     # Number of Stop bits = 1
    serObj.timeout = 1

    if serObj.is_open is False:
        print("Unable to open serial connection. Terminating program.")
        exit(-1)

    try:
        fileObj = open(lpn + '.txt', 'w')
    except:
        print("Unable to open file for writing connection. Terminating program.")
        exit(-1)

    print(f'Running testing script for Juniper {devID.upper()}')
    
    # Functions that handle I/O operations for commands 
    LoginRoot(serObj, fileObj)
    ShowConfig(serObj, fileObj)
    EditConfig(serObj, fileObj)
    ShowSysLicense(serObj, fileObj)
    ShowSysLicense(serObj, fileObj)  
    IsMaster(serObj, fileObj)
    ShowVersion(serObj, fileObj)
    ShowChasFw(serObj, fileObj)
    ShowChasHw(serObj, fileObj)
    ShowChasEnv(serObj, fileObj, devID)
    ShowSysAlarms(serObj, fileObj)
    ShowSysStorage(serObj, fileObj)
    ShowIntTerse(serObj, fileObj, devID)
    ReqSysZero(serObj, fileObj)
    LoginRoot(serObj, fileObj)
    ShowSysLicense(serObj, fileObj)
    ReqPwrOff(serObj, fileObj)

    #read until device poweroff keyword is found
    if devID.upper() == 'EX3300':
        ReadFromSerial("Please press any key to reboot.", serObj, fileObj, False)
    elif devID.upper() == 'QFX5100':
        ReadFromSerial("Power down.", serObj, fileObj, False)

    print ("Script complete. Device safe to unplug. Terminating program.")

    #Close the serial connection and file, exit program  
    serObj.close()
    fileObj.close()
    exit(0)

# Writes a command to the serObj connection
def WriteToSerial(cmd, serObj):
    serObj.write(cmd.encode("utf-8"))
    time.sleep(1)
    return None

'''
Reads output from serObj connection in a listening loop until a keyword or regex is found. 
Toggle regex detecting by setting regexFlag true, else it will do string matching 
'''
def ReadFromSerial(keyword, serObj, fileObj, regexFlag):
    counter = 0
    if regexFlag:
        regex = re.compile(keyword)
    while True:
        try:
            readdata = serObj.readline().decode('ascii')
        except UnicodeDecodeError:
            continue
        
        if len(readdata) != 0:
            #print(readdata)
            counter = 0
            fileObj.write(readdata.strip() + '\n')
            if regexFlag:
                if re.match(regex, readdata.strip()) and len(keyword) == len(readdata.strip()): #string <> string.strip()
                    break
            elif keyword.strip() in readdata.strip() and len(keyword) == len(readdata.strip()): #string <> string.strip()
                break
        else:
            counter += 1
            # send enter into the serial to wakeup device every 10 seconds of inactivity
            if counter%10 == 0:
                WriteToSerial('\r', serObj)
            elif counter > 120:
                print("Serial connection unresponive. Please manually check the device and log.")
                fileObj.close()
                exit(-1)
    return None

'''
Reads output from serObj connection in a listening loop until root> is found. Parses output 
for customer ID and licenseID, returns lists containing this info for deletion. 
'''
def ParseLicenseFromSerial(serObj, fileObj):
    print("Parsing license information...")
    keyword = 'root>'
    licenseID = []
    custID = []
    counter = 0
    while True:
        try:
            readdata = serObj.readline().decode('ascii')
        except UnicodeDecodeError:
            continue

        if len(readdata) != 0:
            # print(readdata)
            counter = 0
            fileObj.write(readdata.strip() + '\n')
            if "License identifier:" in readdata.strip():
                licenseID.append(readdata.strip().split()[-1])
            elif "Customer ID:" in readdata.strip():
                custID.append(readdata.strip().split(':')[-1])
            elif keyword.strip() in readdata.strip() and len(keyword) == len(readdata.strip()): 
                break
        else:
            counter += 1
            if counter > 30:
                print("Serial connection unresponive. 30 second timeout. Please manually check the device.")
                fileObj.close()
                exit(-1)
    return licenseID, custID

#similar to readfromserial, but will only write if it finds an OK
# def ReadFanStatusFromSerial(serObj, fileObj):
#     return None

# LOGIN COMMANDS 
# https://stackoverflow.com/questions/11427138/python-wildcard-search-in-string
def LoginRoot(serObj, fileObj):
    print("Device booting up. This may take a moment...")
    ReadFromSerial('login:', serObj, fileObj, False)
    print("Entering default credentials...")
    WriteToSerial('root\r', serObj)
    ReadFromSerial('root@:..:0%', serObj, fileObj, True)
    print('Entering CLI. This may take a moment...')
    WriteToSerial('cli\r', serObj)
    ReadFromSerial('root>', serObj, fileObj, False)
    return None

# LOGOUT COMMANDS (FOR DEBUG ONLY, NO NEED TO REBOOT DEVICE)
# def LogoutRoot(serObj, fileObj):
#     print('Logging out of cli...')
#     WriteToSerial('exit\r', serObj)
#     ReadFromSerial('root@:..:0%', serObj, fileObj, True)
#     print("Logging out of root...")
#     WriteToSerial('exit\r', serObj)
#     ReadFromSerial('login:', serObj, fileObj, False)
#     return None

# EDIT CONFIG COMMANDS 
def EditConfig(serObj, fileObj):
    print("Editing configuration...")
    WriteToSerial('config\r', serObj)
    ReadFromSerial('root#', serObj, fileObj, False) 
    WriteToSerial('delete chassis auto-image-upgrade\r', serObj)
    ReadFromSerial('root#', serObj, fileObj, False) 
    WriteToSerial('set chassis alarm management-ethernet link-down ignore\r', serObj)
    ReadFromSerial('root#', serObj, fileObj, False) 
    WriteToSerial('set system root-authentication plain-text-password\r', serObj)
    ReadFromSerial('New password:', serObj, fileObj, False) 
    WriteToSerial('Password\r', serObj)
    ReadFromSerial('Retype new password:', serObj, fileObj, False) 
    WriteToSerial('Password\r', serObj)
    ReadFromSerial('root#', serObj, fileObj, False) 
    WriteToSerial('commit\r', serObj)
    ReadFromSerial('root#', serObj, fileObj, False) 
    time.sleep(5)
    WriteToSerial('exit\r', serObj)
    ReadFromSerial('root>', serObj, fileObj, False) 

# SHOW SYSTEM LICENSE AND DELETE SYSTEM LICENSE COMMANDS 
def ShowSysLicense(serObj, fileObj):
    print("Running show system license...")
    WriteToSerial('show system license | no-more\r', serObj)
    licenseID, custID = ParseLicenseFromSerial(serObj, fileObj)
    if len(custID) > 0 and len(licenseID) > 0:
        for elems in custID:
            print(f'Deleting license:\n   Owner - {elems}\n   ID - {licenseID[custID.index(elems)]}')
            WriteToSerial('request system license delete ' + licenseID[custID.index(elems)] + '\r', serObj)
            ReadFromSerial('[yes,no] (no)', serObj, fileObj, False)
            WriteToSerial('yes\r', serObj)
            ReadFromSerial('root>', serObj, fileObj, False)
    else:
        print("No sensitive license information found.")
    return None

# SHOW VIRTUAL-CHASSIS MASTER STATUS COMMANDS 
def IsMaster(serObj, fileObj):
    print("Checking virtual-chassis master status...")
    WriteToSerial('show virtual-chassis\r', serObj)
    ReadFromSerial('root>', serObj, fileObj, False)    
    return None

# SHOW VERSION COMMANDS 
def ShowVersion(serObj, fileObj):
    print("Running show version...")
    WriteToSerial('show version\r', serObj)
    ReadFromSerial('root>', serObj, fileObj, False)
    return None

# SHOW CONFIG COMMANDS
def ShowConfig(serObj, fileObj):
    print("Running show configuration...")
    WriteToSerial('show configuration | no-more\r', serObj)
    ReadFromSerial('root>', serObj, fileObj, False)
    return None 

# SHOW CHASSIS FIRMWARE COMMANDS 
def ShowChasFw(serObj, fileObj):
    print("Running show chassis firmware...")
    WriteToSerial('show chassis firmware\r', serObj)
    ReadFromSerial('root>', serObj, fileObj, False)
    return None

# SHOW CHASSIS HARDWARE COMMANDS 
def ShowChasHw(serObj, fileObj):
    print("Running show chassis hardware...")
    WriteToSerial('show chassis hardware | no-more\r', serObj)
    ReadFromSerial('root>', serObj, fileObj, False)
    return None 

# SHOW CHASSIS ENVIRONMENTALS COMMANDS 
def ShowChasEnv(serObj, fileObj, devID):
    if devID.upper() == 'QFX5100':
        input("Press enter when the device fans spin down.")
        #Clear cli spam by sending an input over serial 
        # WriteToSerial('\r', serObj)
        # ReadFromSerial('root>', serObj, fileObj, False)
    print("Running show chassis environment...")
    WriteToSerial('show chassis environment | no-more\r', serObj)
    ReadFromSerial('root>', serObj, fileObj, False)
    return None

# SHOW SYSTEM ALARMS COMMANDS 
def ShowSysAlarms(serObj, fileObj):
    print("Running show system alarms...")
    WriteToSerial('show system alarms | no-more\r', serObj)
    ReadFromSerial('root>', serObj, fileObj, False)
    return None

# SHOW SYSTEM STORAGE COMMANDS 
def ShowSysStorage(serObj, fileObj):
    print("Running show system storage...")
    WriteToSerial('show system storage | no-more\r', serObj)
    ReadFromSerial('root>', serObj, fileObj, False)
    return None

# SHOW INTERFACES TERSE COMMANDS 
def ShowIntTerse(serObj, fileObj, devID):
    if devID.upper() == 'EX3300':
        print("Suspending 10 seconds to allow interfaces to initialize...")
        time.sleep(10)
    print("Interfaces initialized. Running show interfaces terse...")
    WriteToSerial('show interfaces terse | no-more\r', serObj)
    ReadFromSerial('root>', serObj, fileObj, False)
    return None

# REQUEST SYSTEM ZEROIZE COMMANDS 
def ReqSysZero(serObj, fileObj):
    print("Running system wipe and reboot...")
    WriteToSerial('request system zeroize\r', serObj)
    ReadFromSerial('Erase all data, including configuration and log files? [yes,no] (no)', serObj, fileObj, False)    
    WriteToSerial('yes\r', serObj)
    return None

# REQUEST POWER OFF COMMANDS 
def ReqPwrOff(serObj, fileObj):
    print("Running graceful shutdown...")
    WriteToSerial('request system power-off in 0.01\r', serObj)
    ReadFromSerial('Power Off the system in 0.01? [yes,no] (no)', serObj, fileObj, False)    
    WriteToSerial('yes\r', serObj)
    return None

if __name__ == "__main__":
    main()

'''
See if the program can detect when QFX5100 fans are done testing instead of waiting for user input
Edit config command is not 100% reliable, may have to rollback changes 
Sometimes the device will log the user out unexpectedly, may have to implement change to handle that 
'''