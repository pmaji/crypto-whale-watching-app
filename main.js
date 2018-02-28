console.log("Hello Whalewatcher");
dynamicallyLoadScript("https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js");
var bCBlind=false;
var iCBlind;
var bFreeze=false;

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
	$('body').append('<div id="sidebarCon" style="position:fixed;left:0;top:0;bottom:0;width:150px;height=100%; border-right-style: solid;"></div>');
	$('div#sidebarCon').eq(0).append('<div id="sidebar">');
	var sideB=$('div#sidebar').eq(0);
	var cStyle = $('div#react-entry-point').eq(0).attr('style');
	if(cStyle==undefined){cStyle="";}
	cStyle += "position:relative;margin: 0 0 0 151px";
	$('div#react-entry-point').eq(0).attr('style',cStyle);
	cStyle = $('body').eq(0).attr('style');
	if(cStyle==undefined){cStyle="";}
	cStyle += "font-family: Arial";
	$('body').eq(0).attr('style',cStyle);
	sideB.append('<button id="bFreeze" onclick="freeze()">Toggle Freeze</button><br><br>')
	sideB.append('<button id="ColorblindTrigger" onclick="tColorBlind()">Activate Colorblind</button><br><br>')
	sideB.append('<p id="showHeader">Show/Hide Graphs:</p>')
	var aPairs = getGraphs();
	for (var i=0;i<aPairs.length;i++){
		var sElem='<input type="checkbox" checked id="cShow'+aPairs[i]+'"  onchange="toggleGraph(\''+aPairs[i]+'\')">'
		sElem += aPairs[i] + '</input><br>'
		sideB.append(sElem)
	}
}
function toggleGraph(pName){
	var elem =$('[id*="'+pName+'"')[0]
	if(elem.style.display=="none"){elem.style.display="block"}
	else{elem.style.display="none"}
}
function getGraphs(){
	var aGraph=$('div[id*="live-graph"]');
	var aPairs=[];
	for( var i=0;i<aGraph.length;i++){
		aPairs.push(aGraph[i].id.split("live-graph-")[1]);
	}
	return aPairs;
}
