#!/bin/bash

if [ -z "$process_name" ]; then
    echo "Please provide process name."
    exit 1
fi

experiment=$(kill $signal $process_name)
ret=$?
if [ $ret -eq 0 ]; then
    echo "experiment kill_process -> process <$process_name> on <$instance_id>: success"
else
    echo "experiment kill_process -> process <$process_name> on <$instance_id>: fail"
fi
#Sleep $duration
sleep $duration
