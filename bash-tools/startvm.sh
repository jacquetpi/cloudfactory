#!/bin/bash
if (( "$#" != "2" )) 
then
  echo -n "Missing argument : ./startvm.sh name image"
  exit -1
fi
virsh --connect=qemu:///system start "$1"
# We only leave this script when VM is operational
while sleep 15;
do
  vm_ip=$( virsh --connect=qemu:///system domifaddr "$1" | tail -n 2 | head -n 1 | awk '{ print $4 }' | sed 's/[/].*//' );
  if [ -n "$vm_ip" ]; then #VAR is set to a non-empty string
    break
  fi
done
# May not be fully initialized : test if ssh works (is ping enough?)
count=0
while true;
do
  ssh_test=$( ssh vmtornado@"${vm_ip}" -o StrictHostKeyChecking=no 'echo success' )
  if [[ $ssh_test == *"success"* ]]; then
    echo "Setup : vm $1 ready with ip $vm_ip"
    break
  fi
  count=$(( count + 1 ))
  echo "Start : unable to ssh test vm $1 with ip $vm_ip (trial $count)"
  sleep 15
done
# Post init step
# DSB
if [[ "$2" = "dsb" ]]; then
  ssh vmtornado@"${vm_ip}" -o StrictHostKeyChecking=no "cd /usr/local/src/DeathStarBench-master/socialNetwork/ && docker-compose down && docker-compose up -d"
fi
# Wordpress
if [[ "$2" = "wordpress" ]]; then
  payload="sleep 900 && ./changewpip.sh ${vm_ip}"
  if [[ ${fullip} != *":"* ]];
  then
    payload="$payload && sudo firewall-cmd --zone=public --add-port=80/tcp --permanent && sudo firewall-cmd --reload"
  fi
  ssh vmtornado@"${vm_ip}" -o StrictHostKeyChecking=no "$payload"
fi