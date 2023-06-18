#!/bin/bash
if (( "$#" != "3" )) 
then
  echo "siege.sh Missing argument : ./siege.sh vm timeout concurrent"
  exit -1
fi
start=$( date +%s )
timeout="$2"
concurrent="$3"
fullip=$( bash-tools/retrieveip.sh $1 );
sed -i -- "s/true/false/g" ${HOME}/.siege/siege.conf
output=$( siege --time="$timeout"s --concurrent="$concurrent" --delay=1 http://${fullip}/ 2>&1 )
epoch=$( date +%s%N )
fileoutput="${1}-${epoch}-siege.txt"
echo -n "$output" > "dump/${fileoutput}"
# Test if delay is needed (in case of unreachable service for example)
end=$( date +%s )
runtime=$((end-start))
if [ "$runtime" -le "$timeout" ]; then
  sleep=$((timeout-runtime))
  sleep "$sleep"
fi

