#!bin/bash

ps -ef | grep $process_name | grep -v 'grep' | awk '{ print $2 }'