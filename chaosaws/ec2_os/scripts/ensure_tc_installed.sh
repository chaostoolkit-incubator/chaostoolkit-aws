#!/bin/bash

if [ -z "`rpm -qa iproute-tc`" ]; then
    yum install -y iproute-tc 2>&1 >/dev/null
fi

if [ $? -ne 0 ];then
    echo "Install iproute-tc package failed."
    exit 1
fi