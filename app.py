from flask import Flask, request
import consul
import requests
import json
import sys

app = Flask(__name__)

csl = consul.Consul()
global TOKEN
TOKEN = None

MESSAGE_URL = "https://graph.facebook.com/v2.6/me/messages"
SETTINGS_URL = "https://graph.facebook.com/v2.6/me/thread_settings"
USER_URL = "https://graph.facebook.com/v2.6/"

@app.route("/fhook", methods=["GET"])
def verify_bot():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        return request.args.get["hub.hallenge"], 200
    return "OK", 200

@app.route("/fhook", methods=["POST"])
def webhook():
    rx_data = request.get_json()
    for entry in rx_data["entry"]:
        for evt in entry["messaging"]:
            try:
                sender_id = evt["sender"]["id"]
                
                msg = None
                if "message" in evt: message = evt["message"]["text"]
                elif "postback" in evt: 
                    params = {"access_token": TOKEN}
                    r = requests.get(USER_URL+str(sender_id), params=params)
                    if r.status_code == 200:
                        r = r.json()
                        user_name = r["first_name"] 
                        message = "Hi "+str(user_name)+", what would you like to do tonight?"

                if message is not None: handleMsg(sender_id, message)
                return "OK", 200
            except:
                e = sys.exc_info()[0]
                print(e) 
                return "FAIL", 501
                pass
    return "OK", 200

#The handler will be bottleneck in case of heavy load. So it it should be point of scaling
#For not heavy load should be OK
def handleMsg(sid, msg):
    params = {"access_token": TOKEN}
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "recipient": {"id": sid},
        "message": {"text": msg}
    })
    try: r = requests.post(MESSAGE_URL, params=params, headers=headers, data=data)
    except: pass

def FBWelcomeMessage():
    params = {"access_token": TOKEN}
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "setting_type": "greeting",
        "greeting": {"text": "Hi {{user_first_name}}. I’ll give you personal event recommendations. Let’s start talking."}
    })
    try: r = requests.post(SETTINGS_URL, params=params, headers=headers, data=data)
    except: pass

def FBStartButton():
    params = {"access_token": TOKEN}
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "setting_type": "call_to_actions",
        "thread_state": "new_thread",
        "call_to_actions": [{"payload": "Get started"}]
    })
    try: r = requests.post(SETTINGS_URL, params=params, headers=headers, data=data)
    except: pass

def main():
    try:
        global TOKEN
        k, v = csl.kv.get("Facebook/Config/TOKEN")
        TOKEN = str(v["Value"].decode("utf-8"))

        FBWelcomeMessage()
        FBStartButton()
        app.run(port=8000, host="127.0.0.1")
    except: pass


if __name__ == "__main__": main()
