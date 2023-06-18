#!/bin/bash
if (( "$#" != "3" )) 
then
  echo "Missing argument : ./dsb.sh vm timeout rq/s"
  exit -1
fi
start=$( date +%s )
timeout="$2"
fullip=$( bash-tools/retrieveip.sh $1 );
if [[ ${fullip} == *":"* ]];
then
  ip=$(echo $fullip | cut -d : -f 1)
  port=$(echo $fullip | cut -d : -f 2)
else
  ip="$fullip"
  port="8080"
fi
reqs="$3"
if [ "$reqs" -le "1" ]; then
  reqs="2"
fi
output=$( sudo docker run --rm --net=host pjacquet/dsb-socialnetwork-wrk2 -D exp -t 2 -c 20 -d "$timeout" -L -s ./scripts/social-network/read-home-timeline.lua http://"${ip}":"${port}"/wrk2-api/home-timeline/read -R $reqs 2>&1 )
epoch=$( date +%s%N )
fileoutput="${1}-${epoch}-dsb.txt"
echo -n "$output" > "dump/${fileoutput}"
# Test if delay is needed (in case of unreachable service for example)
end=$( date +%s )
runtime=$((end-start))
if [ "$runtime" -le "$timeout" ]; then
  sleep=$((timeout-runtime))
  sleep "$sleep"
fi