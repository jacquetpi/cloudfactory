#!/bin/bash
if (( "$#" != "1" )) 
then
  echo -n "Missing argument : ./startvm.sh name"
  exit -1
fi
# Exit
virsh --connect=qemu:///system shutdown "$1"
sleep 300
virsh --connect=qemu:///system destroy "$1"