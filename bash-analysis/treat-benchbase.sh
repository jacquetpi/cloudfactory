#!/bin/bash
if (( "$#" != "1" )) 
then
  echo "treat-benchbase.sh Missing argument : ./treat-benchbase.sh folder"
  exit -1
fi
folder="$1"
header="index,timestamp,throughtput,goodput,average,maximum,median,minimum,25th,75th,90th,95th,99th"
echo "$header" > output-benchbase.txt
index=0
for file in $(ls $folder/tpcc-*/*.summary.json); do
  index=$((index+1))
  res=$( cat $file )
  xtmp=$( echo $res | jq '."Current Timestamp (milliseconds)"' )
  xthr=$( echo $res | jq '."Throughput (requests/second)"' )
  xgp=$( echo $res | jq '."Goodput (requests/second)"' )
  xavg=$( echo $res | jq '."Latency Distribution"."Average Latency (microseconds)"' )
  xmax=$( echo $res | jq '."Latency Distribution"."Maximum Latency (microseconds)"' )
  xmed=$( echo $res | jq '."Latency Distribution"."Median Latency (microseconds)"' )
  xmin=$( echo $res | jq '."Latency Distribution"."Minimum Latency (microseconds)"' )
  x25=$( echo $res | jq '."Latency Distribution"."25th Percentile Latency (microseconds)"' )
  x75=$( echo $res | jq '."Latency Distribution"."75th Percentile Latency (microseconds)"' )
  x90=$( echo $res | jq '."Latency Distribution"."90th Percentile Latency (microseconds)"' )
  x95=$( echo $res | jq '."Latency Distribution"."95th Percentile Latency (microseconds)"' )
  x99=$( echo $res | jq '."Latency Distribution"."99th Percentile Latency (microseconds)"' )
  echo "$index,$xtmp,$xthr,$xgp,$xavg,$xmax,$xmed,$xmin,$x25,$x75,$x90,$x95,$x99"  >> output-benchbase.txt
done