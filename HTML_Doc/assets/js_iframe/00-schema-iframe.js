// Quanos_ST4 2020
// type: COTS 
// license: MIT license

/* Version 2023 V1 */

//this nofifies the parent on iframe is ready
$(document).ready(function() {	
	
	enableSendingMessages();
	sendPageNavData();	
	sendPageTitle();
	loadFramesetIfChildpage();
});

//listen to message from parent and scrollst to the index marker requested
window.addEventListener("message", function (event) {		
	if (event.data.scrollToAnchor) {	
		const anchor = $("#" + event.data.scrollToAnchor.anchor);
		if(typeof anchor.offset() === "undefined"){
			return;
		}
		$("html,body").scrollTop(anchor.offset().top);
	}
});

//bind message sending to links to notify parent of clicks
function enableSendingMessages() {	
	$('a.schema-iframe-link').click(function (e) {		
		e.preventDefault();
		const nodeId = retrieveDataSetFieldIEWorkaround(e.currentTarget, "nodeId");		
		var anchorSplit = [];
		var url = window.location.href;
		var currentNodeId = url.split('/')[url.split('/').length - 1].split('.')[0];
		if(typeof e.currentTarget.href.baseVal !== "undefined"){
			anchorSplit = e.currentTarget.href.baseVal.split("#");
		}
		else if(typeof e.currentTarget.href.split !== "undefined"){
			anchorSplit = e.currentTarget.href.split("#");
		}
		if(anchorSplit.length > 1 && anchorSplit[1].length > 0){
			if(nodeId.indexOf(currentNodeId) == -1) {
				parent.postMessage({ "loadAndSyncByIndex": { "nodeId": nodeId, "anchor": anchorSplit[1] } }, "*");
			} else {
				var top = document.getElementById(anchorSplit[1]).offsetTop;
				window.scrollTo(0, top);
			}
		}
		else{
			parent.postMessage({ "loadAndSync": { "nodeId": nodeId } }, "*");
		}
	});
	$('a.schema-index-link').click(function (e) {
		e.preventDefault();		
		parent.postMessage({ "loadAndSyncByIndex": { "nodeId": retrieveDataSetFieldIEWorkaround(e.currentTarget, "nodeId"), "anchor": retrieveDataSetFieldIEWorkaround(e.currentTarget, "nodeAnchor") } }, "*");
	});
}

//Workaround for IE and data parameters on Callout Hotlinks
function retrieveDataSetFieldIEWorkaround(target, dataField)
{	
	if (typeof(target.dataset) !== "undefined" ) {
		return target.dataset[dataField];
	}

	let dataId = dataField.split(/(?=[A-Z])/);
	let dataName = "data-"+dataId.join("-").toLowerCase();

	return target.attributes.getNamedItem(dataName).nodeValue;
}

function sendPageNavData() {
	let meta = document.head.getElementsByTagName("meta");	
	let prev = meta.namedItem("prev");
	if (!prev)
		prev = "";
	else
		prev = prev.content;
	
	let next = meta.namedItem("next");
	if (!next)
		next = "";
	else
		next = next.content;
		
	parent.postMessage({ "pagewieseNavigation": { "prev": prev,
		"next": next }}, "*");
}

function sendPageTitle() {
	var contentTitle = ($("h1.heading").first().text() ? $("h1.heading").first().text() : document.querySelector('h1').innerText);
	parent.postMessage({ "contentTitle": { "title": contentTitle }}, "*");
}

function loadFramesetIfChildpage()
{
	// Check if this page is not already loaded inside an iframe, or that the iframe
	// isn't the one from our index.html:
	if(window.location === window.parent.location || window.parent[0].name !== 'framecontent')
	{
		var filename = document.location.href.split('/').pop();
		var nodeId = filename.substring(0, filename.indexOf('.'));
		document.location = "index." + fileExtension + "#" + nodeId;
	}
}