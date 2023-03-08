## Example

`python3 -m cloudfactory -c 256 -m 512 -a 0.07 -d 0.0 -s -w600,1800,36`

Generate a IaaS workload starting close to 256 `cpu` (in total) and 512 go of `memory` (in total) based on Azure IaaS VM size distribution.  
> Exact sum may not be match due to the constraints applied.  

`Arrival rate` is 7%, `departure rate` is 0% (increasing workload only)  
`s` or `--setup` specify that bash scripts are to be generated  
`w` or `--workload` specify our virtual hours and days duration. Here, an `hour` lasts 600s, a `day` 1800s (`day` must be a multiple of `hour`). Our workload is composed of 36 virtual `hours`