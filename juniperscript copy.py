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
    Logout(serObj, fileObj)
    #Close the serial connection 
    serObj.close()

    #fileObj.write()
    fileObj.close()

    exit(0)



def LoginRoot(serialConn, file):
    
    #wake up the terminal 
    cmd = '\r'
    serialConn.write(cmd.encode("utf-8"))
    time.sleep(1)

    #keep reading from the terminal until there is "login:"
    WaitUntilStringIsRead('login: ', 'root\r', serialConn, file)
    # while True:
    #     readdata = serialConn.readline().decode('ascii')
    #     file.write(readdata.rstrip() + '\n')
    #     if 'login: ' in readdata:
    #         #Login to the device
    #         cmd = 'root\r'
    #         serialConn.write(cmd.encode("utf-8"))
    #         time.sleep(1)
    #         break

    WaitUntilStringIsRead('root@:RE:0% ', 'cli\r', serialConn, file)
    #Keep reading until the root prompt appears, then enter the cli 
    # while True:
    #     readdata = serialConn.readline().decode('ascii')
    #     file.write(readdata.rstrip() + '\n')
    #     if 'root@:RE:0% ' in readdata:
    #         #enter the cli
    #         cmd = 'cli\r'
    #         serialConn.write(cmd.encode("utf-8"))
    #         time.sleep(1)
    #         break

    return None

def WaitUntilStringIsRead(string, cmd, serialConn, file):
    #may have to add a wakeup function 
    while True:
        readdata = serialConn.readline().decode('ascii')
        file.write(readdata.rstrip() + '\n')
        print(readdata.rstrip() + '\n')
        print(string)
        if string in readdata:
            serialConn.write(cmd.encode("utf-8"))
            time.sleep(1)
            break

#this function will wait for the device to boot up and then login as the root 
# def LoginRoot1(serialConn, file):
    
#     #wake up the terminal 
#     cmd = '\r'
#     serialConn.write(cmd.encode("utf-8"))
#     time.sleep(1)

#     while True:
#         #80-82 moved into inf loop 
#         readdata = serialConn.readline().decode('ascii')
#         file.write(readdata.rstrip() + '\n')
#         if 'login: ' in readdata:
#             break

#     #Login to the device
#     cmd = 'root\r'
#     serialConn.write(cmd.encode("utf-8"))
#     time.sleep(1)

#     #Enter the cli of the device
#     cmd = 'cli\r'
#     serialConn.write(cmd.encode("utf-8"))
#     time.sleep(1)

#     return None

def Logout(serialConn, file):
    # cmd = 'exit\r'
    # serialConn.write(cmd.encode("utf-8"))
    # time.sleep(1)

    # while True:
    #     readdata = serialConn.readline().decode('ascii')
    #     file.write(readdata.rstrip() + '\n')
    #     if 'root@:RE:0% ' in readdata:
    #         break

    WaitUntilStringIsRead('root> ', 'exit \r', serialConn, file)

    # cmd = 'exit\r'
    # serialConn.write(cmd.encode("utf-8"))
    # time.sleep(1)

    # while True:
    #     readdata = serialConn.readline().decode('ascii')
    #     file.write(readdata.rstrip() + '\n')
    #     if 'login: ' in readdata:
    #         break

    WaitUntilStringIsRead('root@:RE:0% ', 'exit \r', serialConn, file)


    return None

def ShowVersion(serialConn, file):
    # cmd = 'show version\r'
    # serialConn.write(cmd.encode("utf-8"))
    # time.sleep(1)

    # while True:
    #     readdata = serialConn.readline().decode('ascii')
    #     file.write(readdata.rstrip() + '\n')
    #     if 'root> ' in readdata:
    #         break
    WaitUntilStringIsRead('root>', 'show version\r', serialConn, file)
        
    return None

def ShowConfig(serialConn, file):
    WaitUntilStringIsRead('root>', 'show config\r', serialConn,file)
    return None 

def ShowChasFw(serialConn, file):
    WaitUntilStringIsRead('root>', 'show chassis firmware\r', serialConn,file)
    return None

def ShowChasHw(serialConn, file):
    WaitUntilStringIsRead('root>', 'show chassis hardware\r', serialConn,file)
    return None 

def ShowChasEnv(serialConn, file):
    WaitUntilStringIsRead('root>', 'show chassis environment\r', serialConn,file)
    return None

def ShowSysAlarms(serialConn, file):
    WaitUntilStringIsRead('root>', 'show system alarms\r', serialConn,file)
    return None

def ShowSysStorage(serialConn, file):
    WaitUntilStringIsRead('root>', 'show system storage\r', serialConn,file)
    return None

#must also add functionality to delete license if neccessary 
def ShowSysLicense():
    return None

def ShowIntTerse():
    return None

def ReqSysZero():
    return None

def gracefulShut():
    return None

if __name__ == "__main__":
    main()
