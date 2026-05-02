// Quanos_ST4 2020
// type: COTS 
// license: MIT license

if (!this["Schema"])
	Schema = function () { };


// =============================================================================
//                                REGEXP EXTENSION
// =============================================================================

Schema.Regex = function () { };
Schema.Regex.Create = function (value, options) {
	var regexOpt = "";
	if ((options & Schema.Regex.Options.AllMatches) != 0)
		regexOpt += "g";
	if ((options & Schema.Regex.Options.IgnoreCase) != 0)
		regexOpt += "i";
	if ((options & Schema.Regex.Options.Multiline) != 0)
		regexOpt += "m";

	var sp = Schema.Regex.Unicode.Separator + Schema.Regex.Unicode.Punctuation;

	value = Schema.Regex.Encode(value);

	if ((options & Schema.Regex.Options.Exact) != 0) {
		string = "^" + value + "$";
	}
	else if ((options & Schema.Regex.Options.WholeWord) != 0) {
		string = "^" + value + "(?=[" + sp + "]+)|[" + sp + "]" + value + "(?=[" + sp + "])|[" + sp + "]" + value + "$|^" + value + "$";
	}
	else if ((options & Schema.Regex.Options.StartWord) != 0) {
		string = "^" + value + "|[" + sp + "]" + value;
	}
	else
		string = value;

	return (new RegExp(string, regexOpt));
}


Schema.Regex.Encode = function (value) {
	return (value.replace(/([.*+?^${}()|[\]\/\\])/g, '\\$1').replace(/\s+/g, "\\s"));
}



Schema.Regex.Options = function () { };
Schema.Regex.Options.None = 0;
Schema.Regex.Options.IgnoreCase = 1;
Schema.Regex.Options.WholeWord = 2;
Schema.Regex.Options.StartWord = 4;
Schema.Regex.Options.Exact = 8;
Schema.Regex.Options.AllMatches = 16;
Schema.Regex.Options.Multiline = 32;

Schema.Regex.Unicode = function () { };
Schema.Regex.Unicode.Punctuation = "\\u0021-\\u0023\\u0025-\\u002A\\u002C-\\u002F\\u003A\\u003B\\u003F\\u0040\\u005B-\\u005D\\u005F\\u007B\\u007D\\u00A1\\u00AB\\u00B7\\u00BB\\u00BF\\u037E\\u0387\\u055A-\\u055F\\u0589\\u058A\\u05BE\\u05C0\\u05C3\\u05C6\\u05F3\\u05F4\\u0609\\u060A\\u060C\\u060D\\u061B\\u061E\\u061F\\u066A-\\u066D\\u06D4\\u0700-\\u070D\\u07F7-\\u07F9\\u0964\\u0965\\u0970\\u0DF4\\u0E4F\\u0E5A\\u0E5B\\u0F04-\\u0F12\\u0F3A-\\u0F3D\\u0F85\\u0FD0-\\u0FD4\\u104A-\\u104F\\u10FB\\u1361-\\u1368\\u166D\\u166E\\u169B\\u169C\\u16EB-\\u16ED\\u1735\\u1736\\u17D4-\\u17D6\\u17D8-\\u17DA\\u1800-\\u180A\\u1944\\u1945\\u19DE\\u19DF\\u1A1E\\u1A1F\\u1B5A-\\u1B60\\u1C3B-\\u1C3F\\u1C7E\\u1C7F\\u2010-\\u2027\\u2030-\\u2043\\u2045-\\u2051\\u2053-\\u205E\\u207D\\u207E\\u208D\\u208E\\u2329\\u232A\\u2768-\\u2775\\u27C5\\u27C6\\u27E6-\\u27EF\\u2983-\\u2998\\u29D8-\\u29DB\\u29FC\\u29FD\\u2CF9-\\u2CFC\\u2CFE\\u2CFF\\u2E00-\\u2E2E\\u2E30\\u3001-\\u3003\\u3008-\\u3011\\u3014-\\u301F\\u3030\\u303D\\u30A0\\u30FB\\uA60D-\\uA60F\\uA673\\uA67E\\uA874-\\uA877\\uA8CE\\uA8CF\\uA92E\\uA92F\\uA95F\\uAA5C-\\uAA5F\\uFD3E\\uFD3F\\uFE10-\\uFE19\\uFE30-\\uFE52\\uFE54-\\uFE61\\uFE63\\uFE68\\uFE6A\\uFE6B\\uFF01-\\uFF03\\uFF05-\\uFF0A\\uFF0C-\\uFF0F\\uFF1A\\uFF1B\\uFF1F\\uFF20\\uFF3B-\\uFF3D\\uFF3F\\uFF5B\\uFF5D\\uFF5F-\\uFF65";
Schema.Regex.Unicode.Separator = "\\u0020\\u00A0\\u1680\\u180E\\u2000-\\u200A\\u2028\\u2029\\u202F\\u205F\\u3000";

// =============================================================================
//                                STRING FUNCTIONS
// =============================================================================


Schema.String = function () { };
Schema.String.Format = function (org) {
	for (var i = 1; i < arguments.length; i++) {
		org = org.replace(new RegExp("\\{" + (i - 1) + "\\}", "g"), arguments[i]);
	}

	return (org);
}

Schema.String.IsNumber = function (obj) {
	return (obj.replace(/[\+-]?\s*\d+/, "") = "");
}



Schema.String.Tokenize = function (tokenStream) {
	tokenStream = tokenStream.replace(/\s+/g, " ");
	var tokens = [];
	var pos = 0;

	while (pos < tokenStream.length) {
		var token = Schema.String.TokenizeNext(tokenStream, pos);
		if (!token)
			break;

		tokens.push(token.value);
		pos = token.end + 1;
	}

	return (tokens);
};


Schema.String.TokenizeNext = function (tokenStream, pos) {
	while (pos < tokenStream.length && tokenStream.substr(pos, 1) == " ")
		pos++;

	if (pos >= tokenStream.length)
		return (null);

	var st = pos;
	var inner = false;
	var lastIsEscape = false;

	while (pos < tokenStream.length) {
		var c = tokenStream.substr(pos, 1);

		if (c == ' ' && !inner) {
			pos--;
			break;
		}
		else if (c == '\\' && inner)
			lastIsEscape = !lastIsEscape;
		else if (c == '"' && !lastIsEscape)
			inner = !inner;
		else
			lastIsEscape = false;

		pos++;
	}

	return ({ "value": tokenStream.substr(st, pos - st + 1), "end": pos + 1 });
};

Schema.String.Trim = function (str) {
	if (!str || str == "")
		return str;

	var res = "";
	var i;

	// look from beginning until a non-whitespace char
	for (i = 0; i < str.length; ++i) {
		if (str.charAt(i) == ' ')
			continue;
		else
			break;
	}
	res = str.substring(i);

	// look from end until a non-whitespace char
	for (i = res.length - 1; i >= 0; --i) {
		if (res.charAt(i) == ' ')
			continue;
		else
			break;
	}
	return res.substring(0, i + 1);
}





// =============================================================================
//                                SCHEMA LOCAL SEARCH
// =============================================================================



Schema.Search = function (init) {
	var self = this;
	var fulltextindex = null;
	var parseTree = [];
	var metaOptions;
	var metaRegex;
	var options;
	var useRanking = true;

	var _ID;
	var _TITLE;
	var _FILENAME;
	var _FILESIZE;
	var _META;
	var _CONTENT;
	var _PRIMARYRANK;
	var defaultLocations;
	

var customTokens = [];

    this.RegisterCustomToken = function ( name, value )
    {

        customTokens.push({name: name, value: value});

    };


	this.GetQueryFromUrl = function (variable) {
		var query = window.location.search.substring(1);
		var vars = query.split("&");

		for (var i = 0; i < vars.length; i++) {
			var pair = vars[i].split("=");
			if (pair[0] == variable)
				return decodeURIComponent((pair[1] + '').replace(/\+/g, '%20'));
		}

		return (false);
	}

	this.CreateExpressionTree = function (obj, options) {
		for (var i = 0; i < obj.length; i++) {
			if (obj[i].type == 'AND') {
				if (obj[i].what && obj[i].what.length > 0) {
					obj[i].regex = Schema.Regex.Create(obj[i].what, options);
					if (obj[i].metaOptions || obj[i].metaOptions == 0)
						obj[i].metaRegex = Schema.Regex.Create(obj[i].what, obj[i].metaOptions);
					else
						obj[i].metaRegex = Schema.Regex.Create(obj[i].what, metaOptions);
				}
			}
			else {
				for (var j = 0; j < obj[i].expr.length; j++) {
					if (obj[i].expr[j].what && obj[i].expr[j].what.length > 0) {
						obj[i].expr[j].regex = Schema.Regex.Create(obj[i].expr[j].what, options);
						if (obj[i].expr[j].metaOptions || obj[i].expr[j].metaOptions == 0)
							obj[i].expr[j].metaRegex = Schema.Regex.Create(obj[i].expr[j].what, obj[i].expr[j].metaOptions);
						else
							obj[i].expr[j].metaRegex = Schema.Regex.Create(obj[i].expr[j].what, metaOptions);
					}
				}
			}
		}

		return (obj);
	};



	this.Execute = function (tokenStream) {
		var result = [];
		var itemRanking = [];

		parseTree = Parse(tokenStream);

		var expressionTree = self.CreateExpressionTree(parseTree, options);
		if (expressionTree.length == 0)
			return (result);

		for (var i = 0; i < fulltextindex.length; i++) {
			var item = fulltextindex[i];

			var itemIsResult = true;
			var rank = 0;
            for (var j = 0; j < expressionTree.length; j++)
            {
                var searchResult = self.Search(expressionTree[j], item, rank);
                if (!searchResult.found)
                {
                    itemIsResult = false;
                    break;
                }
                rank = Math.max(rank, searchResult.rank);
            }

            itemRanking.push(rank);

            if (itemIsResult)
                result.push(i);
		}

		if (useRanking)
		{
			result.sort(function (item1, item2)
			{
				return itemRanking[item2] - itemRanking[item1];
			});
		}
        
        return ( result );
	};



	this.GetExpressions = function () {
		return (parseTree);
	};


	this.GetFulltextIndex = function () {
		return (fulltextindex);
	};


	this.GetMetaOptions = function () {
		return (metaOptions);
	};


	this.GetOptions = function () {
		return (options);
	};


	var Initialize = function (init) {
		fulltextindex = init.fulltextindex;
		if (init.options)
			options = init.options;
		else
			options = Schema.Regex.Options.IgnoreCase;

		if (init.metaOptions)
			metaOptions = init.metaOptions;
		else
			metaOptions = Schema.Regex.Options.IgnoreCase;
		
		if (init.useRanking === false)
			useRanking = false;

		_ID = Schema.Search.Location.Id;
		_TITLE = Schema.Search.Location.Title;
		_FILENAME = Schema.Search.Location.Filename;
		_FILESIZE = Schema.Search.Location.Filesize;
		_META = Schema.Search.Location.Meta;
		_CONTENT = Schema.Search.Location.Content;
		_PRIMARYRANK = Schema.Search.Location.PrimaryRank;

		if (init.defaultLocations)
			defaultLocations = init.defaultLocations;
		else
			defaultLocations = [_TITLE, _CONTENT];
	};


	/*this.Search = function (info, item) {
		if (info.type == 'AND') {
			return (self.SearchAnd(info, item));
		}
		else {
			for (var i = 0; i < info.expr.length; i++) {
				if (self.SearchAnd(info.expr[i], item))
					return (true);
			}
			return (false);
		}
	};*/


	this.Search = function (info, item, initialRank)
	{
		var rank = initialRank;
        if (info.type == 'AND')
        {
            var searchResult = self.SearchAnd(info, item, rank);
            if (searchResult.found)
                rank = Math.max(rank, searchResult.rank);
            return { "found": searchResult.found, "rank": rank };
        }
        else
        {
            var success = true;
            for (var i = 0; i < info.expr.length; i++)
            {
                var searchResult = self.SearchAnd(info.expr[i], item, rank);
                if (searchResult.found)
                    rank = Math.max(rank, searchResult.rank);
                success &= searchResult.found;
            }
   

            return { "found": success, "rank": rank };
        }
    
	};

 this.SearchAnd = function (info, item, initialRank)
    {
        var success = false;
        var rank = initialRank;
        for (var i = 0; i < info.where.length; i++)
        {
            if (info.where[i] == _ID)
            {
                if (item[_ID] == info.what)
                {
                    if (!info.invert)
                    {
                        rank = 100;
                    }
                    success |= !info.invert;
                }
            }
            else if (info.where[i] == _META)
            {
                if (self.SearchMeta(info, item))
                {
                    if (!info.invert)
                    {
						if (rank >= 50 && rank < 75)
							rank++;
						else
							rank = Math.max(rank, 50);
                    }
                    success |= !info.invert;
                }
            }
            else
            {
                if (info.regex.exec(item[info.where[i]]))
                {
                    if (!info.invert)
                    {
                        if (info.where[i] == _TITLE)
                        {
                            if (rank >= 75 && rank < 100)
                                rank++;
                            else
                                rank = Math.max(rank, 75);
                        }
                        else
                        {
                            if (rank >= 25 && rank < 50)
                                rank++;
                            else
                                rank = Math.max(rank, 25);
                        }
                    }

                    success |= !info.invert;
                }
            }
        }
        success |= info.invert;

        return { "found": success, "rank": rank };
    };

	this.SearchMeta = function (info, item) {
		var metaexp = info.metaRegex ? info.metaRegex : metaRegex;

		if (!item[_META] || item[_META].length <= 0)
			return (false);

		if (!info.constraints || info.constraints.length <= 0) {
			if (!info.what || info.what == "") {
				for (var name in item[_META])
					return (true);
				return (false);
			}
			else {
				for (var name in item[_META]) {
					if (metaexp.exec(item[_META][name]))
						return (true);
				}
				return (false);
			}
		}
		else {
			for (var i = 0; i < info.constraints.length; i++) {
				if (!info.what || info.what == "") {
					if (item[_META][info.constraints[i]])
						return (true);
				}
				else {
					var entry = item[_META][info.constraints[i]];
					if (entry && metaexp.exec(entry))
						return (true);
				}
			}
			return (false);
		}
	};


	var Parse = function (tokenStream) {
		var tree = [];

		var tokens = Tokenize(tokenStream);

		for (var i = 0; i < tokens.length; i++) {
			if (tokens[i].type == 'OR') {
				var orToken = { 'type': 'OR', 'expr': [] };
				for (var j = 0; j < tokens[i].value.length; j++) {
					var info = self.ParseToken(tokens[i].value[j]);
					if (info)
						orToken.expr.push(info);
				}

				tree.push(orToken);
			}
			else {
				var info = self.ParseToken(tokens[i].value[0]);
				if (info)
					tree.push(info);
			}
		}

		return (tree);
	};



	var ParseMeta = function (token, info) {
		info.where = [_META];
		token = token.substr(4);

		if (token.substr(0, 1) == '[') {
			var inner = false;
			var lastIsEscape = false;

			var pos = 1;
			while (pos < token.length) {
				var c = token.substr(pos, 1);
				if (c == ']' && !inner)
					break;
				else if (c == '\\' && inner)
					lastIsEscape = !lastIsEscape;
				else if (c == '"' && !lastIsEscape)
					inner = false;
				else
					lastIsEscape = false;

				pos++;
			}

			if (pos >= token.length)
				throw _("Search.Error.ResultWriter.InvalidConstraints", token);


			var temp = token.substr(1, pos - 1).split(",");
			var constraints = [];
			for (var i = 0; i < temp.length; i++) {
				var value = Prepare(temp[i]);
				if (value != "")
					constraints.push(value);
			}

			if (constraints.length > 0)
				info.constraints = constraints;

			if (token.substr(pos + 1, 1) == '(')
				pos = ParseMetaOption(token, pos + 1, info);

			if (!pos) {
				throw _("Search.Error.Parser.InvalidOptions", token);
				return (null);
			}


			if (token.substr(pos + 1, 1) == ':')
				info.what = Prepare(token.substr(pos + 2));
		}
		else if (token.substr(0, 1) == '(') {
			var pos = ParseMetaOption(token, 0, info);

			if (token.substr(pos + 1, 1) == ':')
				info.what = Prepare(token.substr(pos + 2));
		}
		else {
			info.what = Prepare(token.substr(1));
		}

		return (info);
	};


	var ParseMetaOption = function (token, pos, info) {
		var len = token.length;
		var end;
		var st = pos;


		while (pos < len) {
			if (token.substr(pos, 1) == ')') {
				end = pos;
				break;
			}
			pos++;
		}

		if (end) {
			var item = token.substr(st + 1, end - st - 1);
			//if (!item || item.length == 0 || parseInt(item) == NaN)
			//2023-09-01: CFTJSD-2069 Usage of "== NaN" regarded as bug - replaced by Number.isNaN()
			if (!item || item.length == 0 || Number.isNaN(parseInt(item)))
				throw _("Search.Error.Parser.InvalidOptions", token);

			info.metaOptions = parseInt(item);
		}
		else
			throw _("Search.Error.Parser.InvalidOptions", token);

		return (end);
	};



	this.ParseToken = function (token) {
		var info = { 'type': 'AND', 'invert': false };
		if (token.substr(0, 1) == '-') {
			info.invert = true;
			token = token.substr(1);
		}

		if (token.substr(0, 5) == 'meta:' || token.substr(0, 5) == 'meta[' || token.substr(0, 5) == 'meta(')
			ParseMeta(token, info);
		else if (token.substr(0, 6) == 'title:') {
			info.where = [_TITLE];
			info.what = Prepare(token.substr(6));
		}
		else if (token.substr(0, 3) == 'id:') {
			info.where = [_ID];
			info.what = Prepare(token.substr(3));
		}
		else if (token.substr(0, 8) == 'content:') {
			info.where = [_CONTENT];
			info.what = Prepare(token.substr(8));
		}
		else if (token.substr(0, 14) == 'x-set-options:') {
			options = parseInt(token.substr(14));
			info = null;
		}
		else if (token.substr(0, 18) == 'x-set-metaoptions:') {
			metaOptions = parseInt(token.substr(18));
			info = null;
		}
		else {
			info.where = defaultLocations;
			info.what = Prepare(token);
		}

		return (info);
	};


	var Prepare = function (input) {
		if (!input)
			return ("");

		if (input.substr(0, 1) == '"')
			input = input.substr(1);
		if (input.substr(input.length - 1, 1) == '"')
			input = input.substr(0, input.length - 1);
		return (input);
	};


	this.SetMetaOptions = function (opts) {
		metaOptions = opts;
	};


	this.SetOptions = function (opts) {
		options = opts;
	};


	var Tokenize = function (tokenStream) {
		tokenStream = tokenStream.replace(/\s+/g, " ");
		var tokens = [];
		var isOrActive = false;
		var pos = 0;

		while (pos < tokenStream.length) {
			var token = Schema.String.TokenizeNext(tokenStream, pos);
			if (!token)
				break;

			if (token.value.toUpperCase() == "OR") {
				if (tokens.length > 0) {
					tokens[tokens.length - 1].type = 'OR';
					isOrActive = true;
				}
			}
			else {
				if (tokens.length == 0 || !isOrActive)
					tokens.push({ 'type': 'AND', 'value': [token.value] });
				else
					tokens[tokens.length - 1].value.push(token.value);

				isOrActive = false;
			}

			pos = token.end + 1;
		}

		return (tokens);
	};


	Initialize(init);
};



Schema.Search.Location = function () { };
Schema.Search.Location.Id = 0;
Schema.Search.Location.Title = 1;
Schema.Search.Location.Filename = 2;
Schema.Search.Location.Filesize = 3;
Schema.Search.Location.Meta = 4;
Schema.Search.Location.Content = 5;
Schema.Search.Location.Breadcrumb = 6;



Schema.Search.ResultWriter = function (init) {
	var self = this;
	var element = null;
	var elementName = null;
	this.expressionTree = [];
	var environment = 3;
	var pageSize = 10;
	var boundaryRegex = new RegExp("[" + Schema.Regex.Unicode.Separator + Schema.Regex.Unicode.Punctuation + "]");
	var propertyName = "writer";
	var result;

	var CheckHighlight = function (expr, section) {
		var doHighlight = false;
		for (var j = 0; j < section.length; j++) {
			if (ContainsValue(expr.where, section[j])) {
				doHighlight = true;
				break;
			}
		}

		return (doHighlight);
	};



	this.Clear = function () {
		$('.search-results').empty();

	};



	var ContainsValue = function (ary, value) {
		for (var i = 0; i < ary.length; i++) {
			if (ary[i] == value)
				return (true);
		}

		return (false);
	};



	this.Execute = function (resultSet) {

		if (!element) {
			if (!document.getElementById(elementName))
				throw _("Search.Error.ResultWriter.NoElement");

			element = document.getElementById(elementName);
		}

		result = resultSet;
		self.expressionTree = search.CreateExpressionTree(search.GetExpressions(), search.GetOptions() | Schema.Regex.Options.AllMatches);

		self.ShowPage(1);
	};



	var GetEnvironment = function (page) {
		var maxPage = GetMaxPage();

		if (page <= environment + 1)
			return ({ 'start': 1, 'end': Math.min(environment + environment + 1, maxPage) });


		if (maxPage <= environment + environment + 1)
			return ({ 'start': 1, 'end': maxPage });

		if (maxPage - page < environment)
			return ({ 'start': Math.max(1, maxPage - environment - environment), 'end': maxPage });

		return ({ 'start': page - environment, 'end': Math.min(page + environment, maxPage) });
	};


	var GetEnvironmentSize = function () {
		return (environment);
	};


	var GetMaxPage = function () {
		if (!result || result.length <= 0)
			return (0);
		if (pageSize <= 0)
			return (1);

		var len = result.length;
		var count = 0;

		while (len > 0) {
			count++;
			len -= pageSize;
		}

		return (count);
	};



	this.GetPageLink = function (page, text) {
		return ('<a href="javascript:' + propertyName + ".ShowPage(" + page + ');" class="searchResultPagingLink">' + text + '</a>');
	};



	var GetPageRegion = function (page) {
		if (pageSize <= 0)
			return ({ 'start': 0, 'end': result.length - 1 });

		var st = (page - 1) * pageSize;
		var end = Math.min(st + pageSize - 1, result.length - 1);
		if (st > result.length)
			return (null);

		return ({ 'start': st, 'end': end });
	};



	this.GetPageSize = function () {
		return (pageSize);
	};



	this.Highlight = function (text, section) {
		var include = (section ? section : [Schema.Search.Location.Content]);

		for (var i = 0; i < self.expressionTree.length; i++) {
			if (self.expressionTree[i].type == 'AND') {
				if (CheckHighlight(self.expressionTree[i], include))
					text = text.replace(self.expressionTree[i].regex, self.HighlightFunction);
			}
			else {
				for (var j = 0; j < self.expressionTree[i].expr.length; j++) {
					if (CheckHighlight(self.expressionTree[i].expr[j], include))
						text = text.replace(self.expressionTree[i].expr[j].regex, self.HighlightFunction);
				}
			}
		}

		return (text);
	};



	this.HighlightFunction = function (match) {
		var st = "";
		var end = "";
		if (boundaryRegex.test(match.substr(0, 1))) {
			st = match.substr(0, 1);
			match = match.substr(1);
		}
		if (boundaryRegex.test(match.substr(match.length - 1, 1))) {
			end = match.substr(match.length - 1, 1);
			match = match.substr(0, match.length - 1);
		}

		return (st + '<span class="search-result-highlight">' + match + '</span>' + end);
	};



	var Initialize = function (init) {
		elementName = init.element;

		if (init.pageSize && parseInt(init.pageSize) > 0)
			pageSize = parseInt(init.pageSize);
		if (init.environment && parseInt(init.environment) > 0)
			environment = parseInt(init.environment);
		if (init.propertyName)
			propertyName = init.propertyName;
	};


	this.SetEnvironmentSize = function (size) {
		environment = size;
	};


	this.SetPageSize = function (size) {
		pageSize = size;
	};


	this.ShowPage = function (page) {
		
		self.WritePagingAndCount(page);
		self.WriteResultCounts(page);
		if (result && result.length > 0) {
			var region = GetPageRegion(page);
			if (region) {
				var fulltextindex = search.GetFulltextIndex();
				if ($("ul.search-results").length == 0) {
					var resultList = $("<ul />").attr("class", "search-results");
					resultList.appendTo($("article"));
				}
				$("ul.search-results").empty();
				for (var i = region.start; i <= region.end; i++)
					self.WriteResult(fulltextindex[result[i]]);					
			}
		}
		enableSendingMessages();
	};

	this.WriteResultCounts = function (page) {
		var countContainer = $("span#result-count");
		countContainer.text(result.length);
		var queryContainer = $("span#search-query");
		queryContainer.text(search.GetQueryFromUrl("q"));		
	};

	this.WriteContext = function (item) {
		var _CONTENT = Schema.Search.Location.Content;

		var ix = item[_CONTENT].length;

		for (var i = 0; i < self.expressionTree.length; i++) {
			var temp;
			if (self.expressionTree[i].type == 'AND') {
				if (!ContainsValue(self.expressionTree[i].where, _CONTENT))
					continue;

				var temp = item[_CONTENT].search(self.expressionTree[i].regex);
				if (temp >= 0)
					ix = Math.min(temp, ix);
			}
			else {
				for (var j = 0; j < self.expressionTree[i].expr.length; j++) {
					if (!ContainsValue(self.expressionTree[i].expr[j].where, _CONTENT))
						continue;

					var temp = item[_CONTENT].search(self.expressionTree[i].expr[j].regex);
					if (temp >= 0)
						ix = Math.min(temp, ix);
				}
			}
		}

		if (ix < 0 || ix >= item[_CONTENT].length)
			ix = 0;

		if (ix >= 0) {
			var pos = (ix < 100 ? 0 : ix - 100);
			var st = pos;
			var ismiddle = true;

			for (var j = ix - 30; j >= pos; j--) {
				var c = item[_CONTENT].substr(j, 1);
				if (c == '.' || c == '!') {
					st = j + 1;
					ismiddle = false;
					break;
				}
				if (item[_CONTENT].substr(j, 1) == ' ')
					st = j;
			}

			var end = st + 200;
			if (end >= item[_CONTENT].length)
				end = item[_CONTENT].length;

			for (var j = end; j > ix + 30; j--) {
				if (item[_CONTENT].substr(j, 1) == " ") {
					end = j;
					break;
				}
			}

			var text = (ismiddle && st > 0 ? "... " : "") + item[_CONTENT].substr(st, end - st) + (end < item[_CONTENT].length ? "..." : "");

			var context = $('<p />').addClass('search-result-content');

			if (text != undefined) context.html(self.Highlight(text));

			return (context);
		}
	};


	this.WriteResult = function (item) {

		var container = $('ul.search-results');

		var itemContainer = $('<li class="search-result" />').appendTo(container);

		var title = self.WriteResultTitle(item);

		if (title)
			itemContainer.attr("aria-label", title.text())
		title.appendTo(itemContainer);


		var context = self.WriteContext(item);
		if (context)
			context.appendTo(itemContainer);

		var info = self.WriteResultFileInfo(item);
		if (info)
			itemContainer.append(info);


	};


	this.WriteResultFileInfo = function (item) {
		var info = $("<p />").addClass("search-result-info").text(item[Schema.Search.Location.Breadcrumb]);
		return (info);
	};



	this.WriteResultTitle = function (item) {
		var loc = Schema.Search.Location;

		var fileId = item[loc.Filename].split('.')[0];
		var anchor = $('<a />').prop("href", "./index.html#"+fileId)
			.attr("target","_blank")
			.attr("data-node-id", fileId)
			.attr("class", "search-result-title")
			.html(self.Highlight((item[loc.Title] && item[loc.Title].length > 0) ? item[loc.Title] : item[loc.Filename]));

		return anchor;

	};

	this.WritePagingAndCount = function (page) {

		var container = $('nav.search-results-pager');
		container.empty();

		var pager = $('<ul />')
			.addClass('pagination')
			.appendTo(container);

		if (result && result.length > 0) {

			var range = GetEnvironment(page);

			if (range.start != range.end) {

				var back = $('<li>').appendTo(pager)

				if (page != range.start) {
					$(self.GetPageLink(page - 1, '&laquo;')).appendTo(back);
				} else {
					back.addClass('disabled');
					$('<a href="#">&laquo;</a>').appendTo(back);
				}


				for (var i = range.start; i <= range.end; i++) {
					var item = $('<li>')
					if (i == page) {
						item.addClass('active');
						item.attr("aria-current", "page");
						$('<a href="#">' + i + '</a>').appendTo(item);
					}
					else {
						$(self.GetPageLink(i, i)).appendTo(item);
					}
					item.appendTo(pager);
				}

				var next = $('<li>').appendTo(pager)

				if (page != range.end) {
					$(self.GetPageLink(page + 1, '&raquo;')).appendTo(next);
				} else {
					next.addClass('disabled');
					$('<a href="#">&raquo;</a>').appendTo(next);
				}
			}
			else {
				container.remove();
			}


		}

	}

	Initialize(init);
};

var search = null;
var writer = null;

function InitializeSearch() {
	search = new Schema.Search({ 'fulltextindex': typeof fulltextindex === "undefined" ? [] : fulltextindex });
	writer = new Schema.Search.ResultWriter({ 'element': 'search-results', 'search': search });

}

function ExecuteSearch() {
	try {
		if (search) {

			query = search.GetQueryFromUrl("q");

			if (query) {

				var result = search.Execute(query);
				writer.Execute(result);
			}
		}
	}
	catch (e) { alert(e); }
}



$(document).ready(function () {

	if ($('#search-results').length > 0) {
		InitializeSearch();
		ExecuteSearch();			
	}
	
});