let messageUUIDs  :string[] = [];
let userRooms     :string[] = ["general"];
let userList      :string[] = [];
let users         :string[] = [];
let firstLoad     :boolean  = true;
let chatMsgCount  :number   = 0;
let firstGetCnt   :number   = 10;
let getCnt        :number   = 10;
let maxStore      :number   = firstGetCnt * 2;
let timeIncrease  :number   = 1;
let currentRoom   :string   = "general";
let useDarkMode   :string   = "darkMode"; // set to "" for no and "darkMode" for yes
let getIntervalID :number;
let roomOpts      :any;

let isURL = (str: string) : boolean => {
    console.log(typeof str);
    return str.startsWith("http://") || 
        str.startsWith("https://") || 
        str.startsWith("www.") || 
        str.endsWith(".com") || 
        str.endsWith(".org") || 
        str.endsWith(".net") || 
        str.endsWith(".edu");
};

let getRoomUsers = () : void => {
    $.ajax({
        url: "/users?" + currentRoom,
        type: "GET",
        success: (data: string[]) => {
            console.log(data);
            let userList = document.getElementById("user-list");
            if (userList === null) { 
                console.error("Could not find user list");
                return; 
            }
            userList.innerHTML = "";
            users = data;
            data.sort(); // sort the users alphabetically
            for (let i = 0; i < data.length; i++) {
                let user = document.createElement("li");
                user.className = "user-list-item";
                user.innerHTML = data[i];
                userList.appendChild(user);
            }
        },
        error: (err: any) => {
            console.error(err);
            //console.error(err);
        }
    });
};

let setCurrentRoom = (room: string) : void => {
    // add the room name to cookie
    currentRoom = room;
    document.cookie = "currentRoom=" + room;
    // get the chat messages
    chatMsgCount = 0;
    clearChats();
    getRoomUsers();
    getChatMessage(firstGetCnt);
    getRoomOptions(room, true);

    // set the title 
    document.title = `May-Cord ${room} | Chat`;

    let homeTitle = document.getElementById("chat-welcome");
    if (homeTitle === null) { return; }
    homeTitle.innerHTML = `Welcome to ${room} ${username()}!`;
};

let playBeep = () => {
    var audio = new Audio("/images/beep.wav");
    audio.play();
};

let messageParse = (message: string) : string => {
    // split the message into words
    // if message has a " "
    // loop through the words
    if (message.includes(" ")) {
        let words = message.split(" ");
        for (let i = 0; i < words.length; i++) {
            // check if the word is a url
            if (isURL(words[i])) {
                // redirect the user to the url
                // add https if it is not there
                if (!words[i].startsWith("http")) { words[i] = "https://" + words[i]; }
                words[i] = `<a href="${words[i]}" target="_blank" rel="noopener noreferrer">${words[i]}</a>`;
            }
        }
        return words.join(" ");
    } else {
        if (isURL(message)) {
            // redirect the user to the url
            // add https if it is not there
            if (!message.startsWith("http") || !message.startsWith("https")) { message = "https://" + message; }
            message = `<a href="${message}" target="_blank" rel="noopener noreferrer">${message}</a>`;
        }
        return message;
    }
};

let messageOptionPopup = (messageUUID: string, author: string):void => {
    let isModerator = roomOpts.moderators.includes(username());
    let oldPopup = document.getElementById("message-option-popup");
    // remove the popup if it already exists
    if (oldPopup !== null) {
        oldPopup.remove();
    }

    let msgObj = document.getElementById("message-" + messageUUID)!;
    let popup = document.createElement("div");
    popup.id = "message-option-popup";
    popup.innerHTML = `
        <div class="message-option-popup-item btn" onclick="copyMessage('${messageUUID}')">Copy</div>
        <div class="message-option-popup-item btn" onclick="reportMessage('${messageUUID}')">Report</div>
    `;
    if (author === username() || isModerator) {
        popup.innerHTML += `
            <div class="message-option-popup-item btn" onclick="deleteMessage('${messageUUID}')">Delete</div>
        `;
    }

    // todo fix uuid 
    if (isModerator && author !== username()) {
        popup.innerHTML += `
            <div class="btn btn-danger" onclick="kickUser('${author}')">Kick</div>
            <div class="btn btn-danger" onclick="banUser('${author}')">Ban</div>
        `;
    }
    msgObj.appendChild(popup);
};

let getRoomOptions = (roomName: string, useRoomOpts:boolean = true): any => {
    $.ajax({
        url: "/roomSettings?" + roomName,
        type: "GET",
        success: (data: any) => {
            console.log(data);
            if (useRoomOpts) {
                roomOpts = data;
                return;
            }
            return data;
        }
    });
};

let closeGenPopup = () => {
    let popup = document.getElementById("general-popup")!;
    popup.innerHTML = "";
    popup.className = "popup";
    popup.style.display = "none";
    getRoomOptions(currentRoom, true);
}

let userPromote = (roomName: string, username: string) => {
    $.ajax({
        url: "/set-moderator",
        type: "PUT",
        data: {
            username : username
        },
        success: (data: any) => {
            console.log(data);
            getRoomOptions(roomName, true);
        },
        error: (err: any) => {
            alert("Could not promote user");
            console.error(err);
        }
    });
};

let updateModPage = (room: string) => {
    let popup = document.getElementById("general-popup")!;
    popup.classList.add("mod-popup");
    popup.innerHTML = "";

    let modPage = document.createElement("div");
    modPage.id = "mod-page";

    let btns = document.createElement("div");
    btns.id = "mod-btns";
    btns.innerHTML = `<div class="btn btn-primary" onclick="closeGenPopup()">Close</div>`;
    // loop through the users
    for (let i = 0; i < users.length; i++) {
        modPage.innerHTML += `
            <div class="toggle-wrapper">
                <input type="checkbox" id="user-${users[i]}" onclick="userPromote('${room}','${users[i]}')" ${roomOpts.moderators.includes(users[i]) ? "checked" : ""}>
                <label for="user-${users[i]}">${users[i]}</label>
            </div>
        `;
    }
    popup.appendChild(modPage);
    popup.appendChild(btns);
    popup.style.display = "block";
};

let roomOptionPopup = (room: string) : void => {
    let popup = document.getElementById("general-popup")!;
    
    let isModerator = roomOpts.moderators.includes(username());
    let isOwner = roomOpts.owner === username();
    
    popup.classList.add("mod-popup");
    // dynamically size the popup
    popup.style.width = window.innerWidth * 0.6 + "px";
    popup.style.height = window.innerHeight * 0.7 + "px";

    // center the popup
    popup.style.left = (window.innerWidth / 2) - (popup.offsetWidth / 2) + "px";
    popup.style.top = (window.innerHeight / 2) - (popup.offsetHeight / 2) + "px";
    
    popup.innerHTML = "";

    let generalInfo = document.createElement("div");
    generalInfo.className = "general-info";
    generalInfo.innerHTML = `
        <table class="table darkMode">
            <h3>${room}</h3>
            <tbody>
                <tr><td>Owner: ${roomOpts.owner}</td></tr>
                <tr><td>Moderators: ${roomOpts.moderators.join(", ")}</td></tr>
                <tr><td>Created: ${roomOpts["time-created"]}</td></tr>
                <tr><td>Room uuid: ${roomOpts.uuid}</td></tr>
            </tbody>
        </table>
    `;
    popup.appendChild(generalInfo);

    if (isModerator) {
        // add the moderator options
        let moderatorOptions = document.createElement("div");
        moderatorOptions.className = "moderator-options";
        moderatorOptions.innerHTML = `
            <div class="toggle-wrapper">
                <input class="toggle-settings" type="checkbox" name="toggle-prof" id="toggle-prof" ${roomOpts["profanity-filter"] ? "checked" : ""}>
                <label for="toggle-prof">Allow Profanity</label>
            </div>
            <div class="toggle-wrapper">
                <input class="toggle-settings" type="checkbox" name="toggle-anon" id="toggle-anon" ${roomOpts["allow-anon-messages"] ? "checked" : ""}>
                <label for="toggle-anon">Allow Anonymous</label>
            </div>
            <div class="toggle-wrapper">
                <input class="toggle-settings" type="checkbox" name="toggle-link" id="toggle-link" ${roomOpts["allow-links"] ? "checked" : ""}>
                <label for="toggle-link">Allow Links</label>
            </div>
            <div class="toggle-wrapper">
                <input class="toggle-settings" type="checkbox" name="toggle-images" id="toggle-images" ${roomOpts["allow-images"] ? "checked" : ""}>
                <label for="toggle-images">Allow Images</label>
            </div>
        `;
        popup.appendChild(moderatorOptions);
    }

    let userButtons = document.createElement("div");
    let dngBtns = document.createElement("div");
    let normalbtns = document.createElement("div");
    userButtons.className = "user-buttons";
    dngBtns.innerHTML = `
        <div class="btn btn-danger" onclick="leaveRoom('${room}')">Leave Room</div>
    `;
    normalbtns.innerHTML = "";

    /*
    TODO:
        - delete room
        - ban user
        - change room owner
        - save room settings
    */

    if (isOwner) {
        dngBtns.innerHTML += `
            <div class="btn btn-danger" onclick="deleteRoom('${room}')">Delete Room</div>
            <div class="btn btn-danger" onclick="changeRoomOwner('${room}')">Change Owner</div>
            <div class="btn btn-danger" onclick="renameRoom('${room}')">Rename Room</div>
        `;
        normalbtns.innerHTML += `
            <div class="btn btn-primary" onclick="updateModPage('${room}')">Moderators</div>
        `;
    }

    if (isModerator) {
        normalbtns.innerHTML += `
            <div class="btn btn-primary" onclick="saveRoomSettings('${room}')">Save</div>
        `;

    }

    normalbtns.innerHTML += `
        <div class="btn btn-primary" onclick="closeGenPopup()">Close</div>
    `;
    userButtons.appendChild(dngBtns);
    userButtons.appendChild(normalbtns);
    popup.appendChild(userButtons);
    popup.style.display = "block";
};

let addChatMessage = (sender: string, message: string, time: string, messageUUID: string, addTop: boolean = false, isImage: boolean = false) : void => {
    // check if message is an object
    if (typeof message === "object") {
        message = message[0];
    }
    
    let chat = document.getElementById("chat-body");
    let userIsMentioned = message.includes("@" + username()) || message.includes("@" + getCookie("userUUID"));
    if (chat === null) { 
        console.error("Could not find chat body");
        return; 
    }
    let chatMessage = document.createElement("div");
    message = messageParse(message);
    chatMessage.className = userIsMentioned ? "chat-msg chat-msg-mention" : "chat-msg";
    chatMessage.id = "message-" + messageUUID;
    chatMessage.innerHTML = `
        <span class="chat-msg-user">${sender}</span>
        <span class="chat-msg-time">: ${time}</span>
        <button class="chat-msg-option-button" onclick="messageOptionPopup('${messageUUID}', '${sender}')">&#9679&#9679&#9679</button>
        <br>
        `;
        if (!isImage) {
            chatMessage.innerHTML += `<span class="chat-msg-text">${message}</span>`;
        } else {
            // display the image (from raw data)
            chatMessage.innerHTML += `<img class="chat-msg-image" src="${message}"></img>`;
        }
    if (addTop) {
        chat.insertBefore(chatMessage, chat.firstChild);
    } else {
        chat.appendChild(chatMessage);
    }
};

let initializeChat = () => {
    let chat = document.getElementById("chat-body");
    if (chat === null) {
        console.error("Could not find chat body");
        return;
    }
    getChatMessage(firstGetCnt);
};

let renderRoomList = () => {
    console.log(userRooms);
    let roomList = document.getElementById("room-list");
    if (roomList === null) { return; }
    roomList.innerHTML = "";
    if (userRooms.length === 0) { 
        let listItem = document.createElement("div");
        listItem.className = "room-list-item";
        listItem.innerHTML = "No rooms available";
        return; 
    }
    for (let i = 0; i < userRooms.length; i++) {
        console.log(userRooms[i]);
        let room = userRooms[i];
        let listItem = document.createElement("div");
        listItem.className =  "room-list-item " + useDarkMode;
        listItem.innerHTML =  `<button class="room-list-item-button ${useDarkMode}" onclick="setCurrentRoom('${room}')">${room}</button>`;
        listItem.innerHTML += `<button class="room-option-btn darkMode" onclick="roomOptionPopup('${room}')">&#9679&#9679&#9679</button>`
        roomList.appendChild(listItem);
    }
};

let clearChats = () => {
    let chat = document.getElementById("chat-body");
    if (chat === null) { return; }
    chat.innerHTML = "";
    messageUUIDs = [];
};

let getUsersRooms = () : void => {
    $.ajax({
        url: "/userRooms",
        type: "GET",
        success: (data: any) => {
            console.log(data);
            userRooms = data;
        },
        error: (err: any) => {  
            console.error(err);
            //console.error(err);
        }
    });
    renderRoomList();
};

let removeChat = (messageUUID: string) : void => {
    let chat = document.getElementById("chat-body");
    if (chat === null) { return; }
    let chatMessage = document.getElementById("message-" + messageUUID);
    if (chatMessage === null) { return; }
    chat.removeChild(chatMessage);
};

let getDeletedMessages = () : void => {
    $.ajax ({
        url: "/deletedMessages",
        type: "GET",
        success: (data: any) => { 
            if (data[0] === "NO-DEAD-MESSAGES") { return; }
            for (let i = 0; i < data.length; i++) {
                removeChat(data[i]);
            }
        },
        error: (err: any) => {
            console.error(err);
        }
    });
};

let getChatMessage = (count: number, addTop:boolean = false) : void => {
    $.ajax({
        url: `/lts_msgs?${currentRoom}&${count}`,
        type: 'GET',
        success: (data) => {
            console.log(data);
            if (data.length === 0) { 
                timeIncrease += 0.4;
                getMessages(1 + timeIncrease);
                if (document.getElementById("chat-body")?.innerHTML === "") {
                    addChatMessage("Server", "No messages to display", "0", "NULL");
                }
                return; 
            }

            // loop through all messages
            for (let i = 0; i < data.length; i++) {
                
                if (messageUUIDs.indexOf(data[i].uuid) !== -1) { continue; }
                let msg = data[i];
                addChatMessage(msg.user, msg.message, msg["time-created"], msg.uuid ,addTop, msg.type === "image");
                messageUUIDs.push(msg.uuid);
                chatMsgCount++;
                // set the scroll to bottom
                let chat = document.getElementById("chat-body");
                if (chat === null) {  return; }
                // scroll to bottom (if addTop then go to 1 (fixes a bug))
                chat.scrollTop = addTop? 1 : chat.scrollHeight;
            }
        }
    });
};

let joinRoom = () => {
    // prompt the user for a room name
    let roomName = prompt("Enter a room id");
    if (roomName === null) { console.error("I think you missed something here..."); return; }

    // send a post request to join the room
    $.ajax({
        url: "/join",
        type: "POST",
        data: {
            roomID: roomName
        },
        success: (data: any) => {
            console.log(data);
            currentRoom = data.roomName;
            userRooms.push(data.roomName);
            window.location.href = "/";
            getUsersRooms();
        },
        error: (err: any) => {
            console.error(err);
        }
    });
    getUsersRooms();
};

let createRoom = () => {
    // prompt the user for a room name
    let roomName = prompt("Give your room a fancy name");
    if (roomName === null) { console.error("I think you missed something here..."); return; }

    // make a post request to create a room0
    $.ajax({
        url: "/create",
        type: "POST",
        data: {
            name: roomName,
            owner: username()
        },  
        success: (data: any) => {
            console.log(data);
            // update the room list
            userRooms.push(roomName ? roomName : "general");
            currentRoom = roomName ? roomName : "general";
            window.location.href = "/";
        },
        error: (err: any) => {
            console.error(err);
        }
    });
    getUsersRooms();

};

// get chat messages every second
let getMessages = (duration: number = 1) => {   
    let cnt = 0;
    if (getIntervalID !== null) {
        clearInterval(getIntervalID);
    }
    getIntervalID = setInterval(() => {
        try {
            // change this value if you want to see more messages
            getChatMessage(getCnt);
            getDeletedMessages();
            if (cnt == 0) {
                getUsersRooms();
                getRoomUsers();
                cnt++;
            } else if (cnt == 5) {
                cnt = 0;
            }
            
        } catch (e) {
            console.error(e);
            getMessages(25); // if we error delay by 25 seconds
        }
    }, 1000 * duration);
};

// get username from cookie 
let getCookie = (name: string) : string => {
    let cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.startsWith(name + "=")) {
            return cookie.substring(name.length + 1);
        }
    }
    return "";
};

let username = () : string => {
    return getCookie("username");
};

let userLoggedIn = () : boolean => {
    return username() !== "";
};

let sendImage = () : void => {
    let input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*";
    input.onchange = (e: any) => {
        let file = e.target.files[0];
        let reader = new FileReader();
        reader.onload = (e: any) => {
            let data = e.target.result;
            $.ajax({
                url : "/chat-image",
                type: "POST",
                data: data,
                success: (data: any) => {
                    console.log(data);
                },
                error: (err: any) => {
                    console.error(err);
                }
            });
        };
        reader.readAsDataURL(file);

    };
    input.click();
};

let sendMessage = (message: string) : void => {
    $.ajax({
        url: "/chat",
        type: "POST",
        data: {
            message: message,
            room: currentRoom
        },
        success: (data: any) => {
            console.log(data);
            // get the lastest messages so we can render the users message
            getChatMessage(10); 
        },
        error: (err: any) => {
            console.log("sendMessage (something went wrong again :/)");
            console.error(err);
        }
    });
};

let clearChatInput = () : void => {
    let chatMessage = document.getElementById("chat-input-text-reworked");
    if (chatMessage === null) { return; }
    
    (<HTMLTextAreaElement>chatMessage).value = "";
};

let submitChatMessage = () : void => {
    // get the message
    let message = (<HTMLTextAreaElement>document.getElementById("chat-input-text-reworked"))?.value;
    if (message === null) { return; }
    if (message === "") { return; }

    // send the message
    sendMessage(message);

    // clear the input
    clearChatInput();
};

let updateNewChats = () => {
    // get the chat body
    let chat = document.getElementById("chat-body");
    if (chat === null) { return; }
    // scroll to bottom
    chat.scrollTop = chat.scrollHeight;

    // clear the chat input
    (<HTMLInputElement>document.getElementById("chat-input-text-reworked")).value = "";
};

if (userLoggedIn()) {
    // check if the enter key is pressed
    document.addEventListener("keydown", (e: KeyboardEvent) => {
        if (e.key === "Enter" && currentPage === 0) {
            submitChatMessage();
            // remove enter key from input
            e.preventDefault();
        }
    });
    setCurrentRoom("general");
}

// handle chat scrolling
let bindChatScrolling = () => {
    let scroller = document.querySelector("#chat-body")!;
    if (scroller === null) { return; }
    scroller.addEventListener("scroll", event => {
        if (currentPage !== 0) { return; }
        if (scroller.scrollTop === 0) {
            getChatMessage(10 + chatMsgCount, true);
        }
    });
};