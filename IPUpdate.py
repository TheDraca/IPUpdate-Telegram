import requests
import os
import time
import socket
import platform
import json

##Config##
SettingsFile= "IPUpdateSettings.json"
with open(SettingsFile) as JSONFile:
    Settings = json.load(JSONFile)

def GetSetting(SettingType, SettingName, Settings=Settings):
        return (Settings[SettingType])[SettingName]

def ChangeSetting(SettingType, SettingName, NewValue, Settings=Settings):
    (Settings[SettingType])[SettingName] = NewValue
    with open(SettingsFile, 'w+') as JSONFile:
        json.dump(Settings,JSONFile)

ChatID = GetSetting("BOTConfig","ChatID")  # Chat ID for telegram user/group
URL = "http://api.telegram.org/bot{0}/sendMessage".format(GetSetting("BOTConfig","Token")) #URL with bot token for sending message
Prefix = "[{0}] ~".format(socket.gethostname())

##Telegram Function##
def SendMessage(Message):
    print("Sending message: {0}".format(Message))
    r = requests.post("{0}?chat_id={1}&text={2}".format(URL, ChatID, Message))

##Main Functions##
#ConnectionCheck to ensure you're connected before attempting to grab an IP
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

# Get IP Address using puiblic API
def GetIP():
    IP = ((requests.get('http://api.ipify.org')).text).strip()
    print("Current Public IP is: {0}".format(IP))
    return IP

def CheckIP(LastIP):
    # Main loop for checking public IP address change
    while True:
        print("\nLooping\n")
        CheckConnection()  # Check device is still connected to the net
        CurrentIP = GetIP()
        if CurrentIP == LastIP:
            print("IP matched! Sleeping for a few minutes!")
            time.sleep(300)
        else:
            print("IP changed!!!")
            SendMessage("{0} Current IP address has changed! New IP is now: {1}".format(Prefix, CurrentIP))
            ChangeSetting("Data","LastIP",CurrentIP)
            LastIP = CurrentIP

# Run Main loop
CheckIP(GetSetting("Data","LastIP"))
