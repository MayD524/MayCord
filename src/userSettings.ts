/* 
    User Options:
        - enable/disable showing username
        - enable/disable showing user avatar
        - status
*/

class userSettings {
    useDarkMode: boolean = false;
    // make a dictionary of settings
    settings: { [key: string]: any } = { 
        showUsername: true,
        showAvatar: true,
        status: "online",
        darkMode: false
    };


    constructor() {
        if (document.cookie.includes("settings=")) {
            this.getSettings();
        } else {
            this.setSettings();
        }
    }

    getSettings() {
        // get cookies
        let cookieSettings = document.cookie.split("settings=")[1].split(";");

        for (let i = 0; i < cookieSettings.length; i++) {
            if (!cookieSettings[i].includes("=")) { continue; }
            let tmpl = cookieSettings[i].split("=");
            this.settings[tmpl[0]] = tmpl[1];

        }
    }

    setSettings() {
        // set cookies
        let cookieSettings = "";
        for (let key in this.settings) {
            cookieSettings += key + "=" + this.settings[key] + ";";
        }
        document.cookie = "settings=" + cookieSettings;
    }

    invertUseName() {
        // send a post request to the server
        this.settings.showUsername = !this.settings.showUsername;
        this.setSettings();
        $.ajax({
            url: "/set-useName",
            type: "PUT",
            success: (data: any) => {
                console.log(data);
            }, 
            error: (err: any) => {
                alert("Something went wrong :/");
                console.error(err);
            }
        });
    }

    setUsername() {
        // get the username
        let username = (document.getElementById("username-input") as HTMLInputElement)!.value;
        if (username === null) { return; }
        if (username === "") { return; }

        console.log("Setting username to: " + username);

        // send a post request to the server
        $.ajax({
            url: "/set-username?username="+username,
            type: "PUT",
            success: (data: any) => {
                let uNav = document.getElementById("username-nav")!;
                let uNameSettings = document.getElementById("username-settings")!;
                uNav.innerHTML = username;
                uNameSettings.innerHTML = username;
                // set the username in the cookie
                document.cookie = "username=" + username;
            }, 
            error: (err: any) => {
                alert("Something went wrong :/");
                console.error(err);
            }
        });

    }
}
let cUserSettings = new userSettings();

let setDefaultSettings = () => {
    let cbUsername = document.getElementById("checkbox-username") as HTMLInputElement;
    cbUsername.value = cUserSettings.settings.showUsername;
};