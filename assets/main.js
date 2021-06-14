dynamicallyLoadScript("https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js");
var bCBlind=false;
var iCBlind;
var bFreeze=false;

const graphsCookieName = "selectedGraphs";
let selectedGraphs = [];

var iInit=setInterval(init,50);

function init(){
	if(!window.jQuery){
		console.log("jQuery not loaded yet");
	}else if(getGraphs().length==0){
		console.log("No graphs loaded yet");
	}else{
		clearInterval(iInit);
		addSidebar();
	}
}

let loading = setInterval(toggleLoading, 50);

function toggleLoading() {

	var aGraph=$('div[id*="live-graph"]');

	if(aGraph.length > 0)
	{
		// get the first chart and look for a child node.
		var parent = aGraph[0];
		var hasChild = parent.children.length > 0;
		// get the loading div
		if(hasChild)
		{
			var elem = $('#loader')[0];
			if(elem.style.display=="block") {
				elem.style.display="none";
				clearInterval(loading);
			}
		}
	}
}


function dynamicallyLoadScript(url) {
	var script = document.createElement("script"); // Make a script DOM node
	script.src = url; // Set it's src to the provided URL
	document.head.appendChild(script); // Add it to the end of the head section of the page (could change 'head' to 'body' to add it to the end of the body section instead)
}
function freeze(){
	if(bFreeze){
		location.reload();
	}else{
		var k = setTimeout(function() {
				bFreeze = true;
				$('button#bFreeze').eq(0).text("Unfreeze");
				for (var i = k; i > 0; i--){ clearInterval(i)}
				if(bCBlind){iCBlind=setInterval(colorblindInt,100);}
			},1);
	}
}
function tColorBlind(){
	if(bCBlind){
		bCBlind=false;
		$('button#ColorblindTrigger').eq(0).text("Activate Colorblind");
		clearInterval(iCBlind);
	}else{
		bCBlind=true;
		$('button#ColorblindTrigger').eq(0).text("Deactivate Colorblind");
		iCBlind=setInterval(colorblindInt,100);
	}
}
function colorblindInt(){
	$('path').each(colorblind);
}
function colorblind(i,ob){
	var e=$(this);
	var fill=e.css('fill');
	if(fill!="none"){
		var rgb=fill.split('(')[1].split(")")[0].replace(/ /g,"").split(",");
		if(parseInt(rgb[1])>0){
			var help= rgb[2];
			rgb[2]=rgb[1];
			rgb[1]= help;
			rgb="rgb("+rgb[0]+","+rgb[1]+","+rgb[2]+")";
			e.css('fill',rgb);
		}
	}
  var stroke=e.css('stroke');
	if(stroke!="none"){
		var rgb=stroke.split('(')[1].split(")")[0].replace(/ /g,"").split(",");
		if(parseInt(rgb[1])>0){
			var help= rgb[2];
			rgb[2]=rgb[1];
			rgb[1]= help;
			rgb="rgb("+rgb[0]+","+rgb[1]+","+rgb[2]+")";
			e.css('stroke',rgb);
		}
	}
}

function addSidebar(){
	$('body').append('<div id="sidebarCon" ></div>');
	$('div#sidebarCon').eq(0).append('<header><h2>Theme</h2> <form id="theme-switcher"> <div> <input type="radio" id="light" name="theme" value="light"> <label for="light">Light</label> </div> <div> <input type="radio" id="dark" name="theme" value="dark"> <label for="dark">Dark</label> </div> <div> <input type="radio" id="dim" name="theme" value="dim"> <label for="dim">Dim</label> </div> </form> </header></br></br>');
	$('div#sidebarCon').eq(0).append('<div id="sidebar">');
	$('div#sidebarCon').eq(0).append('<div id="pairlist" class="checkboxes">');

	var sideB= $('div#sidebar').eq(0);
	var pairsList = $('div#pairlist').eq(0);

	var cStyle = $('div#react-entry-point').eq(0).attr('style');
	if(cStyle==undefined){cStyle="";}
	cStyle += "position:relative;margin: 0 0 0 151px";
	$('div#react-entry-point').eq(0).attr('style',cStyle);
	cStyle = $('body').eq(0).attr('style');
	if(cStyle==undefined){cStyle="";}
	cStyle += "font-family: Arial";
	$('body').eq(0).attr('style',cStyle);
	sideB.append('<button id="bFreeze" onclick="freeze()">Toggle Freeze</button><br><br>');
	sideB.append('<button id="ColorblindTrigger" onclick="tColorBlind()">Activate Colorblind</button><br><br>');
	sideB.append('<p id="showHeader"><h2>Show/Hide Graphs:</h2></p><br>');

	var aPairs = getGraphs();
	var count =0;
	
	for (var i=0;i<aPairs.length;i++) {

		var checked = "";

		// get graph cookie
		var currentGraphsRaw = getCookie(graphsCookieName) !== null ? decodeURIComponent(getCookie(graphsCookieName)) : null;

		// check base on if the selected pairs are saved in the cookie
		if(currentGraphsRaw !== null) {

			var currentGraphs =  currentGraphsRaw.split(',');
			
			selectedGraphs = currentGraphs;

			if (currentGraphs.length > 0) {
	
				checked = currentGraphs.filter(item => item === aPairs[i]).length > 0 ? "checked" : "";
		
			}
			else {
				selectedGraphs.push(aPairs[i]);
				checked = "checked";
				count++;
			}
		}
		else {
			selectedGraphs.push(aPairs[i]);
			checked = "checked";
			count++;
		}
		
		// need to check if array contains any cookies and check the boxes if it does.
		var sElem='<input type="checkbox" ' + checked + ' id="cShow'+aPairs[i]+'"  onchange="toggleGraph(\''+aPairs[i]+'\')"><label>'
		sElem += aPairs[i] + '</label></input><br>'
		pairsList.append(sElem);
	}

	var checkSelectAll = "";
	checkSelectAll = selectedGraphs.length == aPairs.length ? "checked" :"";
	pairsList.prepend('<input type="checkbox" ' + checkSelectAll + ' id="cSelectAll"  onchange="selectAll(this)"><label>Select All</lable></input><br>');
	selectedGraphs.length === 0 ? deleteCookie(graphsCookieName) : ()=> { setCookie(graphsCookieName, selectedGraphs, 365);  };
}

function toggleGraph(pName){
	var elem = $('[id*="'+pName+'"')[0];
	
	// hide and show.
	if(elem.style.display=="none") {
		elem.style.display="block"
	}
	else {
		elem.style.display="none"
	}

	cookieHandler(pName);
	//checkSelectAll();
}

function checkSelectAll() {
	var element = document.getElementById('cSelectAll');
	var totalchartCount = getGraphs().length;

	var checkSelectAll = "";
	checkSelectAll = selectedGraphs.length == totalchartCount ? element.checked = true : element.checked = fase;

}
function getGraphs(){
	var aGraph=$('div[id*="live-graph"]');
	let aPairs= [];
	for( var i=0;i<aGraph.length;i++){
		aPairs.push(aGraph[i].id.split("live-graph-")[1]);
	}
	return aPairs;
}

function cookieHandler(pName) {
	var isChecked = document.querySelector('input[id="cShow'+ pName +'"]').checked;

	if (!selectedGraphs.includes(pName) && isChecked === true) {
		// add to selected Graphs
		selectedGraphs.push(pName);
	}
	else if (selectedGraphs.includes(pName) && isChecked === false) {
		selectedGraphs = selectedGraphs.filter(item => item !== pName);
	}
	
	selectedGraphs.length === 0 ? deleteCookie(graphsCookieName) : setCookie(graphsCookieName, selectedGraphs, 365);
}

function selectAll(source) {
	
	var checkboxes = document.querySelectorAll('input[type="checkbox"]');
    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i] != source){
            checkboxes[i].checked = source.checked;
			cookieHandler(checkboxes[i].id.substring(5, checkboxes[i].length));
			toggleGraph(checkboxes[i].id.substring(5, checkboxes[i].length));
		}
    }

}