// Quanos_ST4 2020
// type: COTS 
// license: MIT license

/* Version 2023 V1 */
/*### iFrame handling ###*/
/* Handler listening to iframe messages, needed to cirumvent "same origin policy" when runing local only */
/* This logic can and should be changed to kind of ajax if running on a webserver */
var indexAnchor = null;

window.addEventListener('message', function (event) {
	
	//Event handling in case iframe request navigation to a different page
	if (event.data.loadAndSync) {
		//this will trigger a $(window) 'hashchange' event which in turn leads to sync and load
		document.location.href = document.location.href.split("#")[0].concat("#", event.data.loadAndSync.nodeId);
	}
	
	//Event handling if index link is ckliced, fires a scrollTo-Message which the ifrma handles
	if (event.data.loadAndSyncByIndex) {
		const postAnchorMessage = function() {	
			document.getElementById("framecontent").removeEventListener("load", postAnchorMessage);		
			document.getElementById("framecontent").contentWindow.postMessage({ "scrollToAnchor": { "anchor": event.data.loadAndSyncByIndex.anchor } }, "*");										
		}
		document.getElementById("framecontent").addEventListener("load", postAnchorMessage);
		document.location.href = document.location.href.split("#")[0].concat("#", event.data.loadAndSyncByIndex.nodeId);
	}
	
	//Event handling to change document.title which is shown in tab text 
	if (event.data.contentTitle) {  
		var mainTitle = document.head.getElementsByTagName("meta")[name = "description"].content;
		mainTitle = (mainTitle != '' ? mainTitle : document.querySelector('meta[name = description]').content);
		if (event.data.contentTitle.title !== "" && mainTitle != event.data.contentTitle.title)
			document.title = mainTitle + " - " + event.data.contentTitle.title;
		else
			document.title = mainTitle;
		
		$("iframe#framecontent").attr("title", event.data.contentTitle.title);
	}
	
	//Event handling in case a pagewise navigation link is clicked
	if (event.data.pagewieseNavigation) {
		if (event.data.pagewieseNavigation.prev === "") {
			$("a#prev-page").addClass("invisible");
			$("a#prev-page-small").addClass("invisible");
		}
		else {
			$("a#prev-page").removeClass("invisible");
			$("a#prev-page-small").removeClass("invisible");
			$("a#prev-page").attr("data-node-id", event.data.pagewieseNavigation.prev);
			$("a#prev-page-small").attr("data-node-id", event.data.pagewieseNavigation.prev);
		}
		
		if (event.data.pagewieseNavigation.next === "") {
			$("a#next-page").addClass("invisible");
			$("a#next-page-small").addClass("invisible");
		}
		else {
			$("a#next-page").removeClass("invisible");
			$("a#next-page-small").removeClass("invisible");
			$("a#next-page").attr("data-node-id", event.data.pagewieseNavigation.next);		
			$("a#next-page-small").attr("data-node-id", event.data.pagewieseNavigation.next);		
		}				
	}
});

/* Functions to manage content loading into iframe and to keep TOC in sync */
function loadContent(nodeId) {
	if (isKnownNodeId(nodeId))
		$("iframe#framecontent")[0].contentWindow.location.replace(nodeId.concat('.', fileExtension));
}

/*### TOC implementation ###*/

//reads URL and loads respective content
function loadContentByBrowserAddressBar() {
	let nodeId = document.location.href.split('#')[1];
	if (!nodeId || !isKnownNodeId(nodeId)) 
		nodeId = "index_content";
	
	if (nodeId !== "search") {
		loadContent(nodeId);
		synchronizeToc(nodeId);
		setActiveTocEntry(nodeId);
	}
	else
		$("iframe#framecontent").first().attr("title","search");	
}

function isKnownNodeId(nodeId) {
	if (nodeId === "search" || nodeId === "index_content")
		return true;
	try {
		return /^[\d-]+$/.test(nodeId);
	}
	catch(e) { }
	return false;
}


function synchronizeToc(nodeId) {
	document.location.href = document.location.href.split("#")[0].concat("#", nodeId);
	var link = $('#toc-link-'.concat(nodeId));
	link.parents("ul.schema-collapse").collapse("show");
	link.closest("li.nav-item").find("ul.collapse.show").collapse("hide");
	$("button#toc-dropdown-".concat(nodeId)).click();
}

function setActiveTocEntry(nodeId) {
	$("nav.schema-toc").find(".schema-toc-link.active").removeClass("active");
	$('#toc-link-'.concat(nodeId)).addClass("active");
}

/* Rotating triangle in TOC if expand/collapsed */
$("ul.schema-collapse").on("hide.bs.collapse", function (e) {
	$(e.target).siblings("div").first().children("button").first().css("transform", "rotate(0deg)");
});

$("ul.schema-collapse").on("show.bs.collapse", function (e) {
	if ($("body").attr("dir") === "rtl")
		$(e.target).siblings("div").first().children("button").first().css("transform", "rotate(-90deg)");
	else
		$(e.target).siblings("div").first().children("button").first().css("transform", "rotate(90deg)");
});

/* TOC interactivity */

//hide or show TOC
$("button#schema-toc-toggle").click(function (e) {
	e.preventDefault();
	let tocmenu = document.getElementsByClassName("schema-toc-nav")[0];
	let tocHidden = tocmenu.classList.contains("d-none");
	if (tocHidden) {
		tocmenu.classList.remove("d-none");
	}
	else if (!tocHidden) {
		tocmenu.classList.add("d-none");
	}
});

//hande pagewise navigation events
$("a.schema-pagewise-nav").click(function (e) {
	e.preventDefault();		
	document.location.href = document.location.href.split("#")[0].concat("#", e.currentTarget.dataset.nodeId);
});

//link is clicked
$("a.schema-toc-link").click(function (e) {
	e.stopPropagation();
	e.preventDefault();
	if (e.currentTarget.classList.contains("active")) {
		$("button#toc-dropdown-".concat(e.currentTarget.dataset.nodeId)).click();
		$(e.currentTarget).removeClass("active");
		$(e.currentTarget).addClass("active");
	}
	else {
		document.location.href = document.location.href.split("#")[0].concat("#", e.currentTarget.dataset.nodeId);
		//can be set in OMD and will be put into header of index-file per aspect
		if (menuAutoClose === "true") {
			$("nav.schema-toc-nav").addClass("d-none");
		}
		//this grabs the focus and transfers it to the iframe after a TOC link has been acitvated	
		$("#framecontent")[0].focus();
	}
});

function getNextLiElement(searchRoot) {
	//fetch the parent li
	var listElement = searchRoot.parents("li").first();

	var nextEntry = listElement.next("li").first();
	if (nextEntry.length > 0)
		return nextEntry.find("div>a").first();
	var rootLevel = listElement.parent("ul.schema-toc-menu");
	if (rootLevel.length > 0)
		return rootLevel.find("li>div>a").first();

	//go one layer up
	return getNextLiElement(listElement);
}

/* implementing keyboard navigation in TOC */
function getNextVisibleLink(linkElement) {
	var divElement = linkElement.closest("div");
	var submenuElement = divElement.next("ul");
	if (submenuElement.length > 0 && submenuElement.hasClass("show"))
		return submenuElement.find("li>div>a").first();

	//if no submenu is in this layer get the next li element
	var next = getNextLiElement(divElement);
	return next;
}

function getLastVisibleSubMenuLink(searchRoot) {
	var lastElement = searchRoot.children().last();
	if (!(lastElement.hasClass("schema-toc-submenu") && lastElement.hasClass("show")))
		return searchRoot.find("div>a").first();

	return getLastVisibleSubMenuLink(lastElement.children("li").last());
}

function getPrevVisibleLink(linkElement) {
	var listEntry = linkElement.closest("li");
	var prevEntry = listEntry.prev("li");
	if (prevEntry.length > 0)
		return getLastVisibleSubMenuLink(prevEntry.last());

	var prevLayer = listEntry.closest("ul").closest("li");
	if (prevLayer.length > 0)
		return prevLayer.find("div>a").first();

	return getLastVisibleSubMenuLink(listEntry.closest("ul").children().last());
}

function tocLinkCloseArrowKey(e) {
	var btn = $("button#toc-dropdown-".concat(e.currentTarget.dataset.nodeId))[0];
	if (btn != null && $(btn.dataset.target).hasClass("show"))
		btn.click();
}

function tocLinkOpenArrowKey(e) {
	var btn = $("button#toc-dropdown-".concat(e.currentTarget.dataset.nodeId))[0];
	if (btn != null && !$(btn.dataset.target).hasClass("show"))
		btn.click();
}

$("a.schema-toc-link").keyup(function (e) {
	//left	
	if (e.keyCode == 37) {
		if ($("body").attr("dir") === "rtl")
			tocLinkOpenArrowKey(e);
		else
			tocLinkCloseArrowKey(e);
	}
	//right
	if (e.keyCode == 39) {
		if ($("body").attr("dir") === "rtl")
			tocLinkCloseArrowKey(e);
		else
			tocLinkOpenArrowKey(e);
	}
	//down
	if (e.keyCode == 40) {
		//gets the li element the link is in 		
		getNextVisibleLink($(this)).focus();
	}
	//up
	if (e.keyCode == 38) {
		getPrevVisibleLink($(this)).focus();
	}
});

/*### upper navbar inlcuding search and languange dropdown functions ###*/
$("a.schema-navbar-link").click(function (e) {
	e.stopPropagation();
	e.preventDefault();
	if (e.currentTarget.dataset.nodeId)
		document.location.href = document.location.href.split("#")[0].concat("#", e.currentTarget.dataset.nodeId);
	else
		document.location.href = document.location.href.split("#")[0];
});

$("a.langMenuItem").click(function (e) {
	let nodeId = document.location.href.split('#')[1];
	if (!nodeId) nodeId = "index_content";
	e.target.setAttribute('href', e.target.href.concat('#', nodeId));
})

$("button#search-toggle").click(function (e) {
	e.preventDefault();
	$("#search-collapse").collapse("toggle");
	$("input#search-form")[0].focus();
});

$("input#search-form").keyup(function (e) {
	if (e.keyCode == 27) {
		$("#search-collapse").collapse("hide");
	}
});

$("form#navbar-search").submit(function (e) {
	setAddressbar("search");
})

$("form#search-collapse").submit(function (e) {
	setAddressbar("search");
})

function setAddressbar(name) {
	document.location.href = document.location.href.split("#")[0].concat("#", name);
};

function iOSSpecialWorkarounds() {
	let userAgent = navigator.userAgent.toLowerCase();
	if ( userAgent.match(/ipad/i) || userAgent.match(/iphone/i) ) {		
		let scrollContainerHeight = $(document).height();
		let scrollContainerWidth = $(document).width();		
		//quick and dirty, value determined empirically
		$("#scroll-container").height(scrollContainerHeight - 60);
		$("nav.schema-toc-nav").height(scrollContainerHeight - 60);
		$("#scroll-container").css("overflow", "auto");			
	}
};

$(document).ready(function () {
	function checkIFrame() {
		var iframe = $("iframe#framecontent")[0];
		if (!iframe) {
			return true;
		}
		let addressBar = document.location.href.split("#");
		return addressBar.length < 2;
	}

	if (!checkIFrame()) {
		loadContentByBrowserAddressBar();
	};
	
	// iOS workaround for iframes -- sets the scroll container height	
	iOSSpecialWorkarounds();
});

/*### reloads the page upon screen orientationchange event ###*/
$(window).on('orientationchange', function(event) {
	let userAgent = navigator.userAgent.toLowerCase();
	if ( userAgent.match(/ipad/i) || userAgent.match(/iphone/i) ) {		
		document.location.reload(true);
	}	
});

/*### fire only if addressbar has changed ###*/
$(window).on('hashchange', function (e) {
	loadContentByBrowserAddressBar();
});

/*### options for popovber ###*/
var popoverOptions = {
        container: "body",
        placement: "bottom",
        trigger: "hover",
        delay: {
            show: 200,
            hide: 100
        }
    };
	
$(function () {
$('[data-bs-toggle="popover"]').popover(popoverOptions)
})