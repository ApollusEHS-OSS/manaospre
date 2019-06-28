import json, sqlite3, os
from flask import Flask, Response, request, g, send_from_directory
from urllib.parse import unquote
from wiphyutils import get_available_channels

# TODO: factor out hostapconfgenerator to a proper module for common use
import sys
sys.path.append("..")
import hostapconfgenerator

# TODO: refactor away app
app = application = Flask(__name__, static_url_path="")

# TODO: read the firewall to get this information
NETWORK_CONFIG = {
    "aws": {"classid": "1:2", "handle": "12"},
    "akam": {"classid": "1:3", "handle": "13"},
    "oc": {"classid": "1:4", "handle": "14"}
}

SHAPING_DB_FULLPATH = "/tmp/shaping.db"
FAVORITES_FULLPATH = "/tmp/favorites.json"
APCONFIG_FULLPATH = "/tmp/apconfig.json"
LASTCALIBRATION_FULLPATH = "/tmp/lastcalibration.json"
LASTDISPLAY_OBJECT_FILENAME = "/tmp/lastdisplay.json"
MAX_RATE_KBPS = 100000
HOSTAPD_RELOAD_FULLPATH = "/usr/bin/hostapd-reload"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(SHAPING_DB_FULLPATH)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def get_structured_search_result(query, params, asDict=False):
    results = []
    c = get_db().cursor()
    c.execute(query, params)
    results_per_asn = {}
    for row in c.fetchall():
        shape = {
            "aws": {
                "loss": row[4],
                "delay": row[5]
            },
            "akam": {
                "loss": row[6],
                "delay": row[7]
            },
            "oc": {
                "loss": row[8],
                "delay": row[9]
            },
            "bandwidth": row[10]
        }
        asn = row[0]
        utchour = row[3]
        if asn not in results_per_asn:
            results_per_asn[asn] = {}
        if "shape" not in results_per_asn[asn]:
            results_per_asn[asn]["shape"] = {}
        # make utchour a string since the array can have holes
        results_per_asn[asn]["shape"][str(utchour)] = shape
        results_per_asn[asn]["name"] = row[1]
        results_per_asn[asn]["cc"] = row[2]
    for asn, row in results_per_asn.items():
        results.append({"asn": asn, "name": row["name"],
            "cc": row["cc"], "shape": row["shape"]})

    # return only the first one as a dict when asDict is set
    if asDict == True:
        results = results[0]
    return results


@app.route('/s', methods = ["GET", "POST"])
def search():
    q = request.args.get("q")
    results = []
    if q is not None:
        # ASN search:
        if q.isdigit() == True:
            search_query = """SELECT
                    asn.id,asn.friendlyname,asn.countrycode,
                    shape.utchour,
                    shape.awsdelay,shape.awsloss,
                    shape.akamdelay,shape.akamloss,
                    shape.ocdelay,shape.ocloss,
                    shape.bandwidth
                FROM asn JOIN shape ON asn.id = shape.asn
                WHERE asn.id like ?
                ORDER BY CAST(asn.id AS INTEGER)
                LIMIT 1200"""
            results = get_structured_search_result(
                search_query, ("" + q + "%",))
        elif len(q) > 2 or len(q) == 1:
            search_query = """SELECT
                    asn.id,asn.friendlyname,asn.countrycode,
                    shape.utchour,
                    shape.awsdelay,shape.awsloss,
                    shape.akamdelay,shape.akamloss,
                    shape.ocdelay,shape.ocloss,
                    shape.bandwidth
                FROM asn JOIN shape ON asn.id = shape.asn
                WHERE friendlyname LIKE ?
                LIMIT 2400"""
            results = get_structured_search_result(
                search_query, ("%" + q + "%",))
        elif len(q) == 2:
            c = get_db().cursor()
            search_query = """SELECT
                    asn.id,asn.friendlyname,asn.countrycode,
                    shape.utchour,
                    shape.awsdelay,shape.awsloss,
                    shape.akamdelay,shape.akamloss,
                    shape.ocdelay,shape.ocloss,
                    shape.bandwidth
                FROM asn JOIN shape ON asn.id = shape.asn
                WHERE asn.countrycode = UPPER(?) OR friendlyname like ?
                LIMIT 2400"""
            results = get_structured_search_result(
                search_query, (q, q))

    resp = Response(json.dumps(results, indent=4))
    resp.headers['Content-Type'] = 'text/json'
    return resp


def send_shape_commands(lastCalibration, asn_data):
    utchour = str(asn_data["selectedutchour"])
    shape = asn_data["shape"][utchour]
    rate_raw = shape["bandwidth"]
    rate_clause = " rate 4Mbit"
    if rate_raw is not None and rate_raw > 0 and rate_raw < MAX_RATE_KBPS:
        rate_clause = " rate %dKbit" % (rate_raw,)

    for shortcode in ["aws", "akam", "oc"]:
        latency = shape[shortcode]["delay"]
        latency -= lastCalibration[shortcode]
        # TODO: calibration
        cmd = "sudo tc qdisc replace dev ifb0 parent %s handle %s: netem delay %dms loss %s%% %s" % (
                NETWORK_CONFIG[shortcode]["classid"],
                NETWORK_CONFIG[shortcode]["handle"],
                latency,
                shape[shortcode]["loss"],
                rate_clause
                )
        # TODO: Use proper logging
        print(cmd)
        os.system(cmd)


def get_status_display_text(asn_data):
    utchour = asn_data["selectedutchour"]
    result_text = "ISP:%s/%s\n" % (asn_data["cc"], asn_data["name"])
    shape_text = ""
    shape = asn_data["shape"][str(utchour)]
    for shortcode in ["aws", "akam", "oc"]:
        if shape_text != "":
            shape_text += " "
        shape_text += "%d/%d" % (
            shape[shortcode]["delay"],
            int(float(shape[shortcode]["loss"])))
    result_text += shape_text
    return result_text


def update_status_display(display_text):
    with open("/tmp/lastdisplay.txt", "w") as f:
        f.write(display_text)


def update_last_shape(shape_to):
    utchour = shape_to["selectedutchour"]
    shape_to["selectedutchour"] = utchour
    json.dump(shape_to, open(LASTDISPLAY_OBJECT_FILENAME, "w"))


def get_last_display_update_text():
    display_text = ""
    try:
        with open("/tmp/lastdisplay.txt", "r") as f:
            display_text = "".join(f.readlines())
    except IOError as e:
        display_text = "Unknown shape"
    return display_text


def get_last_display_update():
    result = {}
    try:
        result = json.load(open(LASTDISPLAY_OBJECT_FILENAME))
    except (FileNotFoundError, ValueError):
        pass
    return result


def get_latest_calibration():
    last_calibration = {"oc": 2, "aws": 22, "akam": 13}

    try:
        last_calibration = json.load(open(LASTCALIBRATION_FULLPATH, "r"))
    except (ValueError, IOError) as e:
        print(("Ignoring %s with %s" % (e, LASTCALIBRATION_FULLPATH)))

    # ensure all keys at least have a 0
    for k in ["oc", "aws", "akam"]:
        if (k in last_calibration) is False:
            last_calibration[k] = 0

    return last_calibration


def get_asn_shape(asn):
    search_query = """SELECT
            asn.id,asn.friendlyname,asn.countrycode,
            shape.utchour,
            shape.awsdelay,shape.awsloss,
            shape.akamdelay,shape.akamloss,
            shape.ocdelay,shape.ocloss,
            bandwidth
        FROM asn JOIN shape ON asn.id = shape.asn
        WHERE asn.id = ?
        ORDER BY CAST(asn.id AS INTEGER)
        LIMIT 1200"""
    return get_structured_search_result(
        search_query, (asn,), asDict=True)


@app.route("/shape")
def shape():
    utchourraw = request.args.get("utchour")
    utchour = 0
    if utchourraw is not None and utchourraw.isdigit() == True:
        utchour = int(utchourraw)
    display_text = get_last_display_update_text()
    asn_shape_to = get_last_display_update()

    asnraw = request.args.get("asn")
    if asnraw is not None:
        try:
            lastCalibration = get_latest_calibration()
            asn = int(asnraw)
            asn_shape_to = get_asn_shape(asn)
            # TODO: choose the median instead
            # if utchour isn't in the shape, choose the lowest hour
            if str(utchour) not in asn_shape_to["shape"]:
                hours_with_data = sorted(
                    [int(x) for x in asn_shape_to["shape"].keys()])
                utchour = hours_with_data[0]
            asn_shape_to["selectedutchour"] = utchour
            send_shape_commands(lastCalibration, asn_shape_to)
            display_text = get_status_display_text(asn_shape_to)
            update_status_display(display_text)
            update_last_shape(asn_shape_to)
        except ValueError as e:
            print(("invalid number:", asnraw))

    # return current shaping
    #resp = Response(display_text)
    #resp.headers['Content-Type'] = 'text/plain'
    resp = Response(json.dumps(asn_shape_to, indent=4))
    resp.headers["Content-Type"] = "text/json"
    return resp


@app.route("/favorites")
@app.route("/favorites/")
@app.route("/favorites/<string:verb>/<int:asn>")
def favorites(verb=None, asn=None):
    result = []
    favorites = []
    try:
        favorites = json.load(open(FAVORITES_FULLPATH))
    except (ValueError, IOError) as e:
        print(("Ignoring %s with %s" % (e, FAVORITES_FULLPATH)))

    if verb is None:
        result = favorites
    elif verb == "add" and asn is not None:
        c = get_db().cursor()
        c.execute("""SELECT
                asn.countrycode,asn.friendlyname
            FROM asn
            WHERE asn.id = ?
            LIMIT 1""",
            (asn,))
        (cc, name) = c.fetchone()
        # TODO: dedupe ASN before append
        favorites.append({"cc": cc, "asn": asn, "name": name})
        json.dump(favorites, open(FAVORITES_FULLPATH, "w"))
        result = favorites
    elif verb == "remove" and asn is not None:
        found = False
        for i in range(len(favorites)):
            if favorites[i]["asn"] == asn:
                found = True
                break
        if found == True:
            del favorites[i]
        json.dump(favorites, open(FAVORITES_FULLPATH, "w"))
        result = favorites

    resp = Response(json.dumps(result))
    resp.headers['Content-Type'] = 'text/json'
    return resp


@app.route("/recalibrate/<string:verb>")
def recalibrate(verb):
    result = {}

    if verb == "execute":
        update_status_display("Recalibrating...\n")
        os.system("cd .. && /usr/bin/python3 calibrate.py")
        result["status"] = "recalibrated"
        result["data"] = json.load(open(LASTCALIBRATION_FULLPATH))
        update_status_display("Recalibrated.\n(reload ISP)")
    else:
        if os.path.isfile(LASTCALIBRATION_FULLPATH):
            try:
                result["data"] = json.load(open(LASTCALIBRATION_FULLPATH))
                result["status"] = "cached"
                result["whendt"] = int(os.stat(LASTCALIBRATION_FULLPATH).st_mtime)
            except json.decoder.JSONDecodeError:
                result["status"] = "uncalibrated"
        else:
            result["status"] = "uncalibrated"

    resp = Response(json.dumps(result))
    resp.headers['Content-Type'] = 'text/json'
    return resp


def get_apconfig():
    result = {}
    try:
        apconfig = json.load(open(APCONFIG_FULLPATH))
        result = apconfig
    except (ValueError, IOError) as e:
        print(("Ignoring %s with %s" % (e, APCONFIG_FULLPATH)))
    return result


class SemanticWiphyException(Exception):
    pass


def set_apconfig(raw_new_config):
    result = False
    try:
        new_config = json.loads(unquote(raw_new_config))
        if new_config["country_code"] != "US":
            raise Exception("AP country_code currently unsupported")
        # TODO (bug): this should check if it's valid for the
        #               channels in the requested regulatory domain,
        #               not the current one
        if int(new_config["channel"]) not in get_available_channels():
            raise SemanticWiphyException(
                    "dropping config for invalid channel")
        #TODO: more sanity checks
        json.dump(new_config, open(APCONFIG_FULLPATH, "w"))
        (_, hostapd_conf) = hostapconfgenerator.build_conf_file(new_config)
        open("/tmp/hostapd.conf", "w").write(hostapd_conf)
        os.system(HOSTAPD_RELOAD_FULLPATH)
        result = True
    except (ValueError, IOError, AttributeError, KeyError,
            SemanticWiphyException) as e:
        print(("Ignoring %s %s with %s" % (
            str(e.__class__), e, APCONFIG_FULLPATH)))
    return result


@app.route("/apconfig/<string:verb>/<string:params>")
@app.route("/apconfig/")
@app.route("/apconfig")
def apconfig(verb=None, params=None):
    result = {}
    if verb is None:
        result = get_apconfig()
    elif verb == "set":
        result["status"] = set_apconfig(params)

    resp = Response(json.dumps(result))
    resp.headers['Content-Type'] = 'text/json'
    return resp


@app.route('/i/<path:path>')
def send_static(path):
    return send_from_directory('i', path)


@app.route('/fonts/<path:path>')
def send_static2(path):
    return send_from_directory('fonts', path)


@app.route("/")
def index():
    return Response(open("search.html").readlines())


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
