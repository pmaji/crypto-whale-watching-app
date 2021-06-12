
// call this function every 50 ms untill the page is loaded.
let refreshID = setInterval(setupThemes, 50);
let cookieName ="selectedTheme";

function setupThemes() {
    let switcher = document.querySelector('#theme-switcher')
	
	let currentTheme = getCookie(cookieName);

    if(switcher && switcher.length > 0) {
		const doc = document.firstElementChild
		
		switcher.addEventListener('input', e =>
		setTheme(e.target.value))
		// document.getElementById("theme").checked = true;
		const setTheme = theme =>
		{
			doc.setAttribute('color-scheme', theme);
			setCookie(cookieName, theme, 365);
		
		}

		if (currentTheme !== undefined) {
			document.querySelector('input[name="theme"][value='+ currentTheme+']').checked = true;
			setTheme(currentTheme);
		}

		clearInterval(refreshID);
    }
}

function setCookie(c_name, value, exdays) {
    var exdate = new Date();
    exdate.setDate(exdate.getDate() + exdays);
    var c_value = escape(value) + ((exdays == null) ? "" : "; expires=" + exdate.toUTCString());
    document.cookie = c_name + "=" + c_value;
}

function getCookie(c_name) {
    var i, x, y, ARRcookies = document.cookie.split(";");
    for (i = 0; i < ARRcookies.length; i++) {
        x = ARRcookies[i].substr(0, ARRcookies[i].indexOf("="));
        y = ARRcookies[i].substr(ARRcookies[i].indexOf("=") + 1);
        x = x.replace(/^\s+|\s+$/g, "");
        if (x == c_name) {
            return unescape(y);
        }
    }
}