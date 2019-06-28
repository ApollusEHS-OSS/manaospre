#!/bin/sh

sudo tc qdisc replace dev ifb0 parent 1:2 handle 12: netem delay 0ms
sudo tc qdisc replace dev ifb0 parent 1:3 handle 13: netem delay 0ms
sudo tc qdisc replace dev ifb0 parent 1:4 handle 14: netem delay 0ms
