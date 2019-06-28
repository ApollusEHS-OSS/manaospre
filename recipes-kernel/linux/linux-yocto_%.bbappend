FILESEXTRAPATHS_prepend := "${THISDIR}/files:"
SRC_URI += " file://defconfig"
# netfilter is enabled in the config; this feature causes it to
#  only be built as a module (and iptable_mangle.ko isn't included
#  in the image for some reason)
KERNEL_FEATURES_remove = "features/netfilter/netfilter.scc"
