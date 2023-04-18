#!/bin/bash
if (( "$#" != "1" )) 
then
  echo "treat-siege.sh Missing argument : ./treat-siege.sh folder"
  exit -1
fi
folder="$1"
header="index,vm,timestamp,availability,rate,failed,max,responsetime"
echo "$header" > output-siege.txt
index=0
for file in $(ls $folder/*-siege.txt); do
  index=$((index+1))
  xvm=$( echo "$file" | rev | cut -d"-" -f3- | cut -d"/" -f1 | rev )
  xtmp=$( echo "$file" | rev | cut -d"-" -f2-  | cut -d"-" -f1  | rev )
  xavl=$( grep 'Availability' "$file" | grep -Eo '[+-]?[0-9]+([.][0-9]+)?' )
  xrate=$( grep 'rate:' "$file" | grep -Eo '[+-]?[0-9]+([.][0-9]+)?' )
  xfail=$( grep 'Failed' "$file" | grep -Eo '[+-]?[0-9]+([.][0-9]+)?' )
  xmax=$( grep 'Longest' "$file" | grep -Eo '[+-]?[0-9]+([.][0-9]+)?' )
  xres=$( grep 'Response' "$file" | grep -Eo '[+-]?[0-9]+([.][0-9]+)?' )
  echo "$index,$xvm,$xtmp,$xavl,$xrate,$xfail,$xmax,$xres"  >> output-siege.txt
done