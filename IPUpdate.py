import requests
import os
import time
import socket
import platform
import json

##Config##
SettingsFile = "IPUpdateSettings.json"
with open(SettingsFile) as JSONFile:
    Settings = json.load(JSONFile)

def GetSetting(SettingType, SettingName, Settings=Settings):
    return (Settings[SettingType])[SettingName]

def ChangeSetting(SettingType, SettingName, NewValue, Settings=Settings):
    (Settings[SettingType])[SettingName] = NewValue
    with open(SettingsFile, 'w+') as JSONFile:
        json.dump(Settings, JSONFile)

# Set ping command depending on platform
if "Windows" in platform.platform():
    PingCommand = "ping -n 1 8.8.8.8"
else:
    PingCommand = "ping -c 1 8.8.8.8"

##Telegram##
ChatID = GetSetting("BOTConfig", "ChatID")  # Chat ID for telegram user/group
URL = "http://api.telegram.org/bot{0}/sendMessage".format(GetSetting("BOTConfig", "Token")) # URL with bot token for sending message
Prefix = "[{0}] ~".format(socket.gethostname())

def SendMessage(Message):
    print("Sending message: {0}".format(Message))
    r = requests.post("{0}?chat_id={1}&text={2} {3}".format(URL, ChatID, Prefix, Message))

##Main Functions##
# ConnectionCheck to ensure you're connected before attempting to grab an IP
def CheckConnection(connected=False):
    while connected == False:
        if os.system(PingCommand) == 0:
            print("Network good!\n")
            connected = True
        else:
            print("Network Bad will loop!")

def CheckIP(LastIP):
    # Main loop for checking public IP address change
    while True:
        print("\nLooping\n")
        CheckConnection()  # Check device is still connected to the net
        CurrentIP = ((requests.get('http://api.ipify.org')).text).strip() # Get IP Address using puiblic API
        if CurrentIP == LastIP:
            print("IP matched! Sleeping for a few minutes!")
            time.sleep(300)
        else:
            print("IP changed!!!")
            SendMessage("Current IP address has changed! New IP is now: {0}".format(CurrentIP))
            ChangeSetting("Data", "LastIP", CurrentIP)
            LastIP = CurrentIP

# Run Main loop
CheckIP(GetSetting("Data", "LastIP"))
