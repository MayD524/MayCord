let setCookies = (cookies: any): void => {
    // loop through all cookie keys
    for (let key in cookies) {
        // set the cookie
        document.cookie = key + "=" + cookies[key];
    }
};

let hideLoginPopup = () => {
    let loginPopup = document.getElementById("login-popup");
    
    if (loginPopup === null) { 
        console.error("Could not find login popup");
        alert("Could not find login popup: hideLoginPopup failed");
        return; 
    }
    (<HTMLInputElement>document.getElementById("username")).value = "";
    (<HTMLInputElement>document.getElementById("password")).value = "";

    loginPopup.style.display = "none";
};

let openRegisterPopup = () => {
    hideLoginPopup();
    let loginPopup = document.getElementById("register-popup");
    if (loginPopup === null) { return; }
    loginPopup.style.display = "block";
};

let hideRegisterPopup = () => {
    let registerPopup = document.getElementById("register-popup");
    if (registerPopup === null) { return; }
    // set fields to empty
    (<HTMLInputElement>document.getElementById("rusername")).value = "";
    (<HTMLInputElement>document.getElementById("rpassword")).value = "";
    (<HTMLInputElement>document.getElementById("remail")).value = "";
    registerPopup.style.display = "none";
};

let openLoginPopup = () => {
    hideRegisterPopup();
    let loginPopup = document.getElementById("login-popup");
    if (loginPopup === null) { return; }
    loginPopup.style.display = "block";
};