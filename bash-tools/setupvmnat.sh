#!/bin/bash
if (( "$#" != "3" )) 
then
  echo "Missing argument : ./setupvmnat.sh vm workload hostport"
  exit -1
fi
sport="$3"
while true;
do
  vm_ip=$( virsh --connect=qemu:///system domifaddr "$1" | tail -n 2 | head -n 1 | awk '{ print $4 }' | sed 's/[/].*//' );
  if [ -n "$vm_ip" ]; then #VAR is set to a non-empty string
    break
  fi
  sleep 10
done
case $2 in
  "idle" | "stressng")
    dport="22"
    ;;
  "wordpress")
    dport="$sport"
    # Supplementary step : 
    ssh vmtornado@"${vm_ip}" -o StrictHostKeyChecking=no "./changewpip.sh ${vm_ip}:${sport}"
    ;;
  "dsb")
    dport="8080"
    ;;
  "tpcc" | "tpch")
    dport="5432"
    ;;
  *)
    echo -n "setupvmnat.sh : unknow workload $2 for $1"
    exit -1
    ;;
esac
echo "setup nating for $1 on port ${sport} for $vm_ip:$dport on workload $2"
sudo firewall-cmd --add-forward-port=port=${sport}:proto=tcp:toaddr=$vm_ip:toport=$dport
# cancel with:  sudo firewall-cmd --reload