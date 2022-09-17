from datetime import datetime
import json
import os
from time import sleep
from socket import gethostname
from platform import platform
import requests

#Funtion for logging and printing outputs with a time stamp
def LogAndPrint(message, File="Log.txt"):
    TimeStamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    message=TimeStamp+" - "+message
    print(message)
    with open(File, "a+") as LogFile:
        LogFile.write(message+"\n")

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

TimeToSleep=int(GetSetting("Data", "TimeBetweenChecks"))

#Domain Functions
GoDaddyDomainEnabled=GetSetting("GoDaddyDomainConfig", "Enabled")
if GoDaddyDomainEnabled == "True":
    from godaddypy import Client, Account
    GoDaddy_Domain=GetSetting("GoDaddyDomainConfig", "Domain")
    GoDaddy_Key=GetSetting("GoDaddyDomainConfig", "Key")
    GoDaddy_Secret=GetSetting("GoDaddyDomainConfig","Secret")
    GoDaddy_RecordType=GetSetting("GoDaddyDomainConfig","RecordType")
    GoDaddy_RecordName=GetSetting("GoDaddyDomainConfig","RecordName")


#Domain Functions
NameCheapDomainEnabled=GetSetting("NameCheapDomainConfig", "Enabled")
if NameCheapDomainEnabled == "True":
    NameCheap_Domain=GetSetting("NameCheapDomainConfig", "Domain")
    NameCheap_DDNS_Passwd=GetSetting("NameCheapDomainConfig","DDNS_Passwd")
    NameCheap_RecordType=GetSetting("NameCheapDomainConfig","RecordType")
    NameCheap_RecordName=GetSetting("NameCheapDomainConfig","RecordName")


def UpdateDomain(CurrentIP):
    if GoDaddyDomainEnabled == "True":
        LogAndPrint("Updating GoDaddy domain DNS")
        client = Client(Account(api_key=GoDaddy_Key, api_secret=GoDaddy_Secret))
        client.update_record_ip(CurrentIP, GoDaddy_Domain, GoDaddy_RecordName, GoDaddy_RecordType)
    if NameCheapDomainEnabled == "True":
        LogAndPrint("Updating NameCheap domain DNS")
        requests.get("https://dynamicdns.park-your-domain.com/update?host={0}&domain={1}&password={2}&ip={3}".format(NameCheap_RecordName,NameCheap_Domain,NameCheap_DDNS_Passwd,CurrentIP))
    if GoDaddyDomainEnabled != "True" and NameCheapDomainEnabled != "True":
        LogAndPrint("Updating domain not enabled... Skipping")

##Main Functions##
def CheckConnection(): # ConnectionCheck to ensure you're connected before attempting to grab an IP
    while os.system(PingCommand) != 0:
        LogAndPrint("Network Bad will loop!")

def SendMessage(Message):
    if GetSetting("BOTConfig", "Enabled") == "True":
        MessagePrefix = "[{0}] ~ ".format(gethostname())
        for ChatID in GetSetting("BOTConfig", "ChatIDs"):
            LogAndPrint("Sending telegram message to {0}".format(ChatID))
            requests.post("http://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}{3}&disable_notification={4}".format(GetSetting("BOTConfig", "Token"), ChatID, MessagePrefix, Message, GetSetting("BOTConfig", "SilentMessage")))

def CheckIP(LastIP):
    # Main loop for checking public IP address change
    while True:
        CheckConnection()  # Check device is still connected to the net
        CurrentIP = ((requests.get('http://api.ipify.org')).text).strip() # Get IP Address using puiblic API
        if CurrentIP == LastIP:
            LogAndPrint("Current IP matched IP in JSON file")
        else:
            if "<" in  str(CurrentIP):
                LogAndPrint("HTML returned rather than an IP... ignoreing")
            else:
                LogAndPrint("IP Has changed! Last known IP was {0}, New IP is now: {1}".format(LastIP,CurrentIP))
                UpdateDomain(CurrentIP)
                SendMessage("Current IP address has changed! New IP is now: {0}".format(CurrentIP))
                ChangeSetting("Data", "LastIP", CurrentIP)
                LastIP = CurrentIP
        LogAndPrint("Sleeping for {0} secs".format(TimeToSleep))
        sleep(TimeToSleep)

# Run Main loop
CheckIP(GetSetting("Data", "LastIP"))
