#!/bin/bash
if (( "$#" != "5" ))
then
  echo "cluster-sizing-exp.sh Missing argument : ./cluster-sizing-exp.sh label dataset vm starting_host max"
  echo "Example ./cluster-sizing-exp.sh dynamic chameleon 10 1 1000"
  exit -1
fi
label="$1"
dataset="$2"
vm="$3"
prev="$4"
max="$5"
echo "label,dataset,vm,host" > output.csv
while :
do
  echo "overall: Launching with $vm"
  python3 -m generator --distribution=examples-data/scenario-vm-distribution-"$dataset".yml --usage=examples-data/scenario-vm-usage-"$label".yml --vm="$vm" --output=cloudsimplus --temporality=360,8640,7 --export="experiment-$label-$dataset-$vm.txt"
  prev=$( source examples-data/deduct-min.sh "$label" "$dataset" "$vm" "$prev" )
  echo "overall: found min with $prev"
  echo "$label,$dataset,$vm,$prev" >> output.csv
  vm=$(( vm + 10 ))
  if [ "$vm" -gt "$max" ]; then
    echo "overall: ending"
    break
  fi
done
