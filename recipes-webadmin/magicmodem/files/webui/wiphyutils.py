from os import popen
import re

IW_LIST_CMD = "/sbin/iw list"

# TODO: This is based on current regulatory domain; allow
#       lookups to others (parse regulatory.db?)
# TODO: Parse regulatory.db or change domain and parse rtnetlink
#       nl80211 NL80211_CMD_GET_WIPHY response instead
def get_iw_list():
    result = ""
    try:
        with popen(IW_LIST_CMD) as f:
            result = f.readlines()
    except IOError as e:
        pass
    return result

def get_available_channels():
    output = get_iw_list()
    channels = []
    freq_line_match = re.compile(
            "^\t\t\t\* [0-9]{4,} MHz \[([0-9]{1,})\] \((.*)\).*$")

    try:
        for i in range(len(output)):
            m = freq_line_match.split(output[i])
            if m is not None and len(m) == 4:
                (_, channel_text, max_tx_power, _) = m
                if max_tx_power != "disabled":
                    channel = int(channel_text)
                    # drop the channels >=32 (5GHz)
                    if channel < 32:
                        channels.append(channel)
    except ValueError as e:
        pass
    return channels

if __name__ == "__main__":
    print(get_available_channels())
