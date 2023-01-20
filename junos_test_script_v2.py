'''
Python Script for Juniper EX3300 & QFX5100 Testing
Dev: Hugo Wilson 
1/17/2023
v2.0
'''

import time
import serial
import sys 
# import os.path 

'''
THIS SCRIPT WILL NOT BE ABLE TO HANDLE PASSWORD RESETS FOR NOW
Commmand line inputs are: script.py COM# LPN### Device###
'''
def main():
    #get the  number of arguments input into the cmd line
    numArg = len(sys.argv)

    #error check the number of arguments
    if numArg != 4:
        print("Invalid arguments. Expected 2. Commmand line format is: script.py COM# LPN### DEVICE####")
        exit(-1)

    #error check the arguments to make sure they are valid. 
    connNum = sys.argv[1]
    lpn = sys.argv[2]
    devID = sys.argv[3]

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
        print("Unable to open serial connection. Serial connection does not exist, check COM number. Terminating program.")
        exit(-1)

    serObj.baudrate = 9600  # set Baud rate to 9600
    serObj.bytesize = 8     # Number of data bits = 8
    serObj.parity   ='N'    # No parity
    serObj.stopbits = 1     # Number of Stop bits = 1
    serObj.timeout = 1

    if serObj.is_open is False:
        print("Unable to open serial connection. Terminating program.")
        exit(-1)

    #open the file to write to
    # cwd = os.getcwd()
    # print("Current working directory: {0}".format(cwd))

    try:
        fileObj = open(lpn + '.txt', 'w')
    except:
        print("Unable to open file for writing connection. Terminating program.")
        exit(-1)

    print(f'Running testing script for Juniper {devID.upper()}')

    #Login then logout
    LoginRoot(serObj, fileObj)
    #verify and delete license if customer information exists
    ShowSysLicense(serObj, fileObj)
    ShowSysLicense(serObj, fileObj)  
    #Check that the device is in master mode 
    IsMaster(serObj, fileObj)
    #run information gathering commands 
    ShowVersion(serObj, fileObj)
    ShowConfig(serObj, fileObj)
    ShowChasFw(serObj, fileObj)
    ShowChasHw(serObj, fileObj)

    #May have to wait until device quiets down, finishes testing
    ShowChasEnv(serObj, fileObj, devID)

    ShowSysAlarms(serObj, fileObj)
    ShowSysStorage(serObj, fileObj)
    #connect hardware and verify functionality 
    ShowIntTerse(serObj, fileObj, devID)
    #reset, reboot, power off
    ReqSysZero(serObj, fileObj)
    LoginRoot(serObj, fileObj)
    ShowSysLicense(serObj, fileObj)
    ReqPwrOff(serObj, fileObj)

    #read until device poweroff keyword is found
    if devID.upper() == 'EX3300':
        ReadFromSerial("Please press any key to reboot.", serObj, fileObj)
    elif devID.upper() == 'QFX5100':
        ReadFromSerial("Power down.", serObj, fileObj)

    print ("Script complete. Device safe to unplug. Terminating program.")

    #Close the serial connection and file, exit program  
    serObj.close()
    fileObj.close()
    exit(0)

def WriteToSerial(cmd, serObj, fileObj):
    serObj.write(cmd.encode("utf-8"))
    time.sleep(1)
    return None

def ReadFromSerial(keyword, serObj, fileObj):
    counter = 0
    while True:
        try:
            readdata = serObj.readline().decode('ascii')
        except UnicodeDecodeError:
            continue

        if len(readdata) != 0:
            counter = 0
            # print(readdata)
            fileObj.write(readdata.strip() + '\n')
            if keyword.strip() in readdata.strip() and len(keyword) == len(readdata.strip()): #string <> string.strip()
                print("FOUND KEYWORD")
                break
        else:
            counter += 1
            # send enter into the serial to wakeup device every 10 seconds of inactivity
            if counter%10 == 0:
                WriteToSerial('\r', serObj, fileObj)
            elif counter > 120:
                print("Serial connection unresponive. 120 second timeout. Please manually check the device.")
                fileObj.close()
                exit(-1)
    return None

def ParseLicenseFromSerial(serObj, fileObj):
    print("parsing license...")
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
            counter = 0
            # print(readdata)
            fileObj.write(readdata.strip() + '\n')

            if "License identifier:" in readdata.strip():
                licenseID.append(readdata.strip().split()[-1])
            elif "Customer ID:" in readdata.strip():
                custID.append(readdata.strip().split()[-1])
            elif keyword.strip() in readdata.strip() and len(keyword) == len(readdata.strip()): #string <> string.strip()
                break
        else:
            counter += 1

            if counter > 120:
                print("Serial connection unresponive. 120 second timeout. Please manually check the device.")
                fileObj.close()
                exit(-1)
    return licenseID, custID

#similar to readfromserial, but will only write if it finds an OK
def ReadFanStatusFromSerial(serObj, fileObj):
    return None

def LoginRoot(serObj, fileObj):
    #Read boot sequence from serial
    print("Device booting up. This may take a moment...")
    ReadFromSerial('login:', serObj, fileObj)
    #Read login from serial
    print("Entering default credentials...")
    WriteToSerial('root\r', serObj, fileObj)
    ReadFromSerial('root@:RE:0%', serObj, fileObj)
    #Read CLI from serial
    print('Entering CLI. This may take a moment...')
    WriteToSerial('cli\r', serObj, fileObj)
    ReadFromSerial('root>', serObj, fileObj)
    return None

def LogoutRoot(serObj, fileObj):
    print('Logging out of cli...')
    WriteToSerial('exit\r', serObj, fileObj)
    ReadFromSerial('root@:RE:0%', serObj, fileObj)
    print("Logging out of root...")
    WriteToSerial('exit\r', serObj, fileObj)
    ReadFromSerial('login:', serObj, fileObj)
    return None

def ShowSysLicense(serObj, fileObj):
    print("Running show system license")
    WriteToSerial('show system license\r', serObj, fileObj)
    licenseID, custID = ParseLicenseFromSerial(serObj, fileObj)
    if len(custID) > 0 and len(licenseID) > 0:
        for elems in custID:
            print(f'Deleting license. Owner: {elems} ID: {licenseID[custID.index(elems)]}')
            WriteToSerial('request system license delete ' + licenseID[custID.index(elems)] + '\r', serObj, fileObj)
            ReadFromSerial('[yes,no] (no)', serObj, fileObj)
            WriteToSerial('yes\r', serObj, fileObj)
            ReadFromSerial('root>', serObj, fileObj)
    return None

def IsMaster(serObj, fileObj):
    print("Checking virtual-chassis master status...")
    WriteToSerial('show virtual-chassis\r', serObj,fileObj)
    ReadFromSerial('root>', serObj, fileObj)    
    return None

def ShowVersion(serObj, fileObj):
    print("Running show version...")
    WriteToSerial('show version\r', serObj, fileObj)
    ReadFromSerial('root>', serObj, fileObj)
    return None

def ShowConfig(serObj, fileObj):
    print("Running show configuration...")
    WriteToSerial('show configuration | no-more\r', serObj, fileObj)
    ReadFromSerial('root>', serObj, fileObj)
    return None 

def ShowChasFw(serObj, fileObj):
    print("Running show chassis firmware...")
    WriteToSerial('show chassis firmware\r', serObj, fileObj)
    ReadFromSerial('root>', serObj, fileObj)
    return None

def ShowChasHw(serObj, fileObj):
    print("Running show chassis hardware...")
    WriteToSerial('show chassis hardware | no-more\r', serObj, fileObj)
    ReadFromSerial('root>', serObj, fileObj)
    return None 

def ShowChasEnv(serObj, fileObj, devID):
    if devID.upper() == 'QFX5100':
        input("Press enter when the device fans shut the fuck up.")

    print("Running show chassis environment...")
    #Send an enter key into the device to clear the console spam 
    WriteToSerial('\r', serObj, fileObj)
    ReadFromSerial('root>', serObj, fileObj)
    WriteToSerial('show chassis environment | no-more\r', serObj, fileObj)
    #Loop to keep reading until the fans display status OK, FAILED, OR ABSENT.0
    ReadFromSerial('root>', serObj, fileObj)
    # while True:
    #     if ReadFanStatusFromSerial(serObj, fileObj) is True:
    #         break
    #     time.sleep(10)
    #     WriteToSerial('show chassis environment | no-more\r', serObj, fileObj)

    return None

def ShowSysAlarms(serObj, fileObj):
    print("Running show system alarms...")
    WriteToSerial('show system alarms | no-more\r', serObj, fileObj)
    ReadFromSerial('root>', serObj, fileObj)
    return None

def ShowSysStorage(serObj, fileObj):
    print("Running show system storage...")
    WriteToSerial('show system storage | no-more\r', serObj, fileObj)
    ReadFromSerial('root>', serObj, fileObj)
    return None

def ShowIntTerse(serObj, fileObj, devID):
    if devID.upper() == 'EX3300':
        print("Suspending 10 seconds to allow interfaces to initialize...")
        time.sleep(10)
    print("Initialized. Running show interfaces terse...")
    WriteToSerial('show interfaces terse | no-more\r', serObj, fileObj)
    ReadFromSerial('root>', serObj, fileObj)
    return None

def ReqSysZero(serObj, fileObj):
    print("Running system reboot...")
    WriteToSerial('request system zeroize\r', serObj, fileObj)
    ReadFromSerial('Erase all data, including configuration and log files? [yes,no] (no)', serObj, fileObj)    
    WriteToSerial('yes\r', serObj, fileObj)
    return None

def ReqPwrOff(serObj, fileObj):
    print("Running graceful shutdown...")
    WriteToSerial('request system power-off\r', serObj, fileObj)
    ReadFromSerial('Power Off the system ? [yes,no] (no)', serObj, fileObj)    
    WriteToSerial('yes\r', serObj, fileObj)
    return None

if __name__ == "__main__":
    main()

'''
Double check EX3300 code compatibility
See if the program can detect when QFX5100 fans are done testing instead of waiting for user input
'''