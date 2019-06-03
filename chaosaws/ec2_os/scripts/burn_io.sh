#Script for BurnIO Chaos Monkey

cat << EOF > /tmp/loop.sh
while [ true ];
do
    sudo dd if=/dev/urandom of=/root/burn bs=32K count=1024 iflag=fullblock
done
EOF

chmod +x /tmp/loop.sh
timeout --preserve-status $duration /tmp/loop.sh

# while true;
# do
#     dd if=/dev/urandom of=/experiment_burnio bs=1M count=1024 iflag=fullblock status=none
# done &

ret=$?
if [ $ret -eq 0 ]; then
    echo "experiment burnio -> <$instance_id>: success"
else
    echo "experiment brunio -> <$instance_id>: fail"
fi

sudo rm /root/burn
sudo rm /tmp/loop.sh
