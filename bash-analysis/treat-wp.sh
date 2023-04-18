#!/bin/bash
if (( "$#" != "1" )) 
then
  echo "treat-wp.sh Missing argument : ./treat-dsb.sh folder"
  exit -1
fi
folder="$1"
header="index,vm,timestamp,50th,70th,80th,90th,95th,99th,unreach,reqs,timeout,timeoutratio"
echo "$header" > output-wp.txt
index=0
for file in $(ls $folder/*-wordpress.txt); do
  index=$((index+1))
  xvm=$( echo "$file" | rev | cut -d"-" -f3- | cut -d"/" -f1 | rev )
  xtmp=$( echo "$file" | rev | cut -d"-" -f2-  | cut -d"-" -f1  | rev )
  xmed=$( grep '0.500000' "$file" | tr -s " " | cut -c2- | cut -d' ' -f 1 )
  x70=$( grep '0.700000' "$file" | tr -s " " | cut -c2- | cut -d' ' -f 1 )
  x80=$( grep '0.800000' "$file" | tr -s " " | cut -c2- | cut -d' ' -f 1 )
  x90=$( grep '0.900000' "$file" | tr -s " " | cut -c2- | cut -d' ' -f 1 )
  x95=$( grep '0.950000' "$file" | tr -s " " | cut -c2- | cut -d' ' -f 1 )
  x99=$( grep '0.990625' "$file" | tr -s " " | cut -c2- | cut -d' ' -f 1 )
  reqs=$( grep 'requests in' "$file" | tr -s " " | cut -c2- | cut -d' ' -f 1 )
  timeout=$( grep 'timeout' $file | tr -s " " | rev | cut -d' ' -f 1 | rev )
  if [[ "$timeout" ]]
  then
    timeoutratio=$( python3 -c "print(${timeout}/${reqs})" )
  fi
  reachtest=$( grep 'unable to connect' "$file" )
  if [[ "$reachtest" ]]
  then
    unreach="1"
    timeoutratio="1"
  else
    unreach="0"
  fi
  echo "$index,$xvm,$xtmp,$xmed,$x70,$x80,$x90,$x95,$x99,$unreach,$reqs,$timeout,$timeoutratio"  >> output-wp.txt
done
