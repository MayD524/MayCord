from difflib import SequenceMatcher
from roomsec import roomSecurity
from datetime import datetime
from pprint import pprint
import hashlib ## hashPassword
import base64
import zlib
import uuid
import json
import time

"""
Password hashing:
    - salt = password + time + username[i] (looped)
    - password_hash = salt + password + time + username[i] (looped)
    (make it nearly impossible to unhash the password)

TODO:
    Encrpyt the database
"""

class serverDataBase:
    def __init__(self,  db_file:str, 
                        initDB:bool=False) -> None:
        self.db_file = db_file
        self.initDB  = initDB
        self.userNameToUUID:dict = {}
        self.dbCache:dict = {}
        self.deletedMessages:dict[str, list[str]] = {}
        self.roomsec = roomSecurity(fillWith="♥")
        if initDB: self.init_db(); return
        self.readFile()
    
    def init_db(self) -> None:
        self.makeTable("users")
        self.makeTable("messages")
        self.makeTable("rooms")
        self.makeUser("admin", "admin", "admin@email.com", "localhost")
        self.createRoom("general", "admin")
        self.writeFile()

    def propigateDataBaseUpdates(self) -> None:
        for user in self.dbCache["users"].keys():
            if "rooms" not in self.dbCache["users"][user].keys():
                self.dbCache["users"][user]["rooms"] = ["general"]
                self.joinRoom("general", user)
        self.writeFile()

    def makeTable(self, table:str) -> None:
        if not self.tableExists(table):
            self.dbCache[table] = {}

    def getInRange(self, roomName:str, rng:int) -> list[dict]:
        roomName = roomName if roomName else "general"
        if not self.roomExists(roomName): print(f"Room {roomName} not found."); return
        if rng > len(self.dbCache["messages"][roomName]): rng = 0
        else: rng = len(self.dbCache["messages"][roomName]) - rng
        
        ## get range of messages in list
        return self.dbCache["messages"][roomName][rng:]

    def deleteKey(self, table:str, key:str) -> None:
        if self.tableExists(table) and self.keyExists(table, key):
            del self.dbCache[table][key]
            
        self.writeFile()
    
    def deleteRoom(self, roomName:str, userUUID:str) -> bool:
        if not self.roomExists(roomName): return False
        user = self.getUsernameFromUUID(userUUID)
        if not self.isOwner(roomName, user): return False
        if roomName == "general": return False
        if roomName in self.dbCache["rooms"]:
            for user in self.dbCache["rooms"][roomName]["members"]:
                self.userLeaveRoom(user, roomName)
                
            del self.dbCache["rooms"][roomName]
            del self.dbCache["messages"][roomName]
            return True
    
    def tableExists(self, table:str) -> bool:
        return table in self.dbCache.keys()
    
    def keyExists(self, table:str, key:str) -> bool:
        return key in self.dbCache[table].keys()
    
    def get(self, table:str, key:str) -> dict[str]:
        return self.dbCache[table][key].copy() if self.keyExists(table, key) else {}
    
    def add(self, table:str, key:str, data:dict[str]) -> None:
        self.dbCache[table][key] = data

    def writeFile(self) -> None:
        with open(self.db_file, "w") as f:
            f.write(base64.b64encode(zlib.compress(json.dumps(self.dbCache).encode("utf-8"))).decode("utf-8"))

    def readFile(self) -> None:
        with open(self.db_file, "r") as reader:
            file_zlib = zlib.decompress(base64.b64decode(reader.read().encode("utf-8"))).decode("utf-8")
            self.dbCache = json.loads(file_zlib)
            
            for user in self.dbCache["users"]:
                self.userNameToUUID[self.dbCache["users"][user]["uuid"]] = user

    def display(self) -> None:
        pprint(self.dbCache)
        return
    
    def userExists(self, username:str) -> bool:
        return self.keyExists("users", username) or username in self.userNameToUUID.keys()
    
    def userLogin(self, username:str, password:str, uip:str, userAgent:str) -> bool:
        if not self.userExists(username): return False
        if self.dbCache["users"][username]["logged-in"]: return False
        ## get the password hash from db
        correctPassword: bool = self.dbCache["users"][username]["password"] == self.hashPassword(username, password)
        if correctPassword:
            self.dbCache["users"][username]["last-login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.dbCache["users"][username]["logged-in"] = True
            self.dbCache["users"][username]["last-uip"] = uip
            self.dbCache["users"][username]["last-user-agent"] = userAgent
        return correctPassword

    def userLoginWithUUID(self, username, uuid:str, uip:str, userAgent:str) -> bool:
        if not self.userExists(username): return False
        if self.dbCache["users"][username]["logged-in"]: return False

        if self.userUUIDMatch(username, uuid):
            self.dbCache["users"][username]["last-login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.dbCache["users"][username]["logged-in"] = True
            self.dbCache["users"][username]["last-uip"] = uip
            self.dbCache["users"][username]["last-user-agent"] = userAgent
            return True
        return False

    def promoteUser(self, roomName:str, user:str, author:str) -> bool:
        if not self.roomExists(roomName): return False
        if not self.userExists(user): return False
        if not self.userExists(author): return False
        if not self.isOwner(roomName, author): return False
        if not self.isMember(roomName, user): return False
        
        if user in self.dbCache["rooms"][roomName]["moderators"]:
            self.dbCache["rooms"][roomName]["moderators"].remove(user)
        else:
            self.dbCache["rooms"][roomName]["moderators"].append(user)
            
        return True
    
    def getUserUUID(self, user:str) -> str:
        return self.dbCache["users"][user]["uuid"] if self.keyExists("users", user) else False
    
    def userUUIDMatch(self, user:str, uuid:str) -> bool:
        return self.getUserUUID(user) == uuid
    
    def roomExists(self, roomName:str) -> bool:
        if roomName == None: return False
        return roomName in self.dbCache["rooms"].keys()
    
    def roomSettings(self, roomName:str) -> dict[str]:
        if not self.roomExists(roomName): return {}
        return self.dbCache["rooms"][roomName]["settings"]
    
    def getRoomSettings(self, roomName:str) -> dict[str]:
        if not self.roomExists(roomName): return {}
        ## check if user is a moderator
        rooms:dict[str] = self.dbCache["rooms"][roomName].copy()
        rooms.pop("members", None)
        return rooms
    
    def createRoom(self, roomName:str, owner:str) -> bool:
        if self.roomExists(roomName): return False
        
        self.dbCache["rooms"][roomName] = {
            "owner": owner, 
            "moderators": [owner],
            "members": [owner], 
            "time-created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            "uuid": str(uuid.uuid4()),
            "profanity-filter": False,
            "banned-words": [],
            "banned-users": [],
            "allow-links": True,
            "allow-images": True,
            "allow-anon-messages": True
        }
        self.dbCache["messages"][roomName] = []
        self.dbCache["users"][owner]["rooms"].append(roomName)
        self.writeFile()
        return True
    
    def isModerator(self, roomName:str, username:str) -> bool:
        if not self.roomExists(roomName): return False
        if not self.userExists(username): return False
        return self.dbCache["rooms"][roomName]["moderators"].count(username) > 0
        
    def isMember(self, roomName:str, username:str) -> bool:
        if not self.roomExists(roomName): return False
        if not self.userExists(username): return False
        return self.dbCache["rooms"][roomName]["members"].count(username) > 0
        
    def isOwner(self, roomname:str, username:str) -> bool:
        if not self.roomExists(roomname): return False
        if not self.userExists(username): return False
        return self.dbCache["rooms"][roomname]["owner"] == username
    
    def addModerator(self, roomName:str, owner:str, newMod:str) -> bool:
        if not self.isOwner(roomName, owner): return False
        if not self.userExists(newMod): return False
        if self.isModerator(roomName, newMod): return False
        
        self.dbCache["rooms"][roomName]["moderators"].append(newMod)
        return True

    def userLeaveRoom(self, username:str, room:str) -> bool:
        if not self.roomExists(room): return 
        if username not in self.dbCache["rooms"][room]["members"]: return False
        
        if username == self.dbCache["rooms"][room]["owner"]:
            self.dbCache["rooms"][room]["owner"] = self.dbCache["rooms"][room]["moderators"][0]
        
        self.dbCache["rooms"][room]["members"].remove(username)
        if username in self.dbCache["rooms"][room]["moderators"]:
            self.dbCache["rooms"][room]["moderators"].remove(username)
        self.dbCache["users"][username]["rooms"].remove(room)
        self.writeFile()
        return True
    
    def getUsernameFromUUID(self, uuid:str) -> str:
        return self.userNameToUUID[uuid] if uuid in self.userNameToUUID.keys() else False
    
    def userInRoom(self, username:str, roomname:str) -> bool: 
        return True if username in self.dbCache["rooms"][roomname]["members"] else False
    
    def joinRoom(self, room:str, username:str) -> bool:
        if not self.roomExists(room): return False
        if username in self.dbCache["rooms"][room]["members"]: return False
        if room in self.dbCache["users"][username]["rooms"]: return False

        self.dbCache["rooms"][room]["members"].append(username)
        self.dbCache["users"][username]["rooms"].append(room)
        self.writeFile()
        return True

    def getUsers(self, room:str) -> list[str]:
        if not self.roomExists(room): return []        
        return [self.dbCache["users"][user]["uuid"] if not self.dbCache["users"][user]["display-username"] else user 
                for user in self.dbCache["rooms"][room]["members"]]
        
    def getUserRooms(self, username:str) -> list[str]:
        return self.dbCache["users"][username]["rooms"] if self.keyExists("users", username) else []
    
    def deleteUser(self, username:str, currentUserUUID:str) -> bool:
        if not self.userExists(username): return False
        if not self.userUUIDMatch(username, currentUserUUID): return False
        if username == "admin": return False
        userRooms = self.getUserRooms(username)
        for room in userRooms:
            self.userLeaveRoom(username, room)
        del self.dbCache["users"][username]
        self.writeFile()
    
    def deleteMessage(self, message:str, author_uuid:str, roomName:str) -> bool:
        if not self.roomExists(roomName): return False
        for i, message_uuid in enumerate(self.dbCache["messages"][roomName]):
            
            if self.dbCache["messages"][roomName][i]["uuid"] == message and (self.dbCache["messages"][roomName][i]["author-uuid"] == author_uuid or self.getUsernameFromUUID(author_uuid) in self.dbCache["rooms"][roomName]["moderators"]):
                del self.dbCache["messages"][roomName][i]
                if roomName in self.deletedMessages:
                    self.deletedMessages[roomName].append(message)
                else:
                    self.deletedMessages[roomName] = [message]
                self.writeFile()
                return True
            
        return False

    def emailExists(self, email:str) -> bool:
        ## check if email is in db
        for user in self.dbCache["users"].keys():
            if self.dbCache["users"][user]["email"] == email: return True
        return False
    
    def userLogout(self, username:str) -> bool:
        if not self.userExists(username): return False
        if not self.dbCache["users"][username]["logged-in"]: return True ## dont need to logout if not logged in
        self.dbCache["users"][username]["logged-in"] = False
        self.dbCache["users"][username]["last-logout"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return True
    
    def makeUser(self, username:str, password:str, email:str, uip:str, userAgent:str) -> bool:
        if self.keyExists("users", username): return False 
        password = self.hashPassword(username, password, True)
        username = self.roomsec.censor(username)[0]

        self.add("users", username, {"password":password, 
                                    "email": email, 
                                    "time-created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                    "uuid": str(uuid.uuid4()), 
                                    "display-username": True, 
                                    "rooms" : ["general"], 
                                    "currentRoom": "general",
                                    "last-seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "last-logout": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "last-uip": uip,
                                    "last-user-agent": userAgent,
                                    "logged-in": True,
                                    "remember-me": False,
                                    })
        if username == "admin": return False
        self.dbCache["rooms"]["general"]["members"].append(username)
        self.writeFile()
        return True
        
    def getAccountCreationTime(self, username:str) -> str:
        return self.get("users", username)["time-created"] if self.keyExists("users", username) else ""
    
    def addImageChat(self, username:str, imageData:bytes, roomName:str) -> None:
        if not self.roomExists(roomName): return

        if not username in self.dbCache["rooms"][roomName]["members"]: return False
        msgUUID = str(uuid.uuid4())
        msg = {
            "message" : imageData.decode("utf-8"),
            "author-uuid" : self.getUserUUID(username),
            "time-created" : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user" : username if self.dbCache["users"][username]["display-username"] else self.getUserUUID(username),
            "uuid" : msgUUID,
            "room" : roomName,
            "type" : "image"
        }
            
        self.dbCache["messages"][roomName].append(msg)
        self.writeFile()

    def serverAllowsProfanity(self, roomName:str) -> bool:
        if not self.roomExists(roomName): return False
        return self.dbCache["rooms"][roomName]["profanity-filter"]
        
    def getMessage(self, roomName:str, messageUUID:str) -> bool:
        if not self.roomExists(roomName): return False
        for message in self.dbCache["messages"][roomName]:
            if message["uuid"] == messageUUID:
                return message
        return False
    
    def addChat(self, username:str, message:str, roomName:str) -> dict:
        if not self.userExists(username): return False
        chatUUID = str(uuid.uuid4())
        if not self.serverAllowsProfanity(roomName):
            message = self.roomsec.censorMessage(message)[0]

        if not self.dbCache["rooms"][roomName]["members"].contains(username): return False

        self.dbCache["users"][username]["currentRoom"] = roomName

        msg = { "message": message, 
                "room": roomName,
                "time-created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                "author-uuid": self.getUserUUID(username), ## send the user uuid anyways (for tracking)
                "uuid": chatUUID,
                "type": "text"
                }
        
        ## check if the user rathers uuid displayed than username
        msg["user"] = username if self.dbCache["users"][username]["display-username"] else self.getUserUUID(username)
        
        self.dbCache["messages"][roomName].append(msg)
        return msg

    """
        <USER CUSTOMIZATION>
        user customizations
    """
    def setUserName(self, oldUserName:str, newUserName:str) -> bool:
        ## user must exists and new username must not be taken
        if (not self.userExists(oldUserName) or self.userExists(newUserName)): return False
        
        ## update the user name in the database
        userDataCopy = self.dbCache["users"][oldUserName].copy()
        # remove the old user
        self.dbCache["users"].pop(oldUserName)
        self.dbCache["users"][newUserName] = userDataCopy
        
        ## update the user name in the rooms
        for room in self.dbCache["users"][newUserName]["rooms"]:
            self.dbCache["rooms"][room]["members"].append(newUserName)
            self.dbCache["rooms"][room]["members"].remove(oldUserName)
            
            if self.dbCache["rooms"][room]["owner"] == oldUserName:
                self.dbCache["rooms"][room]["owner"] = newUserName
            
            if oldUserName in self.dbCache["rooms"][room]["moderators"]:
                self.dbCache["rooms"][room]["moderators"].remove(oldUserName)
                self.dbCache["rooms"][room]["moderators"].append(newUserName)
        
        return True

    def invertUseName(self, username:str) -> bool:
        if (not self.userExists(username)): return False
        
        self.dbCache["users"][username]["display-username"] = not self.dbCache["users"][username]["display-username"]
        return True
    
    def userIsLoggedIn(self, username:str) -> bool:
        if not self.userExists(username): return False
        return self.dbCache["users"][username]["logged-in"]
    
    def kickUser(self, username: str, roomName:str) -> bool:
        if (not self.userExists(username) or not self.roomExists(roomName)): return False
        
        if username in self.dbCache["rooms"][roomName]["members"]:
            self.dbCache["rooms"][roomName]["members"].remove(username)
            for message in self.dbCache["messages"][roomName]:
                if message["author-uuid"] == self.getUserUUID(username):
                    self.dbCache["messages"][roomName].remove(message)
            return True
    
    def banUser(self, username: str, roomName:str) -> bool:
        if not self.kickUser(username, roomName): return False
        self.dbCache["rooms"][roomName]["banned-users"].append(username)
        return True
    
    def unbanUser(self, username: str, roomName:str) -> bool:
        if not self.roomExists(roomName): return False
        if username in self.dbCache["rooms"][roomName]["banned-users"]:
            self.dbCache["rooms"][roomName]["banned-users"].remove(username)
            return True
    
    def setSettings(self, username:str, settings:str, roomName:str) -> bool:
        if not self.userExists(username): return False
        if not self.roomExists(roomName): return False
        if not self.isModerator(roomName, username): return False

        settings = list(settings)
        self.dbCache["rooms"][roomName]["profanity-filter"] = settings[0] == "1"
        self.dbCache["rooms"][roomName]["allow-images"] = settings[1] == "1"
        self.dbCache["rooms"][roomName]["allow-links"] = settings[2] == "1"
        self.dbCache["rooms"][roomName]["allow-anon-messages"] = settings[3] == "1"
        return True
    
    """ 
        <SECURITY>
        Password hash
    """
    ## password & security
    def hashPassword(self, username:str, password:str, newUser:bool=False) -> str:
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if newUser else self.getAccountCreationTime(username)
        salt = hashlib.sha224(password.encode() + time.encode() + username.encode()).hexdigest()
        for char in username:
            salt = hashlib.sha224(salt.encode() + char.encode()).hexdigest()
            
        pwdHash = hashlib.sha256(salt.encode() + password.encode() + time.encode() + username.encode()).hexdigest()
        for char in username:
            pwdHash = hashlib.sha256(pwdHash.encode() + char.encode()).hexdigest()
        
        return hashlib.sha512(salt.encode() + pwdHash.encode() + time.encode() + username.encode()).hexdigest()
    
    
    @staticmethod
    def checkSimularity(string1:str, string2:str, tooSimilar:float=0.56) -> bool:
        if len(string1) != len(string2): return False
        elif string1 == string2: return True
        else: return SequenceMatcher(None, string1, string2).ratio() > tooSimilar

    """
        <SERVER CTRL>
        Some general server control functions
    """
    def updateThread(self, delay:int ) -> None:
        while True:
            time.sleep(delay)
            self.writeFile()