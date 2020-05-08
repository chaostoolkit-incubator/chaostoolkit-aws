
ret=$?
if [ $ret -eq 0 ]; then
    echo "experiment run_cmd -> <$instance_id>: success"
else
    echo "experiment run_cmd -> <$instance_id>: fail"
fi