# Script for NetworkLatency Chaos Monkey

# Adds ${delay}ms +- ${jitter}ms of latency to each packet for $duration seconds
sudo tc qdisc add dev eth0 root netem delay ${delay}ms ${jitter}ms
sleep $duration
sudo tc qdisc del dev eth0 root




