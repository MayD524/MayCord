/*
    Author: May Draskovics
    Date  : 2022-02-03
*/

let currentPage = 0;

// home about and blog
let totalPages  = 3;
let updatePage = () : void  => {
    let homeData  = document.getElementById("home-data");
    let aboutData = document.getElementById("about-data");
    let blogData  = document.getElementById("blog-data");
    let uSettings = document.getElementById("user-settings");
    if (uSettings === null) {
        uSettings = document.createElement("div");
    }
    if (homeData  === null || 
        aboutData === null || 
        blogData  === null){
        console.error("Could not find data element(s)");
        return; 
    }
    switch (currentPage) {
        case 0: // chat / home page
            homeData.style.display = "block";
            aboutData.style.display = "none";
            blogData.style.display = "none";
            uSettings.style.display = "none";
            break;
        case 1: // about page
            homeData.style.display = "none";
            aboutData.style.display = "block";
            blogData.style.display = "none";
            uSettings.style.display = "none";
            break;
        case 2: // blog page
            homeData.style.display = "none";
            aboutData.style.display = "none";
            blogData.style.display = "block";
            uSettings.style.display = "none";
            break;
        case 3: // user settings
            homeData.style.display = "none";
            aboutData.style.display = "none";
            blogData.style.display = "none";
            uSettings.style.display = "block";
            break;
        default:
            homeData.style.display = "block";
            aboutData.style.display = "none";
            blogData.style.display = "none";
            uSettings.style.display = "none";
            break;
    }
};

let setCurrentPage = (page: number) : void => {
    if (page < 0) { page = 0; }
    currentPage = page;
    updatePage();
};

let getMessageData = (messageUUID: string) : string => {
    let message = document.getElementById("message-" + messageUUID)!;
    return message.getElementsByClassName("chat-msg-text")[0]!.innerHTML;
};

let kickUser = (userUUID: string) => { 
    $.ajax({
        url: "/kick-user?user=" + userUUID,
        type: "DELETE",
        success: (data: string) => {
            window.location.href = "/";
        },
        error: (err: any) => {
            console.error(err);
            alert("Could not kick user :: " + err.responseText);
        }
    });
};

let banUser = (userUUID: string) => {
    $.ajax({
        url: "/ban-user?user=" + userUUID,
        type: "DELETE",
        success: (data: string) => {
            window.location.href = "/";
        },
        error: (err: any) => {
            console.error(err);
            alert("Could not ban user :: " + err.responseText);
        }
    });
};

let deleteRoom = (roomUUID: string) => {
    let ask = confirm("Are you sure you want to delete this room?");
    if (!ask) { return; }
    $.ajax({
        url: "/delete?room=" + roomUUID,
        type: "DELETE",
        success: (data: string) => {
            window.location.href = "/";
        },
        error: (err: any) => {
            console.error(err);
            alert("Could not delete room :: " + err.responseText);
        }
    });
};

let saveRoomSettings = () : void => {
    let settings = document.getElementsByClassName("toggle-settings");
    let binSettings:string = ""
    for (let i = 0; i < settings.length; i++) {
        binSettings += (settings[i] as HTMLFormElement)!.checked ? "1" : "0";
    }
    $.ajax ({
        url : "/set-settings?settings=" + binSettings,
        type: "PUT",
        success: (data: string) => {
            alert("Settings saved");
        },
        error: (err: any) => {
            console.error(err);
            alert("Could not save settings :: " + err.responseText);
        }
    });
};


let userDelete = () => {
    let ask1 = confirm("Are you sure you want to delete your account?");
    if (!ask1) { return; }
    let ask2 = confirm("Are you sure you want to delete your account? This action cannot be undone.");
    if (!ask2) { return; }
    let ask3 = confirm("Are you really really really sure you want to delete your account?");
    if (!ask3) { return; }
    $.ajax({
        url: "/delete?user=" + username(),
        type: "DELETE",
        success: (data: string) => {
            document.cookie = "username=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            document.cookie = "userUUID=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            window.location.href = "/";
        },
        error: (err: any) => {
            console.error(err);
            alert("Could not delete user :: " + err.responseText);
        }
    });
};

let userLogout = (pageClose:boolean = false) : void => {
    // ask for confirmation
    let logout = confirm("Are you sure you want to logout?");
    if (!logout) {
        return;
    }

    $.ajax ({
        url: "/logout",
        type: "PUT",
        success: (data: string) => {
            // delete cookies username and userUUID
            document.cookie = "username=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            document.cookie = "userUUID=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            if (pageClose) { return; }
            // refresh the page without resubmitting the form
            window.location.href = "/";
        },
        error: (err: any) => {
            console.error(err);
            alert("Could not logout :: " + err.responseText);
        }
    });
};

let deleteMessage = (messageUUID: string) : void => {
    $.ajax({
        url: "/delete?message=" + messageUUID + "&room=" + currentRoom,
        type: "DELETE",
        success: (data: string) => {
            let message = document.getElementById("message-" + messageUUID)!;
            message.remove();
        },
        error: (err: any) => {
            console.error(err);
            alert("Could not delete message" + err);
        }
    });
};

let copyMessage = (messageUUID: string) : void => {
    let messageData = getMessageData(messageUUID);
    navigator.clipboard.writeText(messageData);
};

let reportMessage = (messageUUID: string) : void => {
    let popup = document.getElementById("general-popup")!;
    $.ajax({
        url: "/report-message",
        type: "PUT",
        data: {
            message: messageUUID,
            room: currentRoom
        },
        success: (data: string) => {
            popup.innerHTML = "<h2>Message reported!</h2><br><p>Thank you for reporting this message.</p>";
            popup.style.display = "block";
            // close popup after 5 seconds
            setTimeout(() => {
                popup.style.display = "none";
            }
            , 5000);
        }, 
        error: (err: any) => {
            popup.innerHTML = "<h2>Error</h2><br><p>Could not report message.</p>";
            popup.style.display = "block";
            // close popup after 5 seconds
            setTimeout(() => {
                popup.style.display = "none";
            }
            , 5000);
        }
    });
};

let leaveRoom = (room: string) => {
    $.ajax({
        url:"/leave-room?room=" + room,
        type: "DELETE",
        success: (data: string) => {
            window.location.href = "/";
        },
        error: (err: any) => {
            console.error(err);
            alert("Could not leave room :: " + err.responseText);
        }
    });
};

if (userLoggedIn()) {
    window.onclick = (event: MouseEvent) => {
        if (event.target !== document.getElementById("message-option-popup") && 
            event.target !== document.getElementById("message-option-popup-content") &&
            !(event.target as HTMLElement).classList.contains("chat-msg-option-button")) {
            let popup = document.getElementById("message-option-popup");
            popup?.remove(); // remove the popup if not null
        }
        else if (event.target !== document.getElementById("general-popup")) {
            closeGenPopup();
        }
    };
    // listener for tab closed
    window.onbeforeunload = () => {
        userLogout(true);
    };
}