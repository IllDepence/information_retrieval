function processQuery() {
    var inp = document.querySelector('#fuzzyQuery');
    var q = inp.value;
    if (q.length < 3) return;

    var req = new XMLHttpRequest();
    req.addEventListener("load", parseJSON);
    req.open("GET", "http://" + window.location.host + "/?q=" + q);
    req.send();

    var mresContainer = document.querySelector('#metaResult');
    mresContainer.style.borderTop = "";
    var mres = document.querySelector('#metaResult > p:first-child');
    mres.innerHTML = "";
}

function parseJSON() {
    resp = JSON.parse(this.responseText);
    cities = resp["results"];

    resText = "";
    for (var i=0; i<cities.length; i++) {
        if (i>9) break;
        resText += "<p class=\"resultItem\" title=\"Click for more info.\" "
            + "onclick=\"cityQuery(this);\">"+ cities[i]["city"] + "</p>";
    }

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
