from http.server import SimpleHTTPRequestHandler, HTTPServer
from http.cookies import CookieError, SimpleCookie
from database.db_handler import serverDataBase
from socketserver import ThreadingMixIn
from datetime import datetime
from urllib import parse
import logging
import pprint
import json
import os

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class httpServer(SimpleHTTPRequestHandler):
    def set_headers(self, code:int=200, dType:str="text/html", cookies:SimpleCookie=None) -> None:
        self.send_response(code)
        self.send_header("Content-type", dType)
        if cookies:
            for morsel in cookies.values():
                self.send_header("Set-Cookie", morsel.OutputString())
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, content-type")
        self.end_headers()
        
    def cookieJarHandler(self) -> dict[str,str]:
        try:
            cookies    = SimpleCookie(self.headers.get("Cookie"))
            outCookies = {}
            
            for cookie in cookies.values():
                cookie = cookie.OutputString().split("=")
                outCookies[cookie[0]] = cookie[1]
            
            return outCookies
        except CookieError as e:
            logging.error("CookieJarHandler Error: " + str(e))
            return {}
            
    def do_OPTIONS(self):
        self.set_headers(200)
        
    def ERROR(self, error:str="Unknown Error") -> None:
        self.set_headers(500)
        self.wfile.write(bytes(error, "utf-8"))
        
    def do_GET(self):
        ## check cookies
        cookies = self.cookieJarHandler()
        logging.info(f"GET request,\nPath: {self.path},\nHeaders: {str(self.headers)}\nCookies: {str(cookies)}")
        print(self.path)
        self.path = parse.unquote_plus(self.path)
        if self.path == "/":
            ## TODO: Try to remove this
            if "userUUID" in cookies and "username" in cookies:
                ## check the userUUID in the cookies
                if dbHandler.userExists(cookies["username"]) and dbHandler.userUUIDMatch(cookies["username"], cookies["userUUID"]):
                    uip = self.client_address[0]
                    userAgent = self.headers.get("User-Agent") if "User-Agent" in self.headers else "Unknown"
                    if userAgent == "Unknown":
                        self.ERROR("<h1>Unknown User-Agent</h1>")
                    dbHandler.userLoginWithUUID(cookies["username"], cookies["userUUID"], uip, userAgent)
                    self.send_loginPage(cookies["username"])
                    return
                
            if not os.path.isfile("../html/index.html"): self.ERROR("<h1>index.html not found</h1>"); return
            html = self.readHtmlFile("../html/index.html")
            self.set_headers(200)
            self.wfile.write(bytes(html, "utf-8"))
            
        elif self.path.startswith("/dist/"):
            if not os.path.isfile(f"..{self.path}"): self.ERROR(f"<h1>{self.path} not found</h1>"); return
            self.set_headers(200, "application/javascript")
            with open("../dist/main.js", "rb") as reader:
                self.wfile.write(reader.read())
                
        elif self.path.startswith("/css/"):
            if not os.path.isfile(f"../html{self.path}"): self.ERROR("<h1>css file not found</h1>"); return
            self.set_headers(200, "text/css")
            with open(f"../html{self.path}", "rb") as reader:
                self.wfile.write(reader.read())
    
        elif self.path.startswith("/images/"):
            if not os.path.isfile(f"../html{self.path}"): self.ERROR("<h1>image file not found</h1>"); return
            self.set_headers(200, "image/jpg")
            with open(f"../html{self.path}", "rb") as reader:
                self.wfile.write(reader.read())
                
        elif self.path == "/contact":
            self.set_headers(200, "text/html")
            
        elif self.path == "/favicon.ico":
            self.set_headers(200, "image/x-icon")
            with open("./favicon.ico", "rb") as reader:
                self.wfile.write(reader.read())
                
        elif self.path.startswith("/lts_msgs?"):
            ## get messages from db
            if not cookies["username"] in dbHandler.dbCache["rooms"][cookies["currentRoom"]]["members"]: self.ERROR("User is not in room") ;return
            roomName, dbEnd = self.path.split("?")[1].split("&")
            msgs = dbHandler.getInRange(roomName, int(dbEnd))

            ## send messages
            self.set_headers(200, "text/json")
            self.wfile.write(json.dumps(msgs).encode("utf-8"))
        
        elif self.path.startswith("/users?"):
            roomName = self.path.split("?")[1]
            users = dbHandler.getUsers(roomName)
            if not users: self.ERROR("<h1>Room does not exist</h1>"); return
            self.set_headers(200, "text/json")
            self.wfile.write(json.dumps(users).encode("utf-8"))
        
        elif self.path.startswith("/userRooms"):
            ## get rooms from db
            rooms = dbHandler.getUserRooms(cookies["username"])

            ## send rooms
            self.set_headers(200, "text/json")
            self.wfile.write(json.dumps(rooms).encode("utf-8"))
            
        elif self.path == "/deletedMessages":
            msgs = dbHandler.deletedMessages[cookies["currentRoom"]] if cookies["currentRoom"] in dbHandler.deletedMessages else ["NO-DEAD-MESSAGES"]
            
            self.set_headers(200, "text/json")
            self.wfile.write(json.dumps(msgs).encode("utf-8"))
            
        elif self.path.startswith("/roomSettings?"):
            roomName = self.path.split("?")[1]
            data = dbHandler.getRoomSettings(roomName)
            self.set_headers(200, "text/json")
            self.wfile.write(json.dumps(data).encode("utf-8"))
            
        else:
            self.ERROR("<h1>404 not found</h1>")
    
    def send_loginPage(self, username:str, newLogin:bool=False) -> None:
        print(f"{username} is logged in")
        html = self.readHtmlFile("../html/loginindex.html")
        
        html = html.replace(
            "%CURRENT_USER%", username).replace(
                "%DISPLAY_USERNAME%", str(dbHandler.dbCache["users"][username]["display-username"])
            ).replace("%USER_UUID%", str(dbHandler.dbCache["users"][username]["uuid"])
            ).replace("%USER_EMAIL%", dbHandler.dbCache["users"][username]["email"]
            ).replace("%LAST_LOGIN%", dbHandler.dbCache["users"][username]["last-seen"])
        
        self.set_headers(200, "text/html", cookies=SimpleCookie({"userUUID": dbHandler.getUserUUID(username), "username": username}))
        self.wfile.write(bytes(html, "utf-8"))
    
    def do_DELETE(self) -> None:
        cookies = self.cookieJarHandler()
        print(self.path)
        logging.info(f"DELETE request,\nPath: {self.path},\nHeaders: {str(self.headers)}\nCookies: {str(cookies)}")
        
        if "?" in self.path:
            self.path, query = self.path.split("?")
            query = query.split("&")
            query = {i.split("=")[0]: i.split("=")[1] for i in query}
            if self.path == "/delete":
                if "user" in query:
                    if not dbHandler.deleteUser(query["user"], cookies["userUUID"]): self.ERROR(f"<h1>{query['user']} could not be deleted</h1>"); return
                    self.set_headers(200)
                    self.wfile.write(bytes(f"deleted {query['user']}", "utf-8"))
                
                ##  TODO: Remove message from users (as it happens)
                elif "message" in query:
                    if not dbHandler.deleteMessage(query["message"], cookies["userUUID"], query["room"]): self.ERROR(f"<h1>{query['message']} could not be deleted</h1>"); return
                    self.set_headers(200)
                    self.wfile.write(bytes(f"deleted {query['message']}", "utf-8"))
                
                elif "room" in query:
                    if not dbHandler.deleteRoom(query["room"], cookies["userUUID"]): self.ERROR(f"<h1>{query['room']} could not be deleted</h1>"); return
                    self.set_headers(200)
                
            elif self.path == "/leave-room":
                if not dbHandler.userLeaveRoom(cookies["username"], query["room"]): self.ERROR(f"<h1>{query['room']} could not be left</h1>"); return
                self.set_headers(200)
                
            elif self.path == "/kick-user":
                uname = dbHandler.getUsernameFromUUID(query["user"])
                if dbHandler.isModerator(cookies["currentRoom"], uname): self.ERROR("<h1>You can't kick a moderator</h1>"); return
                if not dbHandler.isModerator(cookies["currentRoom"], cookies["username"]): self.ERROR("<h1>>You can't kick as a user</h1>"); return
                if not dbHandler.kickUser(query["user"], cookies["currentRoom"]): self.ERROR(f"<h1>{query['user']} could not be kicked</h1>"); return
            
            elif self.path == "/ban-user":
                uname = dbHandler.getUsernameFromUUID(query["user"])
                if dbHandler.isModerator(cookies["currentRoom"], uname): self.ERROR("You can't ban a moderator"); return
                if not dbHandler.isModerator(cookies["currentRoom"], cookies["username"]): self.ERROR("You can't ban as a user"); return
                if not dbHandler.banUser(query["user"], cookies["currentRoom"]): self.ERROR(f"<h1>{query['user']} could not be banned</h1>"); return
                
    def do_PUT(self) -> None:
        cookies = self.cookieJarHandler()
        pprint.pprint(cookies)
        put_data = self.rfile.read(int(self.headers.get("Content-Length"))).decode("utf-8")
        put_data = parse.unquote_plus(put_data)
        logging.info("PUT request,\nPath: " + self.path + ",\nHeaders: " + str(self.headers) + ",\nData: " + put_data)
        print(self.path)
        print(put_data)
        args = {}
        if (len(put_data) > 0):
            args = put_data.split("&")
            args = {args.split("=")[0]: args.split("=")[1] for args in args}
        
        elif "?" in self.path:
            self.path, data = self.path.split("?")
            args = data.split("&")
            args = {arg.split("=")[0]: arg.split("=")[1] for arg in args}
        
        if self.path == "/" and "username" in cookies and "userUUID" in cookies:
            if dbHandler.userExists(cookies["username"]) and dbHandler.userUUIDMatch(cookies["username"], cookies["userUUID"]):
                self.send_loginPage(cookies["username"])
                
        if self.path == "/set-useName":
            if not dbHandler.invertUseName(cookies["username"]): self.ERROR("<h1>Username doesn't exist</h1>"); return
            self.set_headers(200)
            
        elif self.path == "/report-message":
            msg_id = args["message"]
            msg_data = dbHandler.getMessage(cookies["currentRoom"], msg_id)
            if not msg_data: self.ERROR("<h1> Message does not exists</h1>"); return
            with open("./database/reports.logs", "a+") as writer:
                writer.writelines(f"[REPORT] <{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}> {cookies['username']} reported message {msg_id} in room {msg_data['room']} -> {msg_data['message']}\n")
            self.set_headers(200)
            
        elif self.path == "/logout":
            if not dbHandler.userLogout(cookies["username"]): self.ERROR("<h1>Logout failed</h1>"); return
            self.set_headers(200)
            
        elif self.path == "/set-username":
            if not dbHandler.setUserName(cookies["username"], args["username"]): self.ERROR("<h1>Username already taken</h1>"); return
            cookies["username"] = args["username"]
            self.set_headers(200, cookies=SimpleCookie(cookies))
            
        elif self.path == "/set-moderator":
            if not dbHandler.promoteUser(cookies["currentRoom"], args["username"], cookies["username"]): self.ERROR("<h1>PromoteUser failed</h>"); return
            self.set_headers(200)
            
        elif self.path == "/set-settings":
            if not dbHandler.setSettings(cookies["username"], args["settings"], cookies["currentRoom"]): self.ERROR("<h1>Settings failed</h>"); return
            self.set_headers(200)
            
    def do_POST(self):
        cookies = self.cookieJarHandler()
        print(self.path)
        post_data = self.rfile.read(int(self.headers["Content-Length"]))
        if self.path != "/chat-image":
            post_data = parse.unquote_plus(post_data.decode('utf-8'))
        # print the first 100 characters of the post data
        print(post_data[:100])
        logging.info(f"POST request,\nPath: {self.path},\nHeaders: {str(self.headers)}\nData: {post_data}")
        if self.path == "/" and "username" in cookies and "userUUID" in cookies:
            if dbHandler.userExists(cookies["username"]) and dbHandler.userUUIDMatch(cookies["username"], cookies["userUUID"]):
                self.send_loginPage(cookies["username"])

        ## make a dict from args split by '='
        if isinstance(post_data, bytes) or  ":" not in post_data or self.path == "/chat-image":
            args = {}
            if not isinstance(post_data, bytes):
                args = post_data.split("&")
                args = {arg.split("=")[0]:arg.split("=",1)[1] for arg in args}
            #print(args)
            if self.path == "/create":
                if (not dbHandler.userExists(cookies["username"]) or not dbHandler.userUUIDMatch(cookies["username"], cookies["userUUID"])):
                    self.ERROR("<h1>You are not logged in</h1>"); return
                if not args["owner"] == cookies["username"]: self.ERROR("<h1>You are not the owner of this room</h1>"); return
                if not args["name"]: self.ERROR("<h1> no room name </h1>"); return
                if not dbHandler.createRoom(args["name"], cookies["username"]): self.ERROR(f"<h1> Room {args['name']} already exists or is invalid</h1>"); return
                self.set_headers(200, "text/html")
                self.wfile.write(bytes("<h1>Room created</h1>", "utf-8"))

            elif self.path == "/reset-password":
                if (not dbHandler.userExists(cookies["username"]) or not dbHandler.userUUIDMatch(cookies["username"], cookies["userUUID"])):
                    self.ERROR("<h1>You are not logged in</h1>"); return
                
                old_password = args["old_password"]
                new_password = args["new_password"]
                if not dbHandler.hashPassword(cookies["username"], old_password) == dbHandler.dbCache["users"][cookies["username"]]["password"]:
                    self.ERROR("<h1>Wrong password</h1>"); return
                
                dbHandler.dbCache["users"][cookies["username"]]["password"] = dbHandler.hashPassword(cookies["username"], new_password)
                self.set_headers(200)
                self.wfile.write(b'Password reset!')

            elif self.path == "/join":
                if (not dbHandler.userExists(cookies["username"]) or not dbHandler.userUUIDMatch(cookies["username"], cookies["userUUID"])):
                    self.ERROR("<h1>You are not logged in</h1>"); return
                if not args["roomID"]: self.ERROR("<h1> no room name </h1>"); return
                if not dbHandler.roomExists(args["roomID"]): self.ERROR("<h1>Room does not exist</h1>"); return
                dbHandler.joinRoom(args["roomID"], cookies["username"])
                cookies["currentRoom"] = args["roomID"]
                self.set_headers(200, "text/html")
                self.wfile.write(bytes("<h1>Joined room</h1>", "utf-8"))
                
            elif self.path == "/chat":
                if (not dbHandler.userExists(cookies["username"]) or not dbHandler.userUUIDMatch(cookies["username"], cookies["userUUID"])):
                    self.ERROR("<h1>You are not logged in</h1>"); return
                if not args["message"]: self.ERROR("<h1> no message </h1>"); return
                dbHandler.addChat(cookies["username"], args["message"], cookies["currentRoom"])
                self.set_headers(200, "text/html")
                self.wfile.write(bytes("<h1>Message sent</h1>", "utf-8"))
            
            elif self.path == "/chat-image":
                if (not dbHandler.userExists(cookies["username"]) or not dbHandler.userUUIDMatch(cookies["username"], cookies["userUUID"])):
                    self.ERROR("<h1>You are not logged in</h1>"); return
                dbHandler.addImageChat(cookies["username"], post_data, cookies["currentRoom"])
                self.set_headers(200, "text/html")
                self.wfile.write(bytes("<h1>Message sent</h1>", "utf-8"))
                
            return
        
        cmd, args = post_data.split(":")
        args = args.split("&")
        args = {arg.split("=")[0]:''.join(arg.split("=")[1:]) for arg in args}
        if cmd == "new-user":
            if not args["username"]: self.ERROR("<h1>Username not found</h1>"); return
            if not args["password"]: self.ERROR("<h1>Password not found</h1>"); return
            if not args["email"]:    self.ERROR("<h1>Email not found</h1>"); return
            if dbHandler.userExists(args["username"]): self.ERROR("<h1>User already exists</h1>"); return
            dbHandler.makeUser(args["username"], args["password"], args["email"], self.client_address[0], userAgent=self.headers["User-Agent"])
            self.send_loginPage(args["username"], True)
            
        elif cmd == "login":
            if not args["username"]: self.ERROR("<h1>Username not found</h1>"); return
            if not args["password"]: self.ERROR("<h1>Password not found</h1>"); return
            if not dbHandler.userExists(args["username"]): self.ERROR("<h1>User does not exist</h1>"); return
            login = dbHandler.userLogin(args["username"], args["password"], self.client_address[0], userAgent=self.headers["User-Agent"])
            if not login: self.ERROR("<h1>Wrong password</h1>"); return
            self.send_loginPage(args["username"], True)
        
        ## keep this for legacy reasons (for now)
        elif cmd == "new-chat":
            if (not dbHandler.userExists(cookies["username"]) or not dbHandler.userUUIDMatch(cookies["username"], cookies["userUUID"])):
                self.ERROR("<h1>You are not logged in</h1>"); return
            if not args["message"]: self.ERROR("<h1> no message </h1>"); return
            dbHandler.addChat(cookies["username"], args["message"], cookies["currentRoom"])
            self.set_headers(200, "text/html")
                
    @staticmethod 
    def readHtmlFile(filename:str) -> str:
        with open(filename, "r") as reader:
            html = reader.read()
            
        for key in config.keys():
            if f"%{key.upper()}%" in html and not key.upper().startswith("R"):
                html = html.replace(f"%{key.upper()}%", config[key])
                
        return html

def run_server(host:str="localhost", port:int=8080) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename="server.log", filemode="w+")
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, httpServer)
    ## start the chat server
    try:
        print(f"Starting server on {host}:{port}")
        logging.log(logging.INFO, f"Starting server on {host}:{port}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    
    logging.log(logging.INFO, f"Stopping server on {host}:{port}")
    print("\nShutting down server...")
    httpd.server_close()
    
    dbHandler.writeFile()
    print('Server stopped.')


if __name__ == "__main__":
    sqlQueue:list[str]   = []
    config:dict[str,str] = {}
    requestHandler:int   = 0
    with open("./config/config.conf", 'r') as reader:
        tmp = reader.readlines()
        for line in tmp:
            if line == "\n" or line == "": continue
            config[line.split("=")[0]] = line.split("=")[1].strip()
    dbHandler = serverDataBase(config["r-dbFile"], config['r-initDB'] == "True")
    dbHandler.display()
    if (bool(config['r-initDB'])):
        config["r-initDB"] = "False"
    run_server()
    ## log out all users
    for user in dbHandler.dbCache["users"].keys():
        dbHandler.userLogout(user)
    dbHandler.writeFile()
    with open("./config/config.conf", 'w') as writer:
        for key in config.keys():
            writer.write(f"{key}={config[key]}\n")