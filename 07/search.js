window.oldXHRs = [];

function processQuery() {
    var mresContainer = document.querySelector('#metaResult');
    mresContainer.style.borderTop = "";
    var mres = document.querySelector('#metaResult > p:first-child');
    mres.innerHTML = "";

    var inp = document.querySelector('#fuzzyQuery');
    var q = inp.value;
    if (q.length < 1) return;

    // may already have searched for this
    if (localStorage.getItem(q) != null) {
        printResults(localStorage.getItem(q));
        return;
    }

    // clear requests not yet finished that became obsolete
    for (var i=0; i<window.oldXHRs.length; i++) {
        try { window.oldXHRs[i].abort(); }
        catch(err) { console.log(err.message); }
    }

    var req = new XMLHttpRequest();
    req.addEventListener("load", parseJSON.bind(req, q));
    req.open("GET", "http://" + window.location.host + "/?q=" + q);
    req.send();
    window.oldXHRs.push(req);
}

function parseJSON(q) {
    resp = JSON.parse(this.responseText);
    cities = resp["results"];

    resText = "";
    for (var i=0; i<cities.length; i++) {
        if (i>9) break;
        city = cities[i]["city"].replace(/&/g, '&amp;').replace(/</g,
            '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        resText += "<p class=\"resultItem\" title=\"Click for more info.\" "
            + "onclick=\"cityQuery(this);\">"+ city + "</p>";
    }

    // building shortcuts cause my java code is hella slow
    // — these would, of course, have to be cleared as soon as the source data
    // (cities2.txt) changes
    localStorage.setItem(q, resText);
    printResults(resText);
}

function printResults(resText) {
    var res = document.querySelector('#result');
    res.innerHTML = resText;
}

function cityQuery(node) {
    var text = node.innerHTML;
    var city = text.split(",")[0];

    var req = new XMLHttpRequest();
    req.addEventListener("load", parseWikiJSON);
    req.open("GET", "https://en.wikipedia.org/w/api.php?format=json&action="
        + "query&prop=extracts&exintro=&explaintext=&origin=*&titles=" + city);
    req.send();
}

function parseWikiJSON() {
    var resp = JSON.parse(this.responseText);
    var matches = Object.keys(resp["query"]["pages"])
    var mres = document.querySelector('#metaResult > p:first-child');
    if (matches[0] != "-1") {
        var key = matches[0];
        var extract = resp["query"]["pages"][key]["extract"];
        var title = resp["query"]["pages"][key]["title"];
        if (extract.length > 0) {
            if (extract.length > 600) {
                extract = extract.substr(0, 600) + "[...]";
                }
            mres.innerHTML = "\"" + extract + "\"<br>&emsp;— <a href=\""
                + "//en.wikipedia.org/wiki/" + title + "\">Wikipedia</a>";
        } else {
            mres.innerHTML = "No further information found.";
        }
    } else {
        mres.innerHTML = "No further information found.";
    }
    var mresContainer = document.querySelector('#metaResult');
    mresContainer.style.borderTop = "solid 1px #555";
}
