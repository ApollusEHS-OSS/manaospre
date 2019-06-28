import os, json, ipaddress
import sqlite3

SHAPING_DB_FULLPATH = "/tmp/shaping.db"

MARK_LIST = {
    "aws": 2,
    "akam": 3,
    "oc": 4
}

NETWORK_CONFIG = {
    "aws": {"classid": "1:2", "handle": "12", "avglatency": 168},
    "akam": {"classid": "1:3", "handle": "13", "avglatency": 72},
    "oc": {"classid": "1:4", "handle": "14", "avglatency": 8},
}


def get_netblocks():
    db = sqlite3.connect(SHAPING_DB_FULLPATH)
    c = db.cursor()
    c.execute("""SELECT rsc.shortcode,r.prefix FROM route r JOIN routeshortcode rsc ON r.shortcodeid = rsc.id""")
    result = { "aws": [], "akam": [], "oc": [] }
    for row in c.fetchall():
        result[row[0]].append(row[1])
    return result


def get_shape(asn):
    raise Exception("Unimplemented")
    return False

def generate_tc_commands(shape, netblocks):
    base_command = "sudo tc"

    # TODO: setup ingress filter
    # emit the root / default ingress packet rule:
    print("%s qdisc del dev ifb0 root 2>/dev/null" % (base_command))
    print("%s qdisc add dev ifb0 root handle 1: htb" % (base_command))
    for network_short_name, disposition in shape.items():
        assert("netemliteral" in disposition)
        assert(network_short_name in netblocks)
        print("%s class add dev ifb0 parent 1: classid %s htb rate 100Mbit" % (
            base_command,
            NETWORK_CONFIG[network_short_name]["classid"]))
        # TODO: adjust for static latency
        # TODO: measure static latency!
        # TODO: better checking for disposition variables
        print("%s qdisc add dev ifb0 parent %s handle %s: netem delay %s loss %s" % (
            base_command,
            NETWORK_CONFIG[network_short_name]["classid"],
            NETWORK_CONFIG[network_short_name]["handle"],
            disposition["netemliteral"]["delay"],
            disposition["netemliteral"]["loss"]))

    # separate with a newline
    print("# filters next")

    # add the filter rules assigning packets to queuing disciplines
    for network_short_name, netblock_list in netblocks.items():
        for netblock in netblock_list:
            #print(network_short_name, netblock)
            parsed_netblock = ipaddress.ip_network(netblock)
            # TODO: proper split on ipv6 / ipv4
            if parsed_netblock.version == 4:
                cmd = "%s filter add dev ifb0 protocol ip u32 match ip src %s classid %s" % (
                    base_command,
                    netblock,
                    NETWORK_CONFIG[network_short_name]["classid"]
                )
                print(cmd)

def generate_iptables_marks(netblocks):
    # flush all mangle rules
    print("sudo iptables -t mangle -F")
    print("sudo ip6tables -t mangle -F")

    # first flush the tables
    for network_short_name in MARK_LIST.keys():
        for base_command in ["sudo iptables", "sudo ip6tables"]:
            cmd = "%s -t mangle -D %s" % (base_command, network_short_name)
            print(cmd)  # need to ignore output here
            cmd = "%s -t mangle -N %s" % (base_command, network_short_name)
            print(cmd)  # need to ignore output here
            cmd = "%s -t mangle -F %s" % (base_command, network_short_name)
            print(cmd)

    # fill the tables for marking packets
    for network_short_name, netblock_list in netblocks.items():
        for netblock in netblock_list:
            parsed_netblock = ipaddress.ip_network(netblock)
            cmd = "sudo "
            if parsed_netblock.version == 4:
                cmd += "iptables "
            elif parsed_netblock.version == 6:
                cmd += "ip6tables "
            else:
                raise Exception("Unknown IP protocol")
            #cmd += "-t mangle -A %s -s %s -jMARK --set-mark %d" % (
            cmd += "-t mangle -A %s -d %s -jMARK --set-mark %d" % (
                    network_short_name, netblock, MARK_LIST[network_short_name])
            print(cmd)

    # add the jump commands to start packet processing:
    for network_short_name in MARK_LIST.keys():
        for base_command in ["sudo iptables", "sudo ip6tables"]:
            cmd = "%s -t mangle -A PREROUTING -j%s" % (base_command, network_short_name)
            print(cmd)

api_netblocks = get_netblocks()
generate_iptables_marks(api_netblocks)

# TODO: merge this with zeroshaping.sh or the last selected shape
api_shape = {"oc": {"netemliteral": {"delay": "0ms", "loss": "0%"}}, "aws": {"netemliteral": {"delay": "0ms", "loss": "0%"}}, "akam": {"netemliteral": {"delay": "0ms", "loss": "0%"}}}
generate_tc_commands(api_shape, api_netblocks)
