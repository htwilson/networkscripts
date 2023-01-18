'''
Python Script for Juniper EX3300 Testing
Dev: Hugo Wilson 
1/13/2023
Ver 1.0
'''

import time
import serial
import sys 
import os.path 

'''
THIS SCRIPT WILL NOT BE ABLE TO HANDLE PASSWORD RESETS FOR NOW
Commmand line inputs are: script.py COM# LPN###
'''
def main():
    #get the  number of arguments input into the cmd line
    numArg = len(sys.argv)

    #error check the number of arguments
    if numArg != 3:
        print("Invalid arguments. Expected 2. Commmand line format is: script.py COM# LPN###")
        exit(-1)

    #error check the arguments to make sure they are valid. 
    connNum = sys.argv[1]
    lpn = sys.argv[2]

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

    #Run the command helper functions
    LoginRoot(serObj, fileObj)
    ShowVersion(serObj, fileObj)
    ShowConfig(serObj, fileObj)
    ShowChasFw(serObj, fileObj)
    ShowChasHw(serObj, fileObj)
    ShowChasEnv(serObj, fileObj)
    ShowSysAlarms(serObj, fileObj)
    ShowSysStorage(serObj, fileObj)
    ShowSysLicense(serObj, fileObj)
    ShowIntTerse(serObj, fileObj)
    ReqSysZero(serObj, fileObj)
    LoginRoot(serObj, fileObj)
    ReqPwrOff(serObj, fileObj)
    #Logout(serObj, fileObj)
    
    #Listen to the remaining output for termination, no additional command used
    #Cannot use, device takes about two minutes to shutdown, should keep reading until
    ReadUntilStringIsFound("Please press any key to reboot.", 'NO_CMD', serObj, fileObj)
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
def ReadUntilStringIsFound(string, cmd, serialConn, file):
    #create a timeout counter if the connection hangs for more than 2 minutes 
    counter = 0
    while True:
        readdata = serialConn.readline().decode('ascii')
        #if there is data in the connection to be read, write to file 
        if len(readdata) != 0:
            #reset the timeout counter 
            counter = 0
            file.write(readdata.strip() + '\n')
            #The string indicating the return to the cli input has been found, break 
            if string in readdata:
                # print(readdata.strip() + '\n')
                # print(string)
                #If a command is specified, write the command to the serial connection, else ignore
                if cmd != "NO_CMD":
                    serialConn.write(cmd.encode("utf-8"))
                    time.sleep(1)
                break
        #there is nothing recieved from the serial, add to timeout counter
        else:
            #if 2 minutes of no response has elapsed, shutdown program
            if counter > 120:
                print("Serial connection unresponive. Please manually check the device.")
                file.close()
                exit(-1)
            counter+=1 
            time.sleep(1)
    return None

#Logs into the device and enters the CLI 
def LoginRoot(serialConn, file):    
    print("Device booting up. This may take a moment...")
    #keep reading from the terminal until there is "login:"
    ReadUntilStringIsFound('login: ', 'root\r', serialConn, file)
    print("Entering default credentials...")
    print("Entering CLI. This may take a moment...")
    ReadUntilStringIsFound('root@:RE:0% ', 'cli\r', serialConn, file)
    return None

#Logs the user out of the device, function used for dev debugging only
# def Logout(serialConn, file):
#     ReadUntilStringIsFound('root> ', 'exit \r', serialConn, file)
#     ReadUntilStringIsFound('root@:RE:0% ', 'exit \r', serialConn, file)
#     return None

#Runs the show version command 
def ShowVersion(serialConn, file):
    print("Running show version...")
    ReadUntilStringIsFound('root>', 'show version\r', serialConn, file)
    return None

#Runs the show config command 
def ShowConfig(serialConn, file):
    print("Running show configuration...")
    ReadUntilStringIsFound('root>', 'show configuration | no-more\r', serialConn,file)
    return None 

#Runs the show chassis firmware command 
def ShowChasFw(serialConn, file):
    print("Running show chassis firmware...")
    ReadUntilStringIsFound('root>', 'show chassis firmware\r', serialConn,file)
    return None

#Runs the show chassis hardware command 
def ShowChasHw(serialConn, file):
    print("Running show chassis hardware...")
    ReadUntilStringIsFound('root>', 'show chassis hardware\r', serialConn,file)
    return None 

#Runs the show chassis environment command 
def ShowChasEnv(serialConn, file):
    print("Running show chassis environment...")
    ReadUntilStringIsFound('root>', 'show chassis environment\r', serialConn,file)
    return None

#Runs the show system alarms command 
def ShowSysAlarms(serialConn, file):
    print("Running show system alarms...")
    ReadUntilStringIsFound('root>', 'show system alarms\r', serialConn,file)
    return None

#Runs the show system storage command 
def ShowSysStorage(serialConn, file):
    print("Running show system storage...")
    ReadUntilStringIsFound('root>', 'show system storage | no-more\r', serialConn,file)
    return None

#Runs the show system license command 
#must also add functionality to delete license if neccessary 
def ShowSysLicense(serialConn, file):
    print("Running show system license...")
    ReadUntilStringIsFound('root>', 'show system license\r', serialConn,file)
    return None

#Runs the show interfaces terse command, ensure that hardware is plugged in prior to running
#Command may be run faster than the device has time to recogize plugged in devices
def ShowIntTerse(serialConn, file):
    print("Running show interfaces terse...")
    ReadUntilStringIsFound('root>', 'show interfaces terse | no-more\r', serialConn,file)
    return None

#Runs the request system zeroize command 
def ReqSysZero(serialConn, file):
    print("Running system reboot...")
    ReadUntilStringIsFound('root>', 'request system zeroize\r', serialConn,file)
    ReadUntilStringIsFound('[yes,no] (no)', 'yes\r', serialConn, file)
    return None

#Runs the request system power-off command
def ReqPwrOff(serialConn, file):
    print("Running graceful shutdown...")
    ReadUntilStringIsFound('root>', 'request system power-off\r', serialConn,file)
    ReadUntilStringIsFound('[yes,no] (no)', 'yes\r', serialConn, file)
    return None

if __name__ == "__main__":
    main()


#ADD AN ERROR CHECK TO TERMINATE THE PROGRAM IF NOTHING IS DETECTED FOR MORE THAN X MINS