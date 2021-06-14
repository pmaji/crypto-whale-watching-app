
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

