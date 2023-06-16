#!/bin/bash
pathbase="/var/lib/libvirt/images"
if (( "$#" != "4" )) 
then
  echo -n "Missing argument : ./setupvm.sh name core mem image"
  exit -1
fi
image=""
case $4 in
  "idle" | "stressng" | "dsb")
    image="${pathbase}/baseline-ubuntu20-04.qcow2"
    ;;

  "wordpress")
    image="${pathbase}/baseline-ubuntu20-04-wp.qcow2"
    ;;

  "tpcc")
    image="${pathbase}/baseline-ubuntu20-04-tpcc.qcow2"
    ;;

  "tpch")
    image="${pathbase}/baseline-ubuntu20-04-tpch.qcow2"
    ;;

  *)
    echo -n "Unknow image $4 for $1"
    exit -1
    ;;
esac

# Setup : clear old data
virsh --connect=qemu:///system destroy "$1"
virsh --connect=qemu:///system undefine "$1"
# Setup : install data
rsync -avhW --no-compress --progress --info=progress2 "$image" "$pathbase"/"$1".qcow2
virt-install --connect qemu:///system --import --name "$1" --vcpu "$2" --memory "$3" --disk ${pathbase}/"$1".qcow2,format=qcow2,bus=virtio --import --os-variant ubuntu20.04 --network default --virt-type kvm --noautoconsole --check path_in_use=off
# Setup : statistics
virsh --connect qemu:///system dommemstat "$1" --period 1
# Setup : core pining
# for ((vcpu=0;vcpu<"$2";vcpu++)); do
#     virsh --connect=qemu:///system vcpupin "$1" --vcpu "${vcpu}" 1-3
# done
virsh --connect=qemu:///system vcpupin "$1"

# Post action : wait to retrieve vm ip
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
  echo "Setup : unable to ssh test vm $1 with ip $vm_ip (trial $count)"
  sleep 15
done
# Post action : test if needed
if [ "$4" = "idle" ] || [ "$4" = "stressng" ] || [ "$4" = "tpcc" ] || [ "$4" = "tpch" ];
then
    echo -n "No post action required for $1 on workload $4"
    exit 0
fi
# Post action : Execute
case $4 in
  "wordpress")
    payload="sleep 300 && ./changewpip.sh ${vm_ip}"
    if [[ ${fullip} != *":"* ]];
    then
      payload="$payload && sudo firewall-cmd --zone=public --add-port=80/tcp --permanent && sudo firewall-cmd --reload"
    fi
    ;;
  "dsb")
    payload="sleep 300 && cd /usr/local/src/DeathStarBench-master/socialNetwork/ && docker-compose up -d && sleep 60 && python3 scripts/init_social_graph.py --graph=socfb-Reed98"
    ;;
  *)
    echo -n "Unknow execute action : $4, internal error on $1"
    exit -1
    ;;
esac
ssh vmtornado@"${vm_ip}" -o StrictHostKeyChecking=no "$payload"
echo -n "Post install action executed for $1 on workload $4"

