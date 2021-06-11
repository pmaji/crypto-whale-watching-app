
// call this function every 250 ms untill the page is loaded.
let refreshID = setInterval(setupThemes, 250);

function setupThemes() {
    let switcher = document.querySelector('#theme-switcher')
	
    if(switcher && switcher.length > 0) {
		const doc = document.firstElementChild

		switcher.addEventListener('input', e =>
		setTheme(e.target.value))

		const setTheme = theme =>
		doc.setAttribute('color-scheme', theme);
        clearInterval(refreshID);
    }
}