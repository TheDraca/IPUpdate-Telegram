import requests
import os
import time
import socket
import platform
# When launched on boot, time is needed for a network  connection to be established
time.sleep(15)

###Config###
SettingsFile = "IPUpdateSettings.cfg"  # Location of settings file to be used


def GetSetting(Option, File=SettingsFile):
    with open(File) as Settings:
        for line in Settings:
            if Option in line:
                SettingResult = line.split("=", 1)[1]
                SettingResult = SettingResult.rstrip()
                return SettingResult


CHATID = GetSetting("CHATID")  # Chat ID for telegram user/group
TOKEN = GetSetting("TOKEN")  # Bot token for telegram bot
URL = "http://api.telegram.org/bot{0}/sendMessage".format(TOKEN)
prefix = "[{0}] ~".format(socket.gethostname())
SavedLastIP = GetSetting("SavedLastIP")


def sendmsg(ip):
    print("Sending IP change message")
    MSG = "{0} Current IP address has changed! New IP is now: {1}".format(
        prefix, ip)
    r = requests.post("{0}?chat_id={1}&text={2}".format(URL, CHATID, MSG))


def sendmsg404(ip):
    print("Sending 404 telegram message")
    MSG = "{0} Lastip address was not found! Current IP is: {1}".format(
        prefix, ip)
    r = requests.post("{0}?chat_id={1}&text={2}".format(URL, CHATID, MSG))

###IP Functions###


def getip():
    # Get IP Address using puiblic API
    website = (requests.get('http://api.ipify.org')).text
    ip = website.strip()
    print("Current Public IP is: {0}".format(ip))
    return ip


def getLip():
    # Read Last IP from file
    txt = open(SavedLastIP, "r")
    lastip = txt.read()
    txt.close()
    print("Last IP is: {0}".format(lastip))
    return lastip


def setLip(ip):
    #Write IP To lastip file#
    txt = open(SavedLastIP, "w")
    txt.write(ip)
    txt.close()


def CheckConnection(connected=False):
    # Check for web connection
    OS = platform.platform()
    while connected == False:
        if "Windows" in OS:  # Windows and Unix have diffrent parameters for ping counts becuase standards
            pingtest = os.system("ping -n 1 8.8.8.8")
        else:
            pingtest = os.system("ping -c 1 8.8.8.8")

        if pingtest == 0:
            print("Network good!\n")
            connected = True
        else:
            print("Network Bad will loop!")


def checkip(LastIP):
    # Main loop for checking public IP address change
    while True:
        print("\nLooping\n")
        CheckConnection()  # Make sure still connected before trying to get an IP!
        CurrentIP = getip()
        if CurrentIP == LastIP:
            print("IP matched! Sleeping for a few minutes!")
            time.sleep(300)
        else:
            print("IP changed!!!")
            sendmsg(CurrentIP)
            setLip(CurrentIP)
            LastIP = CurrentIP


###MAIN###
# Check if there is a last IP Address
if os.path.exists(SavedLastIP):
    print("Last IP address found!")
else:
    print("Last IP address not found")
    CurrentIP = getip()
    sendmsg404(CurrentIP)
    setLip(CurrentIP)

# Run Main loop
checkip(getLip())
