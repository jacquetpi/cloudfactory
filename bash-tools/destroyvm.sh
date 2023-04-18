#!/bin/bash
pathbase="/var/lib/libvirt/images"
if (( "$#" != "1" )) 
then
  echo -n "Missing argument : ./destroyvm.sh name..."
  exit -1
fi
# Setup : clear old data
virsh --connect=qemu:///system destroy "$1"
virsh --connect=qemu:///system undefine "$1"
rm ${pathbase}/"$1".qcow2