// Quanos_ST4 2020
// type: COTS 
// license: MIT license

/* autocompletion */
document.addEventListener("DOMContentLoaded", function() {
	 
	var webStorage = false;
	var sStorage;
	var autocompleteCollection = [];
	
	if(webStorage) {
		if(typeof(Storage)) {
			try {
				if(sessionStorage == undefined) {
					writeWebStorage();
				}
			} catch(e) {
				console.log(e);
				return;
			}
			
			if(sessionStorage.getItem("autocompleteTextIndex")){
				autocompleteCollection = JSON.parse(sessionStorage.getItem("autocompleteTextIndex"));
			} else {
				writeWebStorage();
			}
		} else {
			console.log("Your browser doesn't support web storage.");
		}
	} else {
		//do implementation without web storage
		autocompleteCollection = getAutocompleteTextIndex();
	}
	
	function writeWebStorage() {
		autocompleteCollection = getAutocompleteTextIndex();
		sessionStorage.setItem("autocompleteTextIndex",JSON.stringify(autocompleteCollection));
	}
	
	$.typeahead({
    input: '.js-typeahead',
    order: "asc",
	cancelButton: true,
	maxItem: 10,
    source: {
        data: autocompleteCollection
    },
    callback: {
        onInit: function (node) {
            //console.log('Typeahead Initiated on ' + node.selector);
        },
		onClickAfter: function (node, a, item, event) {
			//search after complete text.
			node[0].value = '"' + node[0].value + '"';
			
			var getform = $(node[0]).closest("form");
		
			if(getform) { 
				getform.submit();
			} else {
				console.log("No form element could be found"); 
			}
			
		}
    },
	debug: true
});
	
	//console.log(collection);
});

function getAutocompleteTextIndex() {
	// 2023-03-16: Added check for undefined state
	if("undefined" == typeof titletextindex)
		titletextindex = [];
	//remove empty strings
	var validTitleCollection = onlyValidEntries(titletextindex);
	//only unique words
	var uniqueEntries = validTitleCollection.filter(onlyUnique);
	//result of title/subtitle collection
	var result = uniqueEntries;

	return result;
}

function onlyUnique(value, index, self) { 
    return self.indexOf(value) === index;
}

function onlyValidEntries(data) {
	return data.filter(Boolean);
}

function flattenArray(data) {
	return [].concat.apply([],data);
}