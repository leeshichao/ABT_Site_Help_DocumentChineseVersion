// Quanos_ST4 2020
// type: COTS 
// license: MIT license

$(function() {

	var searchpage = $("body").hasClass("schema-search");
    // pull in the new value
	var text = window.location.search.substring(3);
	var words = getwords(text);
	
	if(searchpage == false) {
		if(words.length != 0) {
			$.each(words, function(key, value) {
			
				// remove any old highlighted terms
				//$('.container').removeHighlight();
				// disable highlighting if empty

				if ( value ) {
					// highlight the new term
					$('.highlightable').highlight(value);
				}
			});
		}
	}
	
	function getwords(text) {
		var re = /\s(?=(?:[^'"`]*(['"`]).*?\1)*[^'"`]*$)/g;
		var str = decodeURI(text.replace(/%22/g,'"').replace(/%20/g,' ').replace(/%3A/g,':').replace(/%2C/,','));
		var collection = str.split(re);
		//var reducedcollection = _.without(collection,undefined,'"',"'");
		// 2023-03-16: Replaced underscore.js functions by native functions
		var reducedcollection = collection.filter(function(value){
			return value !== '"' && value !== "'"; 
		});
		
		//var result = _.map(reducedcollection, function(value) { 
		// 2023-03-16: Replaced underscore.js functions by native functions
		var result = reducedcollection.map(function(value) { 
			var str = ""; 
			var length = value.length; 
			var start = value.substr(0,1); 
			var end = value.substr(length - 1, length); 
			
			if(start == end) { 
				if(start.match(/("|')/)) { 
					str = value.substr(1,length - 2).replace(/\+/g,' ');
				} else { 
					str = value.split("+");
				} 
			} else { 
				str = value.split("+"); 
			}
			
			return str;
		});
		
		//return _.flatten(result);
		// 2023-03-16: Replaced underscore.js functions by native functions
		return result.reduce( (a, b) => a.concat(b), []);
	}
});