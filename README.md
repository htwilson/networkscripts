#####################################################################################################
# 1/31/2023
# Hugo Wilson
                                        README
#####################################################################################################

Python Script for Testing Juniper Devices

Overview
    The purpose of this script is to automate most testing procedures that is done for the Juniper
    EX3300 and Juniper QFX5100. This script assumes that the device has already been zeroized, and
    furthermore will serve only do conduct information gathering and license removal. The user is 
    required to manually verify that the logs created from the script pass the testing criteria for
    the device to be considered for resale. In the event that the device has a password, the user is 
    required to manually wipe the password using a reset procedure, login with the root user, and
    then zeroize the device. One that is done, the user can use the script as originally intended. 

    The script takes in 3 arguments:
        prompt> script.py COM# Device### LPN###
    
    The first argument is the Console port that the device being tested is connected to. The second 
    argument is the model of the Juniper switch (EX3300/QFX5100). The last argument is the LPN of the 
    device being tested. Whether the arguments are entered correctly or incorrectly, the script will 
    provide feedback on the terminal. If there are no issues, the tests will run, and the script will 
    periodically write to the console to tell the user what current tests are being run. 

    It is important to note that for the QFX model, the command show chassis environmentals will return
    a status of testing if the fans are still being tested. Testing takes several minutes to complete
    and during this time, the device fans will be loud. To ensure that the script will capture the 
    results of the test, the script will prompt the user to press enter when the device fans have stopped
    testing. As a result, testing the QFX5100 requires an additional user input when the script asks for 
    it.

    To test the physical port functionality should be plugged in as soon as possible, and ideally 
    before running the script. As long as the ports are plugged in before the command "show interfaces terse" 
    is run, then the results of the commands should display properly. To aid this testing for the EX3300
    will pause for 10 seconds to ensure that connections are properly initialized. Also, in regards to 
    the QFX5100, when the device asks the user to press enter when the fans finish testing, the user 
    can also take this time to check that the connections are properly initialized.

Contents 
    junos_test_script_v2.py
        The script that automates some testing procedures for these juniper devices

Notes
    Sometimes the device will log itself out, the script cannot handle this bug. 

    This script will not handle password resets, keystrokes and an additional library may be needed to 
    implement this. 
    
    This script cannot detect for itself when QFX5100 fans finish testing. A possible solution is to 
    enter the command 'show chassis env fans' continuously in a loop and read the output from the serial
    until the code detects the status changes from TESTING to OK 