#!/bin/bash
if (( "$#" != "3" ))
then
  echo "Missing argument : ./wp.sh vm timeout req/s"
  exit -1
fi
timeout="$2"
start=$( date +%s )
fullip=$( bash-tools/retrieveip.sh $1 )
if [[ ${fullip} == *":"* ]];
then
  ip=$(echo $fullip | cut -d : -f 1)
  port=$(echo $fullip | cut -d : -f 2)
else
  ip="$fullip"
  port="80"
fi
reqs="$3"
if [ "$reqs" -le "1" ]; then
  reqs="2"
fi
output=$( /usr/local/src/wrk2/wrk -t3 -c100 --latency -d "$timeout"s -R $reqs "http://$ip:$port" 2 >&1 )
epoch=$( date +%s%N )
fileoutput="${1}-${epoch}-wordpress.txt"
echo -n "$output" > "dump/${fileoutput}"
# Test if delay is needed (in case of unreachable service for example)
end=$( date +%s )
runtime=$((end-start))
if [ "$runtime" -le "$timeout" ]; then
  sleep=$((timeout-runtime))
  sleep "$sleep"
fi