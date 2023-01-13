import time
import serial
import sys 
import os.path 


#THIS SCRIPT WILL NOT BE ABLE TO HANDLE PASSWORD RESETS FOR NOW
def main():
    #get the  number of arguments input into the cmd line
    # Commmand line inputs are: script.py COM# LPN###
    numArg = len(sys.argv)

    #error check the number of arguments
    if numArg != 3:
        print("Invalid arguments. Expected 2. Commmand line format is: script.py COM# LPN###")
        exit(-1)

    #error check the arguments to make sure they are valid. 
    connNum = sys.argv[1]
    lpn = sys.argv[2]
    # print(connNum)
    # print(lpn)

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

    #open the file to write to
    # cwd = os.getcwd()
    # print("Current working directory: {0}".format(cwd))

    fileObj = open(lpn + '.txt', 'w')

    #https://semfionetworks.com/blog/establish-a-console-connection-within-a-python-script-with-pyserial/
    #try 2: open the serial connection 
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

    #read the rest of the output then terminate


    #Logout(serObj, fileObj)
    #Close the serial connection 
    serObj.close()

    #fileObj.write()
    fileObj.close()

    print ("Script complete. Terminating program.")
    exit(0)

#This code will keep reading until the specified string is read, at which point
#it will execute the command specified 
def ReadUntilStringIsFound(string, cmd, serialConn, file):
    #may have to add a wakeup function 
    while True:
        readdata = serialConn.readline().decode('ascii')
        file.write(readdata.rstrip() + '\n')
        

        #if the len of the data is 0, that means that there is no more output from console, 
        # send an enter command to advance the cli 
        if len(readdata) == 0:
            #have an error check here for if the code hangs 
            otherCmd = '\r'
            serialConn.write(otherCmd.encode("utf-8"))
            time.sleep(1)
        
        #The string indicating the return to the cli input has been found, break 
        if string in readdata:
            print(readdata.rstrip() + '\n')
            print(string)
            serialConn.write(cmd.encode("utf-8"))
            time.sleep(1)
            break

def LoginRoot(serialConn, file):    
    print("Device booting up...")
    #keep reading from the terminal until there is "login:"
    ReadUntilStringIsFound('login: ', 'root\r', serialConn, file)
    print("Entering default credentials...")
    print("Entering CLI...")
    ReadUntilStringIsFound('root@:RE:0% ', 'cli\r', serialConn, file)
    return None

# def Logout(serialConn, file):
#     ReadUntilStringIsFound('root> ', 'exit \r', serialConn, file)
#     ReadUntilStringIsFound('root@:RE:0% ', 'exit \r', serialConn, file)
#     return None

def ShowVersion(serialConn, file):
    print("Running show version...")
    ReadUntilStringIsFound('root>', 'show version\r', serialConn, file)
    return None

def ShowConfig(serialConn, file):
    print("Running show configuration...")
    ReadUntilStringIsFound('root>', 'show configuration | no-more\r', serialConn,file)
    return None 

def ShowChasFw(serialConn, file):
    print("Running show chassis firmware...")
    ReadUntilStringIsFound('root>', 'show chassis firmware\r', serialConn,file)
    return None

def ShowChasHw(serialConn, file):
    print("Running show chassis hardware...")
    ReadUntilStringIsFound('root>', 'show chassis hardware\r', serialConn,file)
    return None 

def ShowChasEnv(serialConn, file):
    print("Running show chassis environment...")
    ReadUntilStringIsFound('root>', 'show chassis environment\r', serialConn,file)
    return None

def ShowSysAlarms(serialConn, file):
    print("Running show system alarms...")
    ReadUntilStringIsFound('root>', 'show system alarms\r', serialConn,file)
    return None

def ShowSysStorage(serialConn, file):
    print("Running show system storage...")
    ReadUntilStringIsFound('root>', 'show system storage | no-more\r', serialConn,file)
    return None

#must also add functionality to delete license if neccessary 
def ShowSysLicense(serialConn, file):
    print("Running show system license...")
    ReadUntilStringIsFound('root>', 'show system license\r', serialConn,file)
    return None

def ShowIntTerse(serialConn, file):
    print("Running show interfaces terse...")
    ReadUntilStringIsFound('root>', 'show interfaces terse | no-more\r', serialConn,file)
    return None

def ReqSysZero(serialConn, file):
    print("Running system reboot...")
    ReadUntilStringIsFound('root>', 'request system zeroize\r', serialConn,file)
    ReadUntilStringIsFound('[yes,no] (no)', 'yes\r', serialConn, file)
    return None

def ReqPwrOff(serialConn, file):
    print("Running graceful shutdown...")
    ReadUntilStringIsFound('root>', 'request system power-off\r', serialConn,file)
    ReadUntilStringIsFound('[yes,no] (no)', 'yes\r', serialConn, file)
    return None

if __name__ == "__main__":
    main()
