# Chat1Min
from flask import Flask, request, send_file, redirect
import hashlib, json, threading, time, os
import LeCatchu

users = {}
sessions = {}
online = []
chats = {}
lc = LeCatchu.LeCatchu_Engine(encoding=False, special_exchange="Chat1MinApp")
lckey = lc.decode_direct(os.urandom(128))

dbfile = "users_db.json.lc"
lckeyfile = "lckey.txt"
lock = threading.Lock()

def save():
    global users, dbfile, lckey, lc
    with open(dbfile, "wb") as f:
        f.write(lc.encrypt_with_iv(lc.encode_direct(json.dumps(users, indent=1, default=repr)), lckey))

def load():
    global users, dbfile, lckey, lc
    try:
        with open(dbfile, "rb") as f:
            with lock:
                users = json.loads(lc.decode_direct(lc.decrypt_with_iv(f.read(), lckey)))
    except Exception as e:
        print("Error on loading users data:", e)

def get_lckey():
    global lckeyfile, lckey, lc
    if os.path.exists(lckeyfile):
        with open(lckeyfile, "rb") as f:
            with lock:
                lckey = lc.decode_direct(lc.decrypt_with_iv(f.read(), "Chat1Min"))
    else:
        with open(lckeyfile, "wb") as f:
            f.write(lc.encrypt_with_iv(lc.encode_direct(lckey), "Chat1Min"))

get_lckey()
load()

class User:
    def __init__(self):
        self.username = None
    def hashs(self, target):
        target = target.encode("utf-8", errors="ignore")
        [target:=hashlib.sha256(target).digest() for _ in range((int(hashlib.sha256(target).hexdigest(), 16)%128)+16)]
        return target.hex()
    def sign_up(self, username, password, logs):
        global users
        if username in users:
            return "Account already exists.", 400
        else:
            username = str(username);password = str(password);logs = dict(logs)
            username_allowed = "qwertyuopasdfghjklizxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890._"
            for h in username:
                if h not in username_allowed:
                    return "Special characters are not allowed in username.", 400
            if len(username) < 6:
                return "Username cannot be shorter than 6 characters.", 400
            elif len(username) > 20:
                return "Username cannot be longer than 20 characters.", 400
            if len(password) < 8:
                return "Password must be longer than 8 characters.", 400
            for h in password:
                if ord(h) > 1024:
                    return "Some special characters are not allowed in password", 400
            password = self.hashs(password[:1024])
            with lock:
                users[username] = {"password": password, "logs": logs, "created": time.time(), "chat": None}
            self.username = username
            return "Successfuly.", 200
    def chat_name(self, name1, name2):
        if int(hashlib.sha256(name1.encode()).hexdigest(), 16) >= int(hashlib.sha256(name2.encode()).hexdigest(), 16):
            return hashlib.sha256((name1+","+name2).encode()).hexdigest()
        else:
            return hashlib.sha256((name2+","+name1).encode()).hexdigest()
    def check_pwd(self, username, password):
        global users
        return users[username]["password"]==password
    def log_in(self, username, password):
        global users, sessions
        if username in users:
            password = self.hashs(password)
            if self.check_pwd(username, password):
                cid = self.hashs(str(time.time()))
                with lock:
                    sessions[(cid, request.remote_addr)] = [username, password, time.time()]
                self.username = username
                return cid, 200
            else:
                return "Password is invalid.", 400
        else:
            return "Account not found.", 400
    def online(self):
        global online
        for name, _ in online:
            if name == self.username:
                return
        with lock:
            online.append((self.username, time.time()))
    def find_target(self):
        global online, chats, users
        for name, last in list(online):
            if time.time()-last <= 4:
                if name != self.username:
                    chat = self.chat_name(name, self.username)
                    with lock:
                        online.remove((name, last))
                        chats[chat] = {"last": time.time(), "box": []}
                        users[self.username]["chat"] = chat
                        users[name]["chat"] = chat
                    return chat, 0
            else:
                with lock:
                    online.remove((name, last))
        return None, None
    def check_target(self):
        global chats, users
        for chat, data in list(chats.items()):
            if time.time()-data["last"] >= 60:
                with lock:
                    del chats[chat]
        if users[self.username]["chat"] in chats:
            return users[self.username]["chat"], chats[users[self.username]["chat"]]["last"]
        return self.find_target()
    def send_message(self, content):
        global chats
        target, _ = self.check_target()
        if target:
            if len(content) > 0:
                with lock:
                    chats[target]["box"].append([self.username, content[:4096], int(time.time())])
                return "Successfuly.", 200
            else:
                return "Message content not found.", 400
        else:
            return "Chat room not found.", 400
    def load_messages(self):
        global chats
        target, _ = self.check_target()
        if target:
            return json.dumps(chats[target]["box"]), 200
        else:
            return "Chat room not found.", 400

app = Flask(__name__)

@app.route("/api/sign_up", methods=["POST"])
def sign_up_api():
    data = request.get_json()
    c = User()
    out = c.sign_up(data["username"], data["password"], {"headers": dict(request.headers), "environ": dict(request.environ)})
    save()
    return out

@app.route("/api/log_in", methods=["POST"])
def log_in_api():
    data = request.get_json()
    c = User()
    out = c.log_in(data["username"], data["password"])
    return out

def get_user():
    global sessions
    cid = (request.cookies.get("cid", ""), request.remote_addr)
    if cid in sessions:
        username, password, last = sessions[cid]
        if time.time()-last <= 60*60:
            c = User()
            if c.check_pwd(username, password):
                c.username = username
                return c
        else:
            with lock:
                del sessions[cid]

@app.route("/api/check_target", methods=["POST"])
def check_target_api():
    c = get_user()
    if c:
        ex, last = c.check_target()
        if ex:
            return json.dumps({"matched": True, "elapsed": int(time.time()-last)}), 200
        else:
            return json.dumps({"matched": False}), 200
    else:
        return "Unauthorized", 401

@app.route("/api/send_message", methods=["POST"])
def send_message_api():
    c = get_user()
    if c:
        return c.send_message(request.get_json()["content"])
    else:
        return "Unauthorized", 401

@app.route("/api/load_messages", methods=["POST"])
def load_messages_api():
    c = get_user()
    if c:
        return c.load_messages()
    else:
        return "Unauthorized", 401

@app.route("/")
def main_path():
    if get_user():
        return redirect("/loading")
    return send_file("index.html", mimetype="text/html")

@app.route("/get_account")
def get_account_path():
    return send_file("get_account.html", mimetype="text/html")

@app.route("/loading")
def loading_path():
    global chats
    time.sleep(1) # extra waiting
    c = get_user()
    if not c:
        return redirect("/")
    c.online()
    return send_file("loading.html", mimetype="text/html")

@app.route("/quit_account")
def quit_account_process_path():
    global sessions
    cid = (request.cookies.get("cid", ""), request.remote_addr)
    if cid in sessions:
        del sessions[cid]
    return redirect("/")

@app.route("/chat")
def chat_path():
    global chats
    c = get_user()
    if not c:
        return redirect("/")
    return open("chat.html", "r", encoding="utf-8").read().replace("$UserName", c.username)

@app.route("/quitchat")
def quitchat_process_path():
    global chats, online
    time.sleep(1) # extra waiting
    c = get_user()
    if not c:
        return redirect("/")
    chat = c.check_target()[0]
    if chat in chats:
        with lock:
            del chats[chat]
    for user, last in list(online):
        if user == c.username:
            with lock:
                del online[(user, last)]
    return redirect("/loading")

@app.route("/favicon.ico")
def favicon_file():
    return send_file("favicon.ico", mimetype="image/icon")

@app.route("/logo.png")
def logo_file():
    return send_file("logo.png", mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True)
