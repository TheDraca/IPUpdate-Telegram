import requests
import json
import os
from time import sleep
from socket import gethostname
from platform import platform

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

###Setup###
if "Windows" in platform(): # Set ping command depending on platform
    PingCommand = "ping -n 1 8.8.8.8"
else:
    PingCommand = "ping -c 1 8.8.8.8"

#Domain Functions
DomainEnabled=GetSetting("DomainConfig", "Enabled")
if DomainEnabled == "True":
    from godaddypy import Client, Account
    Domain=GetSetting("DomainConfig", "Domain")
    Key=GetSetting("DomainConfig", "Key")
    Secret=GetSetting("DomainConfig","Secret")

def UpdateDomain(CurrentIP):
    if DomainEnabled == "True":
        print("Updating domain DNS")
        client = Client(Account(api_key=Key, api_secret=Secret))
        client.update_record_ip(CurrentIP, Domain, '@', 'A')
    else:
        print("Updating domain not enabled....")

##Main Functions##
def CheckConnection(): # ConnectionCheck to ensure you're connected before attempting to grab an IP
    while os.system(PingCommand) != 0:
            print("Network Bad will loop!")

def SendMessage(Message):
    if GetSetting("BOTConfig", "Enabled") == "True":
        MessagePrefix = "[{0}] ~ ".format(gethostname())
        for ChatID in GetSetting("BOTConfig", "ChatIDs"):
            requests.post("http://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}{3}&disable_notification={4}".format(GetSetting("BOTConfig", "Token"), ChatID, MessagePrefix, Message, GetSetting("BOTConfig", "SilentMessage")))
            print(GetSetting("BOTConfig", "SilentMessage"))

def CheckIP(LastIP):
    # Main loop for checking public IP address change
    while True:
        print("\nLooping\n")
        CheckConnection()  # Check device is still connected to the net
        CurrentIP = ((requests.get('http://api.ipify.org')).text).strip() # Get IP Address using puiblic API
        if CurrentIP == LastIP:
            print("IP matched! Sleeping for a few minutes!")
        else:
            if "<" in  str(CurrentIP):
                print("HTML returned rather than an IP... ignoreing")
            else:
                print("IP changed!!!")
                UpdateDomain(CurrentIP)
                SendMessage("Current IP address has changed! New IP is now: {0}".format(CurrentIP))
                ChangeSetting("Data", "LastIP", CurrentIP)
                LastIP = CurrentIP
        sleep(300)

# Run Main loop
CheckIP(GetSetting("Data", "LastIP"))
