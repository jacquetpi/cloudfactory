CloudFactory is a IaaS workload generator. Its goals is to generate representative workloads for simulators (such as CloudSimPlus) or for physical platforms (using bash scripts or CBTOOL)

CloudFactory is composed of two elements : 
- A library able to analyze a cloud dataset and generate a workload scenario. Its usage is illustrated in jupyter notebooks at folder root.
- A generator parsing a scenario and generating specified output (bash script, CloudSim scenario, CBTOOL scenario)

Details are available in the [associated paper](https://inria.hal.science/hal-04168667v1/document)

## Setup

```bash
apt-get update && apt-get install -y git python3 python3.venv
git clone https://github.com/jacquetpi/cloudfactory
cd cloudfactory/
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m generator --help
```

## Analyzer Example

We provide an example using Microsoft Azure public dataset in our notebook. To launch it:
```bash
source venv/bin/activate
jupyter notebook
```
Select `build_a_scenario.ipynb` and follow instructions

Generated statistics are described in two Yaml files : `scenario-vm-distribution.yml`(containing VM configuration options distribution) and `scenario-vm-usage.yml`(containing usage related metrics).  
Files can be passed to workload generator with its `--distribution=` and `--usage=` arguments.  
If not specified, generator will use `examples-scenario/scenario-vm-distribution.yml` and `examples-scenario/scenario-vm-usage.yml` values.

## Generator Example : CloudSimPlus

CloudFactory can generate a simulation scenario using CloudSimPlus.
Following example generates a default scenario targeting a workload with 256 cores and 512GB at its initialization phase.

```
python3 -m generator --cpu=256 --mem=512 --output=cloudsimplus
cloudsim_repo="/usr/local/src/cloudsimplus-examples"
mv CloudFactoryGeneratedWorkload.java "$cloudsim_repo"/src/main/java/org/cloudsimplus/examples/
mv *.properties "$cloudsim_repo"
cd "$cloudsim_repo"
mvn clean install
java -cp target/cloudsimplus-examples-*-with-dependencies.jar org.cloudsimplus.examples.CloudFactoryGeneratedWorkload
```
Refer to CloudSimPlus example [repository](https://github.com/cloudsimplus/cloudsimplus-examples) for more details

## Generator Example : Bash

Generate a bash IaaS workload by provisioning 10 VMs:

`python3 -m generator --vm=10 -t600,1800,36 --output=bash`

`t` or `--temporality` specify our virtual hours and days duration. Here, an `hour` lasts 600s, a `day` 1800s (`day` must be a multiple of `hour`). Our workload is composed of 36 virtual `days`

While we provide bash scripts to generate a given workload, VM template are user dependant.
To quickly setup environments, we rely on pre-built qcow2 images with ssh-keys installed.

In the basic implementation, 3 different images are used:

- A baseline image, with stressng, docker and a non-deployed DeathStarbench environment
- PostgresQL image installed with a TPC-C schema
- Wordpress image

The baseline image is used for different workloads (idle, stressng, Deathstarbench) as installation scripts are different between workload.

Values passed to programs are adapted from CloudFactory generated CPU usage.
Conversion is approximative and may be customised using `examples-workload\scenario-vm-workload.yml`

## Generator Example : CBTOOL

More complex deployments can be managed with CBTOOL deployments.
Following example generates a CBTOOL compatible scenario, running on its simulation mode, which can be adapted to others cloud deployments.

```
python3 -m generator --cpu=256 --mem=512 --output=cbtool
cbtool_repo="/usr/local/src/cbtool"
mv cloudfactory.cbtool "$cbtool_repo"
cd "$cbtool_repo"
cbtool/cb --trace=cloudfactory.cbtool
```
Refer to CBTOOL [repository](https://github.com/ibmcb/cbtool) for more details
