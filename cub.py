#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# apt-get install python3-dev python3-pip -y
# python3 -m pip install colorama readchar requests

from time import sleep
from threading import Thread
from colorama import init

import atexit, requests, hashlib, random
import readchar, hmac, uuid, os, string

import ctypes
import requests
import colorama
import readchar

BREAK = 3
LINE_FEED = 13
BACK_SPACE = 127 if os.name == "posix" else 8

ERROR = "[\x1b[31m-\x1b[39m]"
SUCCESS = "[\x1b[32m+\x1b[39m]"
INPUT = "[\x1b[33m?\x1b[39m]"
INFO = "[\x1b[35m*\x1b[39m]"

RED = "\033[1;31;40m"
GREEN = "\033[1;32;40m"
BLUE = "\033[1;36;40m"
WHITE = "\033[1;37;40m"


IG_EDIT_PROFILE = "{{\"gender\":\"3\",\"username\":\"{}\",\"first_name\":\"Eat my butt :p\",\"email\":\"{}\"}}"
IG_LOGIN_ACTUAL = "{{\"username\":\"{}\",\"device_id\":\"{}\",\"password\":\"{}\",\"login_attempt_count\":\"0\"}}"

IG_API_CONTENT_TYPE = "application/x-www-form-urlencoded; charset=UTF-8"
IG_API_USER_AGENT = "Instagram 84.0.0.21.105 Android (24/7.0; 380dpi; 1080x1920; OnePlus; ONEPLUS A3010; OnePlus3T; qcom; en_US; 145652094)"

class Signatures(object):
        def __init__(self):
                super(Signatures, self).__init__()
                self.key = b"02271fcedc24c5849a7505120650925e2b4c5b041e0a0bb0f82f4d41cfcdc944"

        def gen_uuid(self):
                return str(uuid.uuid4())

        def gen_device_id(self):
                return "android-{}".format(hashlib.md5(self.gen_uuid().encode("utf-8")).hexdigest()[:16])

        def gen_signature(self, data):
                return hmac.new(self.key, str.encode(data), hashlib.sha256).hexdigest()

        def sign_post_data(self, data):
                return "signed_body={}.{}&ig_sig_key_version=4".format(self.gen_signature(data), data)

class Device(object):
        def __init__(self):
                super(Device, self).__init__()
                self.filepath = os.path.expanduser("~/.madara-turbo.ini")

                if (os.path.isfile(self.filepath)):
                        if (self.read_ini(self.filepath)):
                                return

                self.create_device_ini()
                self.write_ini(self.filepath)

        def create_device_ini(self):
                self.adid = Signatures().gen_uuid()
                self.uuid = Signatures().gen_uuid()
                self.phone_id = Signatures().gen_uuid()
                self.device_id = Signatures().gen_device_id()

        def read_ini(self, filename):
                lines = [line.rstrip("\r\n") for line in open(filename, "r")]

                for line in lines:
                        if (line.startswith("adid=")):
                                self.adid = line.split("=")[1]
                        elif (line.startswith("uuid=")):
                                self.uuid = line.split("=")[1]
                        elif (line.startswith("phoneid=")):
                                self.phone_id = line.split("=")[1]
                        elif (line.startswith("deviceid=")):
                                self.device_id = line.split("=")[1]

                return None not in (self.adid, self.uuid, self.phone_id, self.device_id)

        def write_ini(self, filename):
                print("; Madara's Instagram Turbo", file=open(filename, "w"))
                print("; Information used for device identification\r\n", file=open(filename, "a"))
                print("[Device]\r\nadid={}\r\nuuid={}".format(self.adid, self.uuid), file=open(filename, "a"))
                print("phoneid={}\r\ndeviceid={}".format(self.phone_id, self.device_id), file=open(filename, "a"))

class Instagram(object):
        def __init__(self):
                super(Instagram, self).__init__()
                self.device = Device()
                self.url = "https://i.instagram.com/api/v1"

                self.attempts = 0
                self.rs = 0
                self.running = True
                self.logged_in = False
                self.session_id = None

                self.email = None
                self.username = None
                self.spam_blocked = False
                self.rate_limited = False
                self.missed_swap = False
                self.claimed = False

        def login(self, username, password):
                response = requests.post(self.url + "/accounts/login/", headers={
                        "Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate",
                        "Accept-Language": "en-US",
                        "User-Agent": IG_API_USER_AGENT,
                        "Content-Type": IG_API_CONTENT_TYPE,
                        "X-IG-Capabilities": "3brTvw==",
                        "X-IG-Connection-Type": "WIFI"
                }, data=Signatures().sign_post_data(IG_LOGIN_ACTUAL.format(
                        username, self.device.device_id, password
                )))

                if (response.status_code == 200):
                        self.session_id = response.cookies["sessionid"]

                response = response.json()

                if (response["status"] == "fail"):
                        if (response["message"] == "challenge_required"):
                                print("{} Please verify this login and make sure 2FA is disabled".format(ERROR))
                        else:
                                print("{} {}".format(ERROR, response["message"]))
                elif (response["status"] == "ok"):
                        self.logged_in = True

                        if (self.get_profile_info()):
                                print("{} Successfully logged in".format(SUCCESS))
                                return self.logged_in
                        else:
                                print("{} Successfully logged in but failed to fetch profile information, this may be due to a rate limit".format(ERROR))
                else:
                        print("{} An unknown login error occured".format(ERROR))

                return False

        def logout(self):
                if (not self.logged_in):
                        return False

                return "\"status\": \"ok\"" in requests.post(self.url + "/accounts/logout/", headers={
                        "Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate",
                        "Accept-Language": "en-US",
                        "User-Agent": IG_API_USER_AGENT,
                        "Content-Type": IG_API_CONTENT_TYPE,
                        "X-IG-Capabilities": "3brTvw==",
                        "X-IG-Connection-Type": "WIFI"
                }, cookies={
                        "sessionid": self.session_id
                }).text

        def update_consent(self):
                response = requests.post(self.url + "/consent/update_dob/", headers={
                        "Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate",
                        "Accept-Language": "en-US",
                        "User-Agent": IG_API_USER_AGENT,
                        "Content-Type": IG_API_CONTENT_TYPE,
                        "X-IG-Capabilities": "3brTvw==",
                        "X-IG-Connection-Type": "WIFI"
                }, data=Signatures().sign_post_data(
                        "{\"current_screen_key\":\"dob\",\"day\":\"1\",\"year\":\"1998\",\"month\":\"1\"}"
                ), cookies={
                        "sessionid": self.session_id
                })

                if ("\"status\": \"ok\"" in response.text):
                        print("{} Successfully updated consent to GDPR".format(SUCCESS))
                        return self.get_profile_info()

                print("{} Failed to consent to GDPR, use an IP that is not from Europe".format(ERROR))
                return False

        def get_profile_info(self):
                response = requests.get(self.url + "/accounts/current_user/?edit=true", headers={
                        "Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate",
                        "Accept-Language": "en-US",
                        "User-Agent": IG_API_USER_AGENT,
                        "X-IG-Capabilities": "3brTvw==",
                        "X-IG-Connection-Type": "WIFI"
                }, cookies={
                        "sessionid": self.session_id
                })

                if ("\"consent_required\"" in response.text):
                        return self.update_consent()
                elif ("few minutes" in response.text):
                        return False

                response = response.json()
                self.email = response["user"]["email"]
                self.username = response["user"]["username"]

                return self.email is not None and self.username is not None

        def get_target_id(self):
                try:
                        return requests.get(self.url + "/users/{}/usernameinfo/".format(self.target), headers={
                                "Accept": "*/*",
                                "Accept-Encoding": "gzip, deflate",
                                "Accept-Language": "en-US",
                                "User-Agent": IG_API_USER_AGENT,
                                "X-IG-Capabilities": "3brTvw==",
                                "X-IG-Connection-Type": "WIFI"
                        }, cookies={
                                "sessionid": self.session_id
                        }).json()["user"]["pk"]
                except:
                        return False

        def build_claim_data(self):
                self.check_url = "{}/feed/user/{}/reel_media/".format(self.url, self.target_id)
                self.claim_data = Signatures().sign_post_data(IG_EDIT_PROFILE.format(self.target, self.email))

        def target_available(self):
                response = requests.get(self.check_url, headers={
                        "Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate",
                        "Accept-Language": "en-US",
                        "User-Agent": IG_API_USER_AGENT,
                        "X-IG-Capabilities": "3brTvw==",
                        "X-IG-Connection-Type": "WIFI"
                }, cookies={
                        "sessionid": self.session_id,
                        "ds_user_id": random_id(random.choice([9, 10, 11, 12]))
                }, timeout=1).text

                if ("few minutes" in response):
                        self.rate_limited = True
                        self.running = False
                #print(response)

                return "{" in response and "\"{}\"".format(self.target) not in response

        def claim_target(self):
                response = requests.post(self.url + "/accounts/edit_profile/", headers={
                        "Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate",
                        "Accept-Language": "en-US",
                        "User-Agent": IG_API_USER_AGENT,
                        "Content-Type": IG_API_CONTENT_TYPE,
                        "X-IG-Capabilities": "3brTvw==",
                        "X-IG-Connection-Type": "WIFI"
                }, cookies={
                        "sessionid": self.session_id
                }, data=self.claim_data)

                if ("feedback_required" in response.text):
                        self.spam_blocked = True
                        self.running = False

                return "\"status\": \"ok\"" in response.text

class Turbo(Thread):
        def __init__(self, instagram):
                super(Turbo, self).__init__()
                self.instagram = instagram

        def run(self):
                while (self.instagram.running):
                        try:
                                if (self.instagram.target_available()):
                                        if (self.instagram.claim_target()):
                                                self.instagram.claimed = True
                                        else:
                                                self.instagram.missed_swap = True

                                        self.instagram.running = False

                                self.instagram.attempts += 1
                        except:
                                continue


                        

def random_id(length):
        return "".join(random.choice(string.digits) for _ in range(length))

class RequestsPS(Thread):
        def __init__(self, instagram):
                super(RequestsPS, self).__init__()
                self.instagram = instagram

        def run(self):
                while self.instagram.running:
                        before = self.instagram.attempts
                        sleep(1) # Sleep 1 second, calc difference
                        self.instagram.rs = self.instagram.attempts - before



def get_input(prompt, mask=False):
        ret_str = b""
        print(prompt, end="", flush=True)

        while (True):
                ch = readchar.readchar()

                if (os.name == "posix"):
                        ch = str.encode(ch)

                code_point = ord(ch)

                if (code_point == BREAK): # Ctrl-C
                        if (os.name == "posix"):
                                print("\r\n", end="", flush=True)

                        exit(0)
                elif (code_point == LINE_FEED): # Linefeed
                        break
                elif (code_point == BACK_SPACE): # Backspace
                        if (len(ret_str) > 0):
                                ret_str = ret_str[:-1]
                                print("\b \b", end="", flush=True)
                else:
                        ret_str += ch
                        print("*" if mask else ch.decode("utf-8"), end="", flush=True)

        print("\r\n", end="", flush=True)
        return ret_str.decode("utf-8")

def on_exit(instagram):
        if (instagram.logged_in):
                if (instagram.logout()):
                        print("{} Successfully logged out".format(SUCCESS))
                else:
                        print("{} Failed to logout :/".format(ERROR))


#INIT MAIN
with open(os.getcwd() + '\\pool.txt', 'r') as fd:
    accountpool = fd.read().splitlines()

    
def main():
        init() # Use Colorama to make Termcolor work on Windows too
        print("{} {}Dan's GodSwap | V1.1\r\n".format(SUCCESS, WHITE))
        ctypes.windll.kernel32.SetConsoleTitleW("GodSwap")
        print("\n{} {}loaded {}{}{} sessions...".format(SUCCESS, WHITE, BLUE, len(accountpool), WHITE))
        print("\n{} {}banned targeting {}disabled{}".format(SUCCESS, WHITE, RED, WHITE))
        threads = get_input("\r\n{} Threads: ".format(INPUT)).strip()
        target = get_input("{} Target: ".format(INPUT)).strip().lower()
        input("press enter to start...")
        loopcount = True
        while loopcount:
                try:
                        for account in accountpool:
                                instagram = Instagram()
                                instagram.target = target
                                
                                if ":" not in account:
                                        continue
                                else:
                                        sleep(.1)
                                username = account.split(":")[0]#get_input("{} Username: ".format(INPUT)).strip()
                                password = account.split(":")[1]#get_input("{} Password: ".format(INPUT), True)

                                #print("\r\n{} Attempting to login...".format(INFO))

                                if (not instagram.login(username, password)):
                                        print("{} Failed to login to @{} - Check your password/account".format(ERROR, username))
                                        continue

                                instagram.target_id = instagram.get_target_id()
                                instagram.build_claim_data()
                                
                                if (not instagram.target_id):
                                        print("{} Failed to get user ID for target".format(ERROR))
                                        input("")
                                print("\x1b[A                                      \x1b[A")

                                for i in range(int(threads)):
                                        thread = Turbo(instagram)
                                        thread.setDaemon(True)
                                        thread.start()
                                rs_thread = RequestsPS(instagram)
                                rs_thread.setDaemon(True)
                                rs_thread.start()


                                while (instagram.running):
                                        try:
                                                for spinner in ["|", "/", "-", "\\", "|", "/", "-", "\\"]:
                                                        print("[\x1b[35m{}\x1b[39m] Turboing - {:,} attempts - {:,} r/s".format(spinner, instagram.attempts, instagram.rs), end="\r", flush=True)
                                                        ctypes.windll.kernel32.SetConsoleTitleW("Xiety / Target: @{} / Session: {}".format(instagram.target, username))
                                                        sleep(0.1) # Update attempts every 100ms
                                        except KeyboardInterrupt:
                                                print("\r{} Turbo stopped, exiting after {:,} attempts...\r\n".format(ERROR, instagram.attempts))
                                                break
                                        
                                if (instagram.spam_blocked):
                                        print("\r{} Tried to claim @{} but account is spam blocked ({:,} attempts)\r\n".format(ERROR, instagram.target, instagram.attempts))
                                        continue
                                elif (instagram.rate_limited):
                                        print("\r{} Rate limited after {:,} attempts\r\n".format(ERROR, instagram.attempts))
                                        continue
                                elif (instagram.missed_swap):
                                        print("\r{} Missed username swap on @{} after {:,} attempts\r\n".format(ERROR, instagram.target, instagram.attempts))
                                        input("\npress enter to close your window....")
                                        os._exit(0)
                                elif (instagram.claimed):
                                        print("\r{} updated username to {}@{}{}\n {}{:,}{} attempts\r\n".format(SUCCESS, GREEN, instagram.target, WHITE, BLUE, instagram.attempts, WHITE))
                                        input("\npress enter to close your window....")
                                        os._exit(0)
                                                                
                except Exception as e:
                        print("error:")
                        print(e)
                        input("\n press enter to exit..")
                        os._exit(0)
                        
if (__name__ == "__main__"):
        main()
