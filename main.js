console.log("Hello Whalewatcher");
dynamicallyLoadScript("https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js")
function dynamicallyLoadScript(url) {
    var script = document.createElement("script"); // Make a script DOM node
    script.src = url; // Set it's src to the provided URL
    document.head.appendChild(script); // Add it to the end of the head section of the page (could change 'head' to 'body' to add it to the end of the body section instead)
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
