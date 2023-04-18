#!/bin/bash
if (( "$#" != "4" ))
then
  echo "deduct-min.sh Missing argument : ./deduct-min.sh label dataset vm start"
  echo "Example ./deduct-min.sh static azure 1000 20"
  exit -1
fi
cpu_config="64"
mem_config="256"
label="$1"
dataset="$2"
vm="$3"
host_count="$4"
while :
do
  #echo "Exp $label-$dataset-$vm : Trying with $host_count"
  java -cp /usr/local/src/cloudsimplus-examples/target/cloudsimplus-examples-*-with-dependencies.jar org.cloudsimplus.examples.CloudFactoryGeneratedWorkload "$host_count" "$cpu_config" "$mem_config" > temp
  if ! grep -q 'No suitable host found' temp; then
    # Everything went fine
    #echo "Exp $label-$dataset-$vm : Match with $host_count"
    mv temp "solution-$label-$dataset-$vm.txt"
    break
  fi
  host_count=$(( host_count + 1 ))
done
echo "$host_count"
