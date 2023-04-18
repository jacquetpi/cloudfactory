#!/bin/bash
if (( "$#" != "3" ))
then
  echo "Missing argument : ./tpcc.sh vm timeout rq/s"
  exit -1
fi
timeout="$2"
start=$( date +%s )
random_input=$( tr -dc A-Za-z0-9 </dev/urandom | head -c 13 ; echo '' )
config_file="/tmp/benchbase-${random_input}.xml"
fullip=$( tools/retrieveip.sh $1 );
if [[ ${fullip} == *":"* ]];
then
  ip=$(echo $fullip | cut -d : -f 1)
  port=$(echo $fullip | cut -d : -f 2)
else
  ip="$fullip"
  port="5432"
fi
cp /usr/local/src/benchbase/config/postgres/sample_tpcc_config.xml "$config_file"
sed -i -- "s/localhost:5432/${ip}:"${port}"/g" "$config_file"
sed -i -- "s/<time>60/<time>${timeout}/g" "$config_file"
sed -i -- "s/<rate>10000/<rate>${3}/g" "$config_file"
location=$( pwd )
cd /usr/local/src/benchbase
output=$( java -jar /usr/local/src/benchbase/target/benchbase-postgres/benchbase.jar -b tpcc -c "$config_file" -d /usr/local/src/vmworkload/dump/"tpcc-$1" --execute=true 2>&1 )
epoch=$( date +%s%N )
fileoutput="${1}-${epoch}-tpcc.txt"
cd "$location"
echo -n "$output" > "dump/${fileoutput}"
# Test if delay is needed (in case of unreachable service for example)
end=$( date +%s )
runtime=$((end-start))
if [ "$runtime" -le "$timeout" ]; then
  sleep=$((timeout-runtime))
  sleep "$sleep"
fi
