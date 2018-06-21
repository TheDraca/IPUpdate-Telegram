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

if "Windows" in platform.platform(): # Set ping command depending on platform
    PingCommand = "ping -n 1 8.8.8.8"
else:
    PingCommand = "ping -c 1 8.8.8.8"

##Main Functions##
def CheckConnection(connected=False): # ConnectionCheck to ensure you're connected before attempting to grab an IP
    while connected == False:
        if os.system(PingCommand) == 0:
            print("Network good!\n")
            connected = True
        else:
            print("Network Bad will loop!")

def SendMessage(Message):
    MessagePrefix = "[{0}] ~ ".format(socket.gethostname())
    for ChatID in GetSetting("BOTConfig", "ChatIDs"):
        r = requests.post("http://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}{3}".format(GetSetting("BOTConfig", "Token"), ChatID, MessagePrefix, Message))

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
