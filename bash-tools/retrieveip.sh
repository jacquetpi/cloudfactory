#!/bin/bash
if [[ $1 =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9] ]]; 
then
    ip="$1"
else
    ip=$( virsh --connect=qemu:///system domifaddr "$1" | tail -n 2 | head -n 1 | awk '{ print $4 }' | sed 's/[/].*//' );
fi
echo "$ip"