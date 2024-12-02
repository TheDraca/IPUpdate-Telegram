from datetime import datetime
import json
import os
from time import sleep
from socket import gethostname
from platform import platform
import requests

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

#Funtion for logging and printing outputs with a time stamp
def LogAndPrint(message, File=GetSetting("Data","LogFile")):
    TimeStamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    message=TimeStamp+" - "+message
    print(message)
    with open(File, "a+") as LogFile:
        LogFile.write(message+"\n")


###Setup###
if "Windows" in platform(): # Set ping command depending on platform
    PingCommand = "ping -n 1 8.8.8.8"
else:
    PingCommand = "ping -c 1 8.8.8.8"

TimeToSleep=int(GetSetting("Data", "TimeBetweenChecks"))


#Domain Functions for Cloudflare
CloudflareDomainEnabled=GetSetting("CloudflareDomainConfig", "Enabled")
if CloudflareDomainEnabled == "True":
    Cloudflare_Domain=GetSetting("CloudflareDomainConfig", "Domain")
    Cloudflare_Token=GetSetting("CloudflareDomainConfig","Token")
    Cloudflare_ZoneID=GetSetting("CloudflareDomainConfig","ZoneID")
    Cloudflare_RecordType=GetSetting("CloudflareDomainConfig","RecordType")
    Cloudflare_RecordName=GetSetting("CloudflareDomainConfig","RecordName")

    CloudflareAPIURL="https://api.cloudflare.com/client/v4/zones/{0}/dns_records".format(Cloudflare_ZoneID)

    #Extra function for grabbing existing DNS entry ID
    def GetCloudfalreEntryID(Cloudflare_RecordType,Cloudflare_RecordName,Cloudflare_Domain,CloudflareAPIURL):
        #Store API Response
        CloudflareResponse=requests.get("{0}?type={1}&name={2}.{3}".format(CloudflareAPIURL,Cloudflare_RecordType,Cloudflare_RecordName,Cloudflare_Domain), headers={"Authorization": "Bearer {0}".format(Cloudflare_Token)})

        #Turn the response into a json and pull the results
        CloudflareResponse=(CloudflareResponse.json()).get("result")

        #Store the results as dir:
        CloudflareResponse=dict(CloudflareResponse[0]).items()

        #Find the id with a quick search:
        for Key,Value in CloudflareResponse:
            if Key == "id":
                CloudflareCurrentDNSEntryID=Value
                break
        #Returrn this value
        return CloudflareCurrentDNSEntryID


def UpdateDomain(CurrentIP):
    if CloudflareDomainEnabled == "True":
        LogAndPrint("Updating Cloudflare domain DNS")
        CloudflareCurrentDNSEntryID=GetCloudfalreEntryID(Cloudflare_RecordType,Cloudflare_RecordName,Cloudflare_Domain,CloudflareAPIURL)
        requests.patch("{0}/{1}".format(CloudflareAPIURL,CloudflareCurrentDNSEntryID,CurrentIP), headers={"Authorization": "Bearer {0}".format(Cloudflare_Token)}, json={'content': CurrentIP})
    else:
        LogAndPrint("Updating domain not enabled... Skipping")

##Main Functions##
def CheckConnection(): # ConnectionCheck to ensure you're connected before attempting to grab an IP
    while os.system(PingCommand) != 0:
        LogAndPrint("Network Bad will loop!")

def SendMessage(Message):
    try:
        if GetSetting("BOTConfig", "Enabled") == "True":
            MessagePrefix = "[{0}] ~ ".format(gethostname())
            for ChatID in GetSetting("BOTConfig", "ChatIDs"):
                LogAndPrint("Sending telegram message to {0}".format(ChatID))
                MessageUpdate=requests.post("https://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}{3}&disable_notification={4}".format(GetSetting("BOTConfig", "Token"), ChatID, MessagePrefix, Message, GetSetting("BOTConfig", "SilentMessage")))

                if int(MessageUpdate.status_code) != 200:
                    LogAndPrint("HTTP error {0}".format(MessageUpdate.status_code))
                    raise Exception ("http_error")
    except:
        LogAndPrint("Error sending telegram message")
def CheckIP(LastIP):
    # Main loop for checking public IP address change
    while True:
        try:
            CheckConnection()  # Check device is still connected to the net
            APIResponse=requests.get('https://api.ipify.org?format=json') # Get IP Address using public API
            if int(APIResponse.status_code) == 200:
                CurrentIP=json.loads(APIResponse.text) #Json of public api in format {"ip":"1.2.3.4"}
                CurrentIP=CurrentIP["ip"] #Store just the IP i.e 1.2.3.4

                if CurrentIP == LastIP:
                    LogAndPrint("Current IP matched IP in JSON file")
                else:
                    if "<" in  str(CurrentIP):
                        LogAndPrint("HTML returned rather than an IP... ignoring")
                    else:
                        LogAndPrint("IP Has changed! Last known IP was {0}, New IP is now: {1}".format(LastIP,CurrentIP))
                        UpdateDomain(CurrentIP)
                        SendMessage("Current IP address has changed! New IP is now: {0}".format(CurrentIP))
                        ChangeSetting("Data", "LastIP", CurrentIP)
                        LastIP = CurrentIP
        except:
            LogAndPrint("Unknown error occured, looping")
        LogAndPrint("Sleeping for {0} secs".format(TimeToSleep))
        sleep(TimeToSleep)

# Run Main loop
CheckIP(GetSetting("Data", "LastIP"))
