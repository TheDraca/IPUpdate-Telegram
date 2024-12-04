import logging
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


#Set debug level to debug if the settings file says so, else we're on info
if GetSetting("Data", "DebugEnabled").lower() == "true":
    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s',filename=(GetSetting("Data", "LogFile")))
else:
    logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s',filename=(GetSetting("Data", "LogFile")))

#Set request's logging level to warning to avoid tokens in log file
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


#Announce the script has started
logging.info("---------- Starting IPUpdate! ----------")



###Setup###
if "Windows" in platform(): # Set ping command depending on platform
    PingCommand = "ping -n 1 8.8.8.8"
    logging.debug("Windows detected using ping -n for internet checks")
else:
    logging.debug("NOT Windows detected using ping -c for internet checks")
    PingCommand = "ping -c 1 8.8.8.8"

TimeToSleep=int(GetSetting("Data", "TimeBetweenChecks"))


#Domain Functions for Cloudflare
if GetSetting("CloudflareDomainConfig", "Enabled").lower() == "true":
    CloudflareDomainEnabled=True
else:
    CloudflareDomainEnabled=False

if CloudflareDomainEnabled:
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
    if CloudflareDomainEnabled:
        logging.info("Updating Cloudflare domain DNS")
        CloudflareCurrentDNSEntryID=GetCloudfalreEntryID(Cloudflare_RecordType,Cloudflare_RecordName,Cloudflare_Domain,CloudflareAPIURL)
        requests.patch("{0}/{1}".format(CloudflareAPIURL,CloudflareCurrentDNSEntryID,CurrentIP), headers={"Authorization": "Bearer {0}".format(Cloudflare_Token)}, json={'content': CurrentIP})
    else:
        logging.info("Updating domain not enabled... Skipping")

##Main Functions##
def CheckConnection(): # ConnectionCheck to ensure you're connected before attempting to grab an IP
    while os.system(PingCommand) != 0:
        logging.warning("Network Bad will loop!")

def SendMessage(Message):
    try:
        if GetSetting("BOTConfig", "Enabled").lower () == "true":
            MessagePrefix = "[{0}] ~ ".format(gethostname())
            for ChatID in GetSetting("BOTConfig", "ChatIDs"):
                logging.info("Sending telegram message to {0}".format(ChatID))
                MessageUpdate=requests.post("https://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}{3}&disable_notification={4}".format(GetSetting("BOTConfig", "Token"), ChatID, MessagePrefix, Message, GetSetting("BOTConfig", "SilentMessage")))

                if int(MessageUpdate.status_code) != 200:
                    logging.warning("HTTP error {0}".format(MessageUpdate.status_code))
                    raise Exception ("http_error")
    except:
        logging.warning("Error sending telegram message")
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
                    logging.info("Current IP matched IP in JSON file")
                else:
                    if "<" in  str(CurrentIP):
                        logging.warning("HTML returned rather than an IP... ignoring")
                    else:
                        logging.info("IP Has changed! Last known IP was {0}, New IP is now: {1}".format(LastIP,CurrentIP))
                        UpdateDomain(CurrentIP)
                        SendMessage("Current IP address has changed! New IP is now: {0}".format(CurrentIP))
                        ChangeSetting("Data", "LastIP", CurrentIP)
                        LastIP = CurrentIP
        except:
            logging.error("Unknown error occured, looping")
        logging.info("Sleeping for {0} secs".format(TimeToSleep))
        sleep(TimeToSleep)



# Run Main loop
CheckIP(GetSetting("Data", "LastIP"))
