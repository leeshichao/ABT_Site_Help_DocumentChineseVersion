// Quanos_ST4 2020
// type: COTS 
// license: MIT license

document.addEventListener("DOMContentLoaded", function() {
	var param = window.location.hash;
	var search = window.location.search;
console.log ("Die Console funktioniert");
	if(param || search) {
		var indexEntry = param.substring(1);
		var searchEntry = search.substr(3).replace(/\+|%22|%20/g,' ').trim();
		
		//Opening index entries in collapsibles
		if(indexEntry.substr(0,3) == "ID0") {
			$.each($("a.card"), function(index, collapsible) { 
				var card = $(collapsible);
				if(card.attr("data-entries")) {
					if(card.attr("data-entries").match(indexEntry)) {
						card.click();
						console.log ("Klick ausgelöst");
					}
				}
			});
			//Opening content in Collaosibles through a link (passing by a parameter from the URL)
		} else {
			$.each($("a.card"), function(index, collapsible) {
				var card = $(collapsible);
				var cardTextContent = $(collapsible).next("div.collapse")[0].textContent.toUpperCase();
				var textIsContained = cardTextContent.indexOf(searchEntry.toUpperCase());
				
				if(textIsContained !== -1) {					
					var currentId = window.location.hash;
					var currentCardId = collapsible.hash.replace('collapse','');
					
					if(currentId.indexOf(currentCardId) != -1) {
						card.click();
						console.log ("Klick ausgelöst");
					}
				}
			});
		}
	}
});

function expandContent(linkId) {
	if(linkId) {
		$.each($("div.textmodule"), function(index, tm) {
			
			var textmoduleId = tm.id;
			var card = $(tm).children("a.card");
			var contentDiv = $(tm).children("div.collapse");
		
			if(textmoduleId == linkId) {
				if(!$(contentDiv).hasClass("in")) {
					card.click();
					console.log ("Klick ausgelöst");
				}
			} else {
				if($(contentDiv).hasClass("in")) {
					card.click();
					console.log ("Klick ausgelöst");
				}
			}
		});
	}
}