// Quanos_ST4 2020
// type: COTS 
// license: MIT license

function postHotspotMessage(hotspotId, highlight) {

	const params = getLocationParams();
	const dataId = params["data-hotspot-id"];
	if (dataId === undefined) {
		return;
	}
	top.postMessage({ dataId: dataId, hotspotId: hotspotId, highlight: highlight }, "*");
}

function receiveHotspotMessage(event) {

	const data = event.data;
	if (!data.hasOwnProperty("hotspotId")) {
		return;
	}
	const params = getLocationParams();
	const dataId = params["data-hotspot-id"];
	if (dataId === undefined || dataId !== data.dataId) {
		return;
	}
	const elements = document.querySelectorAll(`[hotspotid="${data.hotspotId}"]`);
	if (data.highlight) {
		addHotspotHighlight(data.hotspotId, elements);
		return;
	}
	removeHotspotHighlight(data.hotspotId, elements);
}

function updateLinkMap(linkMap, list) {

	if (list === undefined) {
		return;
	}
	const linkList = list.split(String.fromCharCode(0xE027));
	if (linkList.length < 1) {
		return;
	}
	for (let i = 0; i < linkList.length; i++) {

		const link = linkList[i];
		const entries = link.split(String.fromCharCode(0xE028));
		linkMap.set(entries[0], { id: entries[1], title: entries[2] });
	}
}

function writeGeneralHyperlinkAttributes(hyperlink, nodeId, title) {
	hyperlink.setAttribute("href", "#");
	hyperlink.setAttribute("id", `schema-linklist-link-${nodeId}`);
	hyperlink.setAttribute("data-node-id", nodeId);
	hyperlink.setAttribute("title", title);
}

function updateInternalHyperlink(linkMap, hyperlink){
	
	const target = hyperlink.getAttribute("data-target");
	const link = linkMap.get(target);
	if (link) {

		const anchorSplit = link.id.split("#");
		if (anchorSplit.length > 1 && anchorSplit[1].length > 0) {

			writeGeneralHyperlinkAttributes(hyperlink, anchorSplit[0], link.title);
			hyperlink.addEventListener("click", (e) => {
				e.preventDefault();
				top.postMessage({ "loadAndSyncByIndex": { "nodeId": anchorSplit[0], "anchor": anchorSplit[1] } }, "*");
			});
		}
		else {

			writeGeneralHyperlinkAttributes(hyperlink, link.id, link.title);
			hyperlink.addEventListener("click", (e) => {
				e.preventDefault();
				top.postMessage({ "loadAndSync": { "nodeId": link.id } }, "*");
			});
		}
	}
}

(function () {

	window.addEventListener("message", receiveHotspotMessage);
	const hyperlinks = document.getElementsByTagName("a");
	if (hyperlinks.length < 1)
		return;

	const linkMap = new Map();
	const params = getLocationParams();
	const list = params["data-link-list"];
	updateLinkMap(linkMap, list);

	for (let i = 0; i < hyperlinks.length; i++) {

		const hyperlink = hyperlinks[i];
		if (hyperlink.hasAttribute("data-target")) {
			updateInternalHyperlink(linkMap, hyperlink);
		}
		else if (hyperlink.hasAttribute('href') || hyperlink.hasAttribute('xlink:href')) {
			hyperlink.setAttribute("target", "_top");
		}
	}
})();
