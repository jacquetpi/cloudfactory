import yaml
import pandas as pd
import numpy as np

def build_cpu_and_mem_distribution_dataframes(trace_df : pd.DataFrame,
                            col_flavor_cpu : str = 'vmcorecount', col_flavor_mem : str = 'vmmemory',
                            col_vm_created : str = 'vmcreated', col_vm_deleted : str = 'vmdeleted',
                            timestamp_begin : int = None, timestamp_end : int = None, timestamp_step : int = 3600 ):
    
    if timestamp_begin is None: timestamp_begin = trace_df[col_vm_created].min()
    if timestamp_end is None: timestamp_end = trace_df[col_vm_created].max()

    keys_core, core_values_per_key = __init_values_per_key(trace_df, col_flavor_cpu)
    keys_mem, mem_values_per_key = __init_values_per_key(trace_df, col_flavor_mem)

    considered_timestamps = list()
    for timestamp in range(timestamp_begin, timestamp_end, timestamp_step):
    
        # Dataset containing all VM alive in current range (deleted after min, created before max)
        filtered_by_aliveness = trace_df.loc[(trace_df[col_vm_deleted] >= (timestamp)) & (trace_df[col_vm_created] <= (timestamp+timestamp_step) )]

        __add_to_result_dict_observed_freq(alive_df=filtered_by_aliveness, metric=col_flavor_cpu, metric_keys=keys_core, result_dict=core_values_per_key)
        __add_to_result_dict_observed_freq(alive_df=filtered_by_aliveness, metric=col_flavor_mem, metric_keys=keys_mem, result_dict=mem_values_per_key)
        considered_timestamps.append(timestamp)

    core_values_per_key['timestamp'] = considered_timestamps
    mem_values_per_key['timestamp'] = considered_timestamps
    
    return pd.DataFrame(core_values_per_key), pd.DataFrame(mem_values_per_key)
    
    
def get_cpu_and_mem_average_distribution(trace_df : pd.DataFrame,
                            col_flavor_cpu : str = 'vmcorecount', col_flavor_mem : str = 'vmmemory',
                            col_vm_created : str = 'vmcreated', col_vm_deleted : str = 'vmdeleted',
                            timestamp_begin : int = None, timestamp_end : int = None, timestamp_step : int = 3600 ):
    
    cpu_timestamped_df, mem_timestamped_df = build_cpu_and_mem_distribution_dataframes(trace_df=trace_df,
                                        col_flavor_cpu=col_flavor_cpu, col_flavor_mem=col_flavor_mem,
                                        col_vm_created=col_vm_created, col_vm_deleted=col_vm_deleted,
                                        timestamp_begin=timestamp_begin, timestamp_end=timestamp_end, timestamp_step=timestamp_step)

    cpu_grouped = cpu_timestamped_df.drop('timestamp', axis=1)
    cpu_grouped = cpu_grouped.mean().to_frame()

    cpu_keys = cpu_grouped.index.values
    cpu_vals = cpu_grouped.values.tolist()
    res_cpu = pd.DataFrame({col_flavor_cpu: [int(key) for key in cpu_keys], 'freq': [round(np.mean(value),2) for value in cpu_vals]})

    mem_grouped = mem_timestamped_df.drop('timestamp', axis=1)
    mem_grouped = mem_grouped.mean().to_frame()

    mem_keys = mem_grouped.index.values
    mem_vals = mem_grouped.values.tolist()
    res_mem = pd.DataFrame({col_flavor_mem: [float(key) for key in mem_keys], 'freq': [round(np.mean(value),2) for value in mem_vals]})

    return res_cpu.loc[res_cpu['freq'] > 0.01].reset_index(drop=True), res_mem.loc[res_mem['freq'] > 0.01].reset_index(drop=True)

def __init_values_per_key(trace_df : pd.DataFrame, column_name : str):
    keys = list(trace_df[column_name].unique())
    keys.sort()
    values_per_keys = dict()
    for key in keys: values_per_keys[str(key)] = list()
    return keys, values_per_keys

def __add_to_result_dict_observed_freq(alive_df : pd.DataFrame, metric : str, metric_keys : list, result_dict : dict):

    distribution_df = pd.DataFrame(alive_df.groupby(metric).size().rename('count')).reset_index()
    total = distribution_df['count'].sum()
    distribution_df['freq'] = round((distribution_df['count']/total),2)

    observed_metric = list(distribution_df[metric] )
    for key in metric_keys:
        if key not in observed_metric:
            result_dict[str(key)].append(0)
        else:
            result_dict[str(key)].append(float(distribution_df.loc[distribution_df[metric] == key]['freq'].iloc[0]))
        

def convert_distribution_to_scenario(cpu_distribution : pd.DataFrame,  mem_distribution : pd.DataFrame,
                                     col_freq_cpu : str = 'freq', col_flavor_cpu = 'vmcorecount',
                                     col_freq_mem : str = 'freq', col_flavor_mem = 'vmmemory',
                                     output_file : str = 'scenario-vm-distribution.yml'
                                    ):
    
    ordered_cpu_distribution = cpu_distribution.sort_values(by=[col_flavor_cpu]).set_index(col_flavor_cpu)
    ordered_mem_distribution = mem_distribution.sort_values(by=[col_flavor_mem]).set_index(col_flavor_mem)
    
    yml_dict = dict()
    yml_dict["vm_distribution"] = dict()
    yml_dict["vm_distribution"]["config_cpu"] = ordered_cpu_distribution.apply(
        lambda row : float(row[col_freq_cpu]), axis=1).to_dict()
    
    yml_dict["vm_distribution"]["config_mem"] = ordered_mem_distribution.apply(
        lambda row :float(row[col_freq_mem]), axis=1).to_dict()
    
    with open(output_file, 'w') as outfile:
        yaml.dump(yml_dict, outfile, default_flow_style=False)