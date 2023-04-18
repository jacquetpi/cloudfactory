#!/bin/bash
fullip=$( tools/retrieveip.sh $1 );
if [[ ${fullip} == *":"* ]];
then
  ip=$(echo $fullip | cut -d : -f 1)
  port=$(echo $fullip | cut -d : -f 2)
else
  ip="$fullip"
  port="22"
fi
output=$( ssh vmtornado@"${ip}" -p "$port" -o StrictHostKeyChecking=no "$2" 2>&1 )
epoch=$( date +%s%N )
fileoutput="${1}-${epoch}-ssh.txt"
echo -n "$output" > "dump/${fileoutput}"
