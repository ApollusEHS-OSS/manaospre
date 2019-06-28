from lcdproc.server import Server
import time, os, json, sqlite3

NETWORK_CONFIG = {
    "aws": {"classid": "1:2", "handle": "12"},
    "akam": {"classid": "1:3", "handle": "13"},
    "oc": {"classid": "1:4", "handle": "14"}
}

SHAPING_DB_FULLPATH = "/tmp/shaping.db"
FAVORITES_FULLPATH = "/tmp/favorites.json"
LASTCALIBRATION_FULLPATH = "/tmp/lastcalibration.json"
LASTDISPLAY_FULLPATH = "/tmp/lastdisplay.txt"

db = sqlite3.connect(SHAPING_DB_FULLPATH)

def get_favorites():
    favorites = []
    try:
        favorites = json.load(open(FAVORITES_FULLPATH, "r"))
    except (ValueError, IOError) as e:
        #print("Error reading favorites %s: %s" % (e, FAVORITES_FULLPATH))
        pass
    return favorites

def update_display(line1Widget, line2Widget, ispOffset):
    global db
    favorites = get_favorites()

    if ispOffset < 0 or ispOffset >= len(favorites):
        line1Widget.set_text("Please setup")
        line2Widget.set_text(" favorites")
    else:
        asn = int(favorites[ispOffset]["asn"])
        isp_text = "ISP:%s/%s" % (favorites[ispOffset]["cc"], favorites[ispOffset]["name"])
        line1Widget.set_text(isp_text)
        c = db.cursor()
        c.execute("""SELECT
                awsdelay,awsloss,akamdelay,akamloss,ocdelay,ocloss,friendlyname,countrycode
                FROM shape LEFT JOIN asn ON shape.asn = asn.id
                WHERE asn = ? LIMIT 1""", (asn,))
        shape = c.fetchone()
        if shape is not None:
            shape_text = "%d/%d %d/%d %d/%d" % (shape[0], shape[1], shape[2], shape[3], shape[4], shape[5])
            line2Widget.set_text(shape_text)
            with open(LASTDISPLAY_FULLPATH, "w") as f:
                f.write("%s\n%s" % (isp_text, shape_text))

def update_shaping(lastCalibration, ispOffset):
    global db
    favorites = get_favorites()

    if ispOffset >= 0 and ispOffset < len(favorites):
        asn = int(favorites[ispOffset]["asn"])
        c = db.cursor()
        c.execute("""SELECT
                awsdelay,awsloss,akamdelay,akamloss,ocdelay,ocloss,friendlyname,countrycode
                FROM shape LEFT JOIN asn ON shape.asn = asn.id
                WHERE asn = ? LIMIT 1""", (asn,))
        shape = c.fetchone()
        if shape is not None:
            shapeStructured = {
                "aws": {
                    "avglatency": shape[0],
                    "loss": shape[1]
                },
                "akam": {
                    "avglatency": shape[2],
                    "loss": shape[3]
                },
                "oc": {
                    "avglatency": shape[4],
                    "loss": shape[5]
                }
            }

            for shortcode in ["aws", "akam", "oc"]:
                avglatency = shapeStructured[shortcode]["avglatency"]
                avglatency -= lastCalibration[shortcode]

                if avglatency < 0:
                    avglatency = 1

                cmd = "sudo tc qdisc replace dev ifb0 parent %s handle %s: netem delay %dms loss %s" % (
                        NETWORK_CONFIG[shortcode]["classid"],
                        NETWORK_CONFIG[shortcode]["handle"],
                        avglatency,
                        shapeStructured[shortcode]["loss"]
                        )
                #print(cmd)
                os.system(cmd)

def sanity_check_calibration(calibration):
    # TODO: write more of this
    for shortcode in ["aws", "akam", "oc"]:
        if shortcode not in calibration:
            calibration[shortcode] = 0


def get_calibration():
    last_calibration = {"aws": 0, "akam": 0, "oc": 0}
    try:
        last_calibration = json.load(open(LASTCALIBRATION_FULLPATH, "r"))
    except (ValueError, IOError) as e:
        #print("Error reading last calibration %s: %s" % (e, LASTCALIBRATION_FULLPATH))
        pass
    sanity_check_calibration(last_calibration)
    return last_calibration

def main():
    current_isp_index = 0

    try:
        lcd = Server("localhost", debug=False)
        lcd.start_session()

        sc = lcd.add_screen("home")
        sc.set_heartbeat("off")
        sc.set_duration(10)

        line1 = sc.add_string_widget("Line1Widget", text="Init...", x=1, y=1)
        line2 = sc.add_scroller_widget("Line2Widget", text="", speed=6, top=2, right=16)

        last_calibration = get_calibration()

        update_display(line1, line2, current_isp_index)
        update_shaping(last_calibration, current_isp_index)

        lcd.add_key("Down")
        lcd.add_key("Up")


        last_update_time = time.time()
        while(True):
            key = lcd.poll()
            if key is not None:
                favorites = get_favorites()
                if key == "key Down\n":
                    current_isp_index += 1
                    if current_isp_index == len(favorites):
                        current_isp_index = 0
                elif key == "key Up\n":
                    current_isp_index -= 1
                    if current_isp_index < 0:
                        current_isp_index = len(favorites) - 1
                else:
                    print(("Unknown key: ", key))
                update_display(line1, line2, current_isp_index)
                # reload the calibration, in case it has updated
                last_calibration = get_calibration()
                update_shaping(last_calibration, current_isp_index)
                last_update_time = time.time()
            # watch for file changes on LASTDISPLAY_FULLPATH
            elif os.path.isfile(LASTDISPLAY_FULLPATH) and os.stat(LASTDISPLAY_FULLPATH).st_mtime > last_update_time:
                last_update_time = time.time()
                with open(LASTDISPLAY_FULLPATH) as f:
                    line1.set_text(f.readline().split("\n")[0])
                    line2.set_text(f.readline().split("\n")[0])

            time.sleep(0.2)
    except ConnectionRefusedError:
        print("display: problem connecting to lcdproc, shutting down")

if __name__ == "__main__":
    main()
