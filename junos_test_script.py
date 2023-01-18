'''
Python Script for Juniper EX3300 & QFX5100 Testing
Dev: Hugo Wilson 
1/17/2023
Ver 1.02
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

    #Run the command helper functions
    LoginRoot(serObj, fileObj)

    #remove the cli spam if QFX5100 
    # if devID.upper() == 'QFX5100':
    #     ConfigSpam(serObj, fileObj)
    
    #Check the license information, if it returns true, then a license was deleted and the device must be reset 
    ShowSysLicense(serObj, fileObj)  
    #Check that the device is in master mode 
    IsMaster(serObj, fileObj)

    ShowVersion(serObj, fileObj)
    ShowConfig(serObj, fileObj)
    ShowChasFw(serObj, fileObj)
    ShowChasHw(serObj, fileObj)
    ShowChasEnv(serObj, fileObj)
    ShowSysAlarms(serObj, fileObj)
    ShowSysStorage(serObj, fileObj)
    
    ShowIntTerse(serObj, fileObj)
    ReqSysZero(serObj, fileObj)
    LoginRoot(serObj, fileObj)
    ShowSysLicense(serObj, fileObj)
    ReqPwrOff(serObj, fileObj)
    #Logout(serObj, fileObj)
    
    #Listen to the remaining output for termination, no additional command used
    #Cannot use, device takes about two minutes to shutdown, should keep reading 
    #MAKE SURE TO PUT THE COMMAND BELOW BACK IN AFTER DEV
    if devID.upper() == 'EX3300':
        ReadSerialThenWrite("Please press any key to reboot.", 'NO_CMD', serObj, fileObj)
    elif devID.upper() == 'QFX5100':
        ReadSerialThenWrite("Power down.", 'NO_CMD', serObj, fileObj)

    print ("Script complete. Device safe to unplug. Terminating program.")

    #Close the serial connection and file, exit program  
    serObj.close()
    fileObj.close()
    exit(0)

'''
This function will listen for output from the serial connection until
a keyword, string is found. Once the string is found, the function will send
the designated command and exit. Formatted as listen first, then send command
''' 
def ReadSerialThenWrite(string, cmd, serialConn, file):
    #create a timeout counter if the connection hangs for more than 2 minutes 
    counter = 0
    # If there is nothing read from the serial, send a wakeup cmd to ensure prompt is not idle
    # wakeup = '\r'
    # serialConn.write(wakeup.encode("utf-8"))
    # time.sleep(1)

    while True:
        readdata = serialConn.readline().decode('ascii')
        #if there is data in the connection to be read, write to file 
        if len(readdata) != 0:
            #reset the timeout counter 
            counter = 0
            file.write(readdata.strip() + '\n')
            #The string indicating the return to the cli input has been found, break 
            # print(string, readdata)
            # print(len(string), len(readdata.strip()))
            # print(string in readdata.strip(), len(string) == len(readdata.strip()))
            if string.strip() in readdata.strip() and len(string) == len(readdata.strip()): #string <> string.strip()
                #print('Found keyword!')
                #If a command is specified, write the command to the serial connection, else ignore
                if cmd != "NO_CMD":
                    serialConn.write(cmd.encode("utf-8"))
                    time.sleep(1)
                break
        #there is nothing recieved from the serial, add to timeout counter
        else:
            counter+=1
            #if 2 minutes of no response has elapsed, shutdown program
            if counter > 120:
                print("Serial connection unresponive. 120 second timeout. Please manually check the device.")
                file.close()
                exit(-1)
            # print(counter)
    return None

#Logs into the device and enters the CLI 
def LoginRoot(serialConn, file): 
    print("Device booting up. This may take a moment...")
    #keep reading from the terminal until there is "login:" #ISSUE WITH QFX WHERE LOGIN: is found before login
    ReadSerialThenWrite('login:', 'root\r', serialConn, file)
    print("Entering default credentials...")
    print("Entering CLI. This may take a moment...")
    ReadSerialThenWrite('root@:RE:0%', 'cli\r', serialConn, file)
    return None

#Logs the user out of the device, function used for dev debugging only
def Logout(serialConn, file):
    print("Logging out...")
    ReadSerialThenWrite('root>', 'exit \r', serialConn, file)
    ReadSerialThenWrite('root@:RE:0%', 'exit \r', serialConn, file)
    return None

#Runs the show version command 
def ShowVersion(serialConn, file):
    print("Running show version...")
    ReadSerialThenWrite('root>', 'show version\r', serialConn, file)
    return None

#Runs the show config command 
def ShowConfig(serialConn, file):
    print("Running show configuration...")
    ReadSerialThenWrite('root>', 'show configuration | no-more\r', serialConn,file)
    return None 

#Runs the show chassis firmware command 
def ShowChasFw(serialConn, file):
    print("Running show chassis firmware...")
    ReadSerialThenWrite('root>', 'show chassis firmware\r', serialConn,file)
    return None

#Runs the show chassis hardware command 
def ShowChasHw(serialConn, file):
    print("Running show chassis hardware...")
    ReadSerialThenWrite('root>', 'show chassis hardware | no-more\r', serialConn,file)
    return None 

#Runs the show chassis environment command 
def ShowChasEnv(serialConn, file):
    print("Running show chassis environment...")
    ReadSerialThenWrite('root>', 'show chassis environment | no-more\r', serialConn,file)
    return None

#Runs the show system alarms command 
def ShowSysAlarms(serialConn, file):
    print("Running show system alarms...")
    ReadSerialThenWrite('root>', 'show system alarms | no-more\r', serialConn,file)
    return None

#Runs the show system storage command 
def ShowSysStorage(serialConn, file):
    print("Running show system storage...")
    ReadSerialThenWrite('root>', 'show system storage | no-more\r', serialConn,file)
    return None

#Runs the show system license command 
#must also add functionality to delete license if neccessary 
#CURRENTLY WORKING HERE TO DELETE THE SYSTEM LICENSE 
def ShowSysLicense(serialConn, file):
    print("Running show system license...")
    ReadSerialThenWrite('root>', 'show system license\r', serialConn,file)
    # Check for customer ID, if exists delete the license, else does nothing 
    # DeleteSysLicense(serialConn, file)
    return None

# def DeleteSysLicense(serialConn, file):
#     #create a timeout counter if the connection hangs for more than 2 minutes 
#     print("Checking if there is a license to delete...") 
#     counter = 0
#     #List to store the license ID that will be parsed from the readdata
#     licenseID = []
#     while True:    
#         readdata = serialConn.readline().decode('ascii')
#         #if there is data in the connection to be read, write to file 
#         if len(readdata) != 0:
#             #reset the timeout counter 
#             counter = 0
#             string = readdata.strip() + '\n'
#             file.write(string)
#             print(string)      
#             print("STRING SPLIT")
#             if "Customer ID:" in string:
#                 list.append(string.split(' '))  
#             #The string indicating the return to the cli input has been found, break 
#             if "root> " in readdata:
#                 break
#         #there is nothing recieved from the serial, add to timeout counter
#         else:
#             #if 2 minutes of no response has elapsed, shutdown program
#             if counter > 120:
#                 print("Serial connection unresponive. 120 second timeout. Please manually check the device.")
#                 file.close()
#                 exit(-1)
#             counter+=1
#     print(licenseID)
#     return None

#Runs the show interfaces terse command, ensure that hardware is plugged in prior to running
#Command may be run faster than the device has time to recogize plugged in devices
def ShowIntTerse(serialConn, file):
    print("Suspending 10 seconds to allow interfaces to initialize...")
    #may replace with a 10 second timer so no user input is needed 
    #input("Verify ports are plugged in and LEDs are on. Press Enter to continue.")
    time.sleep(10)
    print("Initialized. Running show interfaces terse...")
    ReadSerialThenWrite('root>', 'show interfaces terse | no-more\r', serialConn,file)
    return None

#Runs the request system zeroize command 
def ReqSysZero(serialConn, file):
    print("Running system reboot...")
    ReadSerialThenWrite('root>', 'request system zeroize\r', serialConn,file)
    ReadSerialThenWrite('Erase all data, including configuration and log files? [yes,no] (no)', 'yes\r', serialConn, file)
    return None

#Runs the request system power-off command
def ReqPwrOff(serialConn, file):
    print("Running graceful shutdown...")
    ReadSerialThenWrite('root>', 'request system power-off\r', serialConn,file)
    ReadSerialThenWrite('Power Off the system ? [yes,no] (no)', 'yes\r', serialConn, file)
    return None

# def ConfigSpam(serialConn, file):
#     print("Changing configuration settings...")
#     ReadSerialThenWrite('root>', 'config\r', serialConn,file)
#     ReadSerialThenWrite('root#', 'delete chassis auto-image-upgrade\r', serialConn,file)
#     ReadSerialThenWrite('root#', 'set chassis alarm management-ethernet link-down ignore\r', serialConn,file)
#     ReadSerialThenWrite('root#', 'set system root-authentication plain-text-password\r', serialConn, file)
#     ReadSerialThenWrite('New password:', 'Password\r', serialConn,file)
#     ReadSerialThenWrite('Retype new password:', 'Password\r', serialConn,file)
#     #ReadSerialThenWrite('root#', 'commit\r', serialConn,file)
#     ReadSerialThenWrite('root#', 'exit\r', serialConn,file)
#     return None

def IsMaster(serialConn, file):
    print("Checking virtual-chassis master status...")
    ReadSerialThenWrite('root>', 'show virtual-chassis\r', serialConn,file)
    return None

if __name__ == "__main__":
    main()


'''
NOTES
This program is designed to automate command inputs for the diagnostic procedure required to qualify JUNIPER EX3300 
and QFX5100 for resale. The base functionality of this program assumes that the device is perfect with no errors. 
This requires the user to manually verify the log for device errors, and if they exist, console in and manually test
the device. The hope is to improve functionality by allowing the code to automatically fix some of these issues if they
arise. Note that this code will never fix all issues, as it is impossible to know what issues may arise. It is only designed
to fix the common ones seen in these devices. Some common errors with these devices that may be automated in the future 
are shown below. The development of this script is very similar to the development of code for socket programming. 

Test Cases:
    Customer License information needs to be deleted
    JUNOS booted off the backup image
    configure to remove cli spam 

Known Issues:
    will only read root@:RE:0%, cannot detect root@:LC:0% for entering cli 
'''