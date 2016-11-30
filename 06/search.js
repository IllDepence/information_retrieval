function processQuery() {
    var inp = document.querySelector('#fuzzyQuery');
    var q = inp.value;
    if (q.length < 3) return;

    var req = new XMLHttpRequest();
    req.addEventListener("load", parseJSON);
    req.open("GET", "http://" + window.location.host + "/?q=" + q);
    req.send();
}

function parseJSON() {
    resp = JSON.parse(this.responseText);
    cities = resp["results"];

    resText = "";
    for (var i=0; i<cities.length; i++) {
      if (i>9) break;
      resText += cities[i]["city"] + "<br>";
    }

    var res = document.querySelector('#result');
    res.innerHTML = resText;
}
