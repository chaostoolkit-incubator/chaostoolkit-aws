#!/bin/bash

if [ -n "`rpm -qa iproute-tc`" ]; then
    yum remove -y iproute-tc 2>&1 >/dev/null
fi

ret3=$?
if [ $ret3 -ne 0 ];then
    echo "Remove iproute-tc package failed."
    exit 1
fi