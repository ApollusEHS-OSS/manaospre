function xhrGetPromise(options) {
    return new Promise(function(resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.timeout = options.timeoutMs || 10 * 1000; // in ms
        xhr.open("GET", options.url);
        xhr.onload = function() {
            if (this.status >= 200 && this.status < 300) {
                //resolving onload
                resolve(xhr.response);
            } else {
                // ignoring error response onload
                //reject(xhr.status);
                resolve("error");
            }
        };
        xhr.onerror = function() {
            //reject(xhr.status);
            // nop
            resolve("onerror");
        };
        xhr.send(options.url);
    });
}

function clearSearchResults() {
    var resultWidget = document.getElementById("resulttag");
    resultWidget.innerText = "";
}

function renderSearchResults(results) {
    var resultWidget = document.getElementById("resulttag");
    var finalHtml = "";
    finalHtml += "<table class=\"searchresults\"><tbody>\n";
    finalHtml += results.map(function (row) {
        return "<tr>" +
            "<td style=\"width:70px;\">" +
                "<button class=\"shapebtn\" onclick=\"addFavoriteIsp(" + row["asn"] + ")\">" +
                    "<i class=\"fa fa-plus\"></i></button> " +
                "<button class=\"shapebtn\" onclick=\"setCurrentShaping(" + row["asn"] + ")\">" +
                    "<i class=\"fa fa-tachometer\"></i></button> " +
            "</td>" +
            "<td><span class=\"flag " + row["cc"].toLowerCase() + "\" style=\"padding:0; margin:0px; margin-top:-2px;\"></span></td>" +
            "<td style=\"width:2em;\">" + row["cc"] + "</td>" +
            "<td>ASN" + row["asn"] + "</td>" +
            "<td>" + row["name"] + "</td>" +
            "</tr>";
    }).join("\n");
    finalHtml += "</tbody><table>\n";

    resultWidget.innerHTML = finalHtml;
}

function sendSearch() {
    var searchWidget = document.getElementById("searchtag");

    if (searchWidget.value == "") {
        clearSearchResults();
    } else {
        var q = xhrGetPromise({url: "/s?q=" + searchWidget.value});
        q.then(function(x) {
            try {
                var results = JSON.parse(x);
                renderSearchResults(results);
            } catch(e) {
                console.log("exception: " + e);
            }
        });
    }
}

function addFavoriteIsp(asn) {
    try {
        xhrGetPromise({url: "/favorites/add/" + asn}).then(function(results) {
            // TODO: error handling on parse failure?
            favoriteIspData = JSON.parse(results)
            renderIspList(favoriteIspData);
        });
    } catch(e) {
        console.log("exception: " + e);
    }
}

function removeFavoriteIsp(offset) {
    var asn = favoriteIspData[offset]["asn"];
    xhrGetPromise({url: "/favorites/remove/" + asn}).then(function(results) {
        console.log(results);
        favoriteIspData = JSON.parse(results)
        renderIspList(favoriteIspData);
    });
}

function updateFavorites() {
    xhrGetPromise({url: "/favorites/"}).then(function(results) {
        favoriteIspData = JSON.parse(results);
        renderIspList(favoriteIspData);
    });
}

function renderIspList(ispData) {
    var isplistWidget = document.getElementById("isplist");
    var finalHtml = "";
    
    var offset = 0;
    for (var i = 0 ; i < ispData.length ; ++i) {
        finalHtml += "<li style=\"margin:2px; padding:0; vertical-align:middle;\">" +
            "<button class=\"shapebtn\" onclick=\"removeFavoriteIsp(" + i + ")\">" +
                "<i class=\"fa fa-minus\"></i></button> " +
            "<button class=\"shapebtn\" onclick=\"setCurrentShaping(" + ispData[i]["asn"] + ")\">" +
                "<i class=\"fa fa-tachometer\"></i></button>" +
            ispData[i]["cc"] + " - " + ispData[i]["name"] +
            "</li>\n";
    }

    isplistWidget.innerHTML = finalHtml;
}

// TODO: have the appserver inject the initial values
var favoriteIspData = [];

function getDisplayText(asnData) {
    // TODO: Check that the required fields are available
    displayText = "";
    if (typeof asnData == "object" && "cc" in asnData && "shape" in asnData) {
        var selectedUtcHour = asnData["selectedutchour"];
        var shape = asnData["shape"][selectedUtcHour];
        displayText = "ISP:" + asnData["cc"] +
            "/" + asnData["name"] + "\n" +
            shape["aws"]["delay"] + "/" + shape["aws"]["loss"] + " " +
            shape["akam"]["delay"] + "/" + shape["akam"]["loss"] + " " +
            shape["oc"]["delay"] + "/" + shape["oc"]["loss"] + " " +
            (shape["bandwidth"] / 1024.0).toFixed(1) + "Mbps";
    }
    return displayText;
}

function setCurrentShaping(asnValue) {
    var shapeDisplayWidget = document.getElementById("shapedisplay");
    asn = parseInt(asnValue);
    
    if ("number" === typeof asn && !isNaN(asn)) {
        xhrGetPromise({url: "/shape?asn=" + asn}).
            then(function(shapeResults) {
                var shapeResultsObj = JSON.parse(shapeResults);
                shapeDisplayWidget.innerText =
                    getDisplayText(shapeResultsObj);
                renderChart(shapeResultsObj);
            });
    }
}

function recalibrate() {
    var calibrationDisplayWidget = document.getElementById("calibrationdisplay");
    calibrationDisplayWidget.innerHTML = "Recalibrating...";
    xhrGetPromise({url: "/recalibrate/execute", timeoutMs: 120 * 1000}).
        then(function(results) {
            var resultsParsed = JSON.parse(results);
            calibrationdisplay.innerHTML = "Recalibrated.<br>(reload ISP)<br>" +
                JSON.stringify(resultsParsed["data"]);
            var shapeDisplayWidget = document.getElementById("shapedisplay");
            shapeDisplayWidget.innerText = "No shaping selected";
        });
}

function getAPKeyToIdMapping() {
    return {
        "wpa_passphrase": "appass",
        "country_code": "apregdomain",
        "channel": "apchannel",
        "ssid": "apname"
    };
}

function updateAPConfig() {
    xhrGetPromise({url: "/apconfig"}).then(function(results) {
        var apconfigWidget = document.getElementById("apconfig");
        var finalHtml = "";
        var keyToIdMapping = getAPKeyToIdMapping();
        apconfig = JSON.parse(results);
        for (key in apconfig) {
            if (key in keyToIdMapping) {
                var elem = document.getElementById(keyToIdMapping[key]);
                elem.value = apconfig[key];
            }
        }
    });
}

function saveAPConfig() {
    var keyToIdMapping = getAPKeyToIdMapping();
    var configToSend = {};
    for (destKey in keyToIdMapping) {
        var domKey = keyToIdMapping[destKey];
        var elem = document.getElementById(domKey);
        configToSend[destKey] = elem.value;
    }
    var configUrl = "/apconfig/set/" + encodeURI(JSON.stringify(configToSend));
    xhrGetPromise({url: configUrl}).then(function(results) {
        console.log("saveAPConfig result: " + results);
    });
}

function renderChart(shapeResultsObj) {
    var srKeys = Object.keys(shapeResultsObj["shape"]);
    var shapeData = srKeys.map(function (k) {
        /* TODO: some error checking here */
        return {"x": k, "y": shapeResultsObj["shape"][k]["aws"]["delay"]};
    });
    var ctx = document.getElementById('timeOfDayChart').getContext('2d');
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: "App Latency",
                    yAxisID: 'y-axis-1',
                    showLine: true,
                    data: shapeData,
                    borderColor: ['rgba(255, 206, 86, 1)'],
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false,
                },
            ]
        },
        options: {
            scales: {
                xAxes: [{
                    type: 'linear',
                    position: 'bottom'
                }],
                yAxes: [{
                    type: 'linear',
                    display: true,
                    position: 'left',
                    id: 'y-axis-1'
                }]
            },
        }
    });
}

function init() {
    updateFavorites(favoriteIspData);
    updateAPConfig();
    // TODO: have the appserver inject the initial values
    var shapeDisplayWidget = document.getElementById("shapedisplay");
    xhrGetPromise({url: "/shape"}).
        then(function(shapeResults) {
            var shapeResultsObj = JSON.parse(shapeResults);
            shapeDisplayWidget.innerText = getDisplayText(shapeResultsObj);
            renderChart(shapeResultsObj);
        });
    var calibrationDisplayWidget = document.getElementById("calibrationdisplay");
    xhrGetPromise({url: "/recalibrate/get"}).
        then(function(results) {
            var resultsParsed = JSON.parse(results);
            if (isNaN(parseInt(resultsParsed["whendt"])) !== true) {
                var recalibrationDate = new Date(resultsParsed["whendt"] * 1000);
                calibrationdisplay.innerHTML = "Last:" +
                    " " + recalibrationDate.toLocaleDateString() +
                    " " + recalibrationDate.toLocaleTimeString() + "<br>" +
                    JSON.stringify(resultsParsed["data"]);
            } else {
                calibrationdisplay.innerHTML = "Uncalibrated";
            }
        });
}
