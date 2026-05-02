// Quanos_ST4 2020
// type: COTS 
// license: MIT license

$(function() {
	var triggerButtons = document.getElementsByTagName('a');
	for(var i = 0; i < triggerButtons.length; i++){
		if (triggerButtons[i].hasAttribute('data-toggle') && triggerButtons[i].attributes.getNamedItem('data-toggle').value == "collapse" && triggerButtons[i].parentElement.getElementsByClassName('search-result-highlight').length >= 1){
			triggerButtons[i].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));
		}
	}
});