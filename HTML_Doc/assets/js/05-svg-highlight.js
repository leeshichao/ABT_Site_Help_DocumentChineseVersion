// Quanos_ST4 2020
// type: COTS 
// license: MIT license

var legendHighlightClass = "hotspot-highlight";
var svgHightlightClass = "highlight";
var linkMap = new Map();

$("[data-insert-svg]").each(function( index ) {
	var list = $(this).attr("data-link-list");
	var linkList = list.split(String.fromCharCode(0xE027));
	linkList.forEach(function(link)	{
		var s = link.split(String.fromCharCode(0xE028));
		linkMap.set(s[0], link);
	});

	var hotspotId = $(this).attr("data-hotspot-id");
	$(this).after(omd.svgImages[$(this).attr("data-insert-svg")]);
	var svg = $(this).next();
	svg.attr('data-hotspot-id', hotspotId);
    $(this).remove();
});

$("svg").each(function( index ) {

    var svg = Snap(this);
	var elements = svg.selectAll("a");
	if(!elements)
		return;
  	
	elements.forEach(function(element) {
	  	if(element.node.hasAttribute('data-target')) {
			var target = element.node.getAttribute('data-target');
			var link = linkMap.get(target);
			
			
			if(link) {
				var linkElements = link.split(String.fromCharCode(0xE028));
				var nodeId = linkElements[1];				
				const anchorSplit = nodeId.split('#');
				if(anchorSplit.length > 1 && anchorSplit[1].length > 0){
					nodeId = anchorSplit[0];
					element.node.setAttribute('href', './index.html#' + nodeId);
				}
				else{
					element.node.setAttribute('href', './index.html#'+ nodeId);
				}
		    	element.node.setAttribute('target', '_blank'); //open in new window
			}
		}
		else if (element.node.hasAttribute('href') || element.node.hasAttribute('xlink:href')) {
			element.node.setAttribute('target', '_blank'); //open in new window
		}
  	});
});

$("svg").each(function( index ) {
    var svg = Snap(this);

    var tableLegend = $('table[data-legend-id=' + $(this).attr('data-hotspot-id')  + ']');
	
    tableLegend.on("mouseenter", "td:nth-child(odd)", function() {
        setFocus(findSvgElementFromLegendTable($(this)));
        highlightTableEntries($(this));
    });

    tableLegend.on("mouseleave", "td:nth-child(odd)", function() {
        leaveFocus(findSvgElementFromLegendTable($(this)));
        unhighlightTableEntries($(this));
    });

    tableLegend.on("mouseenter", "td:nth-child(even)", function() {
        setFocus(findSvgElementFromLegendTable($(this).prev()));
        highlightTableEntries($(this).prev());
    });
    tableLegend.on("mouseleave", "td:nth-child(even)", function() {
        leaveFocus(findSvgElementFromLegendTable($(this).prev()));
        unhighlightTableEntries($(this).prev());
    });

    $(this).on("mouseenter", "[hotspotid]", function() {
        setFocus(findMatchingSvgElements($(this)));
        highlightTableEntries(findTableEntryForSvgElement($(this)));
    });

    $(this).on("mouseleave", "[hotspotid]", function() {
        leaveFocus(findMatchingSvgElements($(this)));
        unhighlightTableEntries(findTableEntryForSvgElement($(this)));
    });

    function findSvgElementFromLegendTable(leftTableEntry) {
        var ref = leftTableEntry.children()[0].innerHTML;
        return svg.selectAll("*[hotspotid=\"" + ref + "\"]");
    }

    function findMatchingSvgElements(domElement) {
        var ref = domElement.attr("hotspotid");
        return svg.selectAll("*[hotspotid=\"" + ref + "\"]");
    }

    function findTableEntryForSvgElement(domElement) {
        var ref = domElement.attr("hotspotid");
        var entry = tableLegend.find("td:nth-child(odd)").filter(function() {
            return $(this).find("p").text() == ref;
        });
        return entry.first();
    }
});


function setFocus(svgElements) {
  if(!svgElements)
    return;
  svgElements.forEach(function(element) {
    element.addClass(svgHightlightClass);
  });
}

function leaveFocus(svgElements) {
  if(!svgElements)
    return;
  svgElements.forEach(function(element) {
    element.removeClass(svgHightlightClass);
  });
}

function highlightTableEntries(leftTableEntry) {
  if(!leftTableEntry)
    return;
  leftTableEntry.addClass(legendHighlightClass);
  leftTableEntry.next().addClass(legendHighlightClass);
}

function unhighlightTableEntries(leftTableEntry) {
  if(!leftTableEntry)
    return;
  leftTableEntry.removeClass(legendHighlightClass);
  leftTableEntry.next().removeClass(legendHighlightClass);
}

$("iframe").each(function() {
	
	var dataId = $(this).attr('data-hotspot-id');
	var tableLegend = $('table[data-legend-id=' + dataId  + ']');
		
	function NotifyIframes(tableEntry, highlight){
	    var hotspotid = tableEntry.children()[0].innerHTML;
		$("iframe").each(function() { this.contentWindow.postMessage({ dataId: dataId, hotspotId: hotspotid, highlight: highlight }, "*"); });
	}
	tableLegend.on("mouseenter", "td:nth-child(odd)", function() { NotifyIframes($(this), true); });
	tableLegend.on("mouseleave", "td:nth-child(odd)", function() { NotifyIframes($(this), false); });
	tableLegend.on("mouseenter", "td:nth-child(even)", function() { NotifyIframes($(this).prev(), true); });
	tableLegend.on("mouseleave", "td:nth-child(even)", function() { NotifyIframes($(this).prev(), false); });
});

window.addEventListener("message", function(event) {

    var data = event.data;
	if(!data.hasOwnProperty("hotspotId")){
		return;
	}
	var tableLegend = $('table[data-legend-id=' + data.dataId  + ']');
	if(!tableLegend.length && window === window.parent){
		$("iframe").each(function() { this.contentWindow.postMessage(data, "*"); });
		return;
	}
	var entry = tableLegend.find("td:nth-child(odd)")
		.filter(function() { return $(this).find("p").text() == data.hotspotId; })
		.first();
		
	if(data.highlight){
		highlightTableEntries(entry);
		return;
	}
	unhighlightTableEntries(entry);
});
