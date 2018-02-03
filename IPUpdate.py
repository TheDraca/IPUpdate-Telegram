import requests
import os.path
import time
import socket
# When launched on boot, time is needed for a network  connection to be established
#time.sleep(15)


###Telegram config###

CHATID = ""  # Chat ID for telegram user/group
TOKEN = ""  # Bot token for telegram bot
URL = "http://api.telegram.org/bot{0}/sendMessage".format(TOKEN)
prefix = "[{0}] ~".format(socket.gethostname())

def sendmsg(ip):
    print("Sending IP change message")
    MSG = "{0} Current IP address has changed! New IP is now: {1}".format(prefix, ip)
    r = requests.post("{0}?chat_id={1}&text={2}".format(URL, CHATID, MSG))

def sendmsg404(ip):
    print("Sending 404 telegram message")
    MSG = "{0} Lastip address was not found! Current IP is: {1}".format(prefix, ip)
    r = requests.post("{0}?chat_id={1}&text={2}".format(URL, CHATID, MSG))

###End of Telegram config###


###IP Functions###
def getip():
    website = requests.get('http://api.ipify.org')
    ip = website.text
    print("Current Public IP is: {0}".format(ip))
    return ip

def getLip():
    #Read Last IP from file#
    txt = open("lastip.txt", "r")
    lastip = txt.read()
    txt.close()
    print("Last IP is: {0}".format(lastip))
    return lastip

def setLip(ip):
    #Write IP To lastip file#
    txt = open("lastip.txt", "w")
    txt.write(ip)
    txt.close()
    lastip = ip

def CheckConnection(connected):
    while connected == False:
        try:
            getip()
        except:
            print("getip failed, likely there's no web connection - looping until solved")
            time.sleep(2)
        connected = True
        print("getip success!!")
###End of IP Functions###


# Main loop for checking public IP address
def checkip(ipchange):
    while ipchange == False:
        print("\nLooping\n")
        if getip() == getLip():
            print("IP matched! Sleeping for a few minutes!")
            time.sleep(120)
            ipchange = False
        else:
            print("IP changed!!!")
            sendmsg(getip())
            setLip(getip())


###MAIN###
#getip()
connected = False
ipchange = False
CheckConnection(connected)

# Check if IP address has changed from last run
if os.path.exists("lastip.txt"):
    print("Last IP address found!")
else:
    print("Last IP address not found")
    sendmsg404(getip())
    setLip(getip())

if getip() == getLip():
    print("MATCH! - Not sending telegram message")
    ipchange = False
else:
    print("NO MACTCH - Sending telegram message")
    sendmsg(getip())
    setLip(getip())
    ipchange = False

# Run main loop
checkip(ipchange)
