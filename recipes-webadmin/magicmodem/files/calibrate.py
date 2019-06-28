import json, os
from statistics import mean, stdev

MAX_DEVIATION_PER_SHORTCODE_MS = 500

LASTCALIBRATION_FULLPATH = "/tmp/lastcalibration.json"

URLLIST_STATIC = """{
    "aws": ["api-global.netflix.com"],
    "akam": ["secure.netflix.com", "cdn0.nflximg.net"],
    "oc": ["fast.com"]
}"""

def zero_shaping():
    parent_handle_list = [
            ("1:2", 12),
            ("1:3", 13),
            ("1:4", 14)
        ]
    
    for parent_handle in parent_handle_list:
        cmd = "sudo tc qdisc replace dev ifb0 parent %s handle %s: netem delay 0ms" % (parent_handle[0], parent_handle[1])
        os.system(cmd)

# check agreement, take the highest in each class
def calculate_calibration_latency(shortcode_url_avg_entries):
    shortcode_avg_map = dict()
    for entry in shortcode_url_avg_entries:
        if entry[0] not in shortcode_avg_map:
            shortcode_avg_map[entry[0]] = []
        shortcode_avg_map[entry[0]].append(entry[2])

    final_calibration = dict()
    for shortcode in list(shortcode_avg_map.keys()):
        averages = shortcode_avg_map[shortcode]
        if len(averages) < 2:
            (mean_shortcode, stdev_shortcode, max_shortcode) = (averages[0], averages[0], averages[0])
        else:
            (mean_shortcode, stdev_shortcode, max_shortcode) = (mean(averages), stdev(averages), max(averages))

        if stdev_shortcode > MAX_DEVIATION_PER_SHORTCODE_MS:
            # TODO: find a better alert for the user that the calibration failed
            print(Exception("measurements for %s don't agree (stdev: %d, rtts: %s)" % (
                shortcode, stdev_shortcode, json.dumps(averages))))
            mean_shortcode = 0.0
        final_calibration[shortcode] = int(mean_shortcode + 0.5)

    # TODO: make sure everything is in final_calibration before writing it out
    try:
        json.dump(final_calibration, open(LASTCALIBRATION_FULLPATH, "w"))
    except IOError as e:
        print(("Ignoring %s with %s" % (e, LASTCALIBRATION_FULLPATH)))

def main():
    #urllist = json.load(open("urllist.json", "r"))
    urllist = json.loads(URLLIST_STATIC)
    url_to_shortcode_map = dict()
    for shortcode in ["aws", "akam", "oc"]:
        assert(shortcode in urllist)
        for url in urllist[shortcode]:
            url_to_shortcode_map[url] = shortcode

    zero_shaping()
    ordered_urls = list(url_to_shortcode_map.keys())
    cmd = "/usr/bin/nping --unprivileged --tcp-connect -p 443 --flags rst %s" % (" ".join(ordered_urls))

    cmd_output = os.popen(cmd).readlines()

    # use a line counter for lookahead parsing:
    current_line_num = 0
    reassembled_shortcode_url_avg = list()
    for current_line_num in range(len(cmd_output)):
        line = cmd_output[current_line_num]
        if line.startswith("Statistics for host "):
            average_rtt = int(float(cmd_output[current_line_num + 2].split(":")[3].split("ms")[0]) + 0.5)
            hostname = line.split(" ")[3]
            reassembled_shortcode_url_avg.append((url_to_shortcode_map[hostname], hostname, average_rtt))
    calculate_calibration_latency(reassembled_shortcode_url_avg)


if __name__ == "__main__":
    main()
