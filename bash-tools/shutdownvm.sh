#!/bin/bash
if (( "$#" != "1" )) 
then
  echo -n "Missing argument : ./startvm.sh name"
  exit -1
fi
# Retrieve schedprobe data if existing
vm_ip=$( virsh --connect=qemu:///system domifaddr "$1" | tail -n 2 | head -n 1 | awk '{ print $4 }' | sed 's/[/].*//' );
ssh vmtornado@"$vm_ip" -o StrictHostKeyChecking=no "systemctl --user stop schedprobe"
mkdir -p dump/latency
scp -o StrictHostKeyChecking=no vmtornado@"$vm_ip":src/schedprobe/*.csv dump/latency
# Exit
virsh --connect=qemu:///system shutdown "$1"
sleep 300
virsh --connect=qemu:///system destroy "$1"