import yaml, math, time
import pandas as pd
import numpy as np
from scipy import signal
from collections import defaultdict
from sklearn.cluster import KMeans

def build_n_scenario(trace_df : pd.DataFrame, n_profile : int,
                    col_cpu_avg : str = 'avgcpu', col_cpu_per : str = 'p95maxcpu'):


    avg_percentile_tuple = trace_df.apply(lambda row : [row[col_cpu_avg], row[col_cpu_per]], axis=1).tolist()
    kmeans = KMeans(n_clusters=n_profile, random_state=0, n_init="auto").fit(avg_percentile_tuple)
    attributed_class_center = kmeans.cluster_centers_
    attributed_class_value = kmeans.labels_

    trace_df_labeled = trace_df
    trace_df_labeled["label"] = attributed_class_value

    usage_distribution = pd.DataFrame(trace_df_labeled.groupby('label').size().rename('count')).reset_index()
    __compute_cpu_bounds_per_label(usage_distribution=usage_distribution, trace_df_labeled=trace_df_labeled,
                    col_cpu_avg=col_cpu_avg, col_cpu_per=col_cpu_per)
    return usage_distribution, trace_df_labeled

def __compute_cpu_bounds_per_label(usage_distribution : pd.DataFrame, trace_df_labeled : pd.DataFrame,
                    col_cpu_avg : str, col_cpu_per : str):
    total = usage_distribution['count'].sum()
    usage_distribution['freq'] = round((usage_distribution['count']/total),2)
    usage_distribution['bound_avg_lower'] = usage_distribution.apply(lambda row : round(trace_df_labeled[trace_df_labeled['label'] == row['label']][col_cpu_avg].min(),1), axis=1)
    usage_distribution['bound_avg_higher'] = usage_distribution.apply(lambda row : round(trace_df_labeled[trace_df_labeled['label'] == row['label']][col_cpu_avg].max(),1), axis=1)
    usage_distribution['bound_per_lower'] = usage_distribution.apply(lambda row : round(trace_df_labeled[trace_df_labeled['label'] == row['label']][col_cpu_per].min(),1), axis=1)
    usage_distribution['bound_per_higher'] = usage_distribution.apply(lambda row : round(trace_df_labeled[trace_df_labeled['label'] == row['label']][col_cpu_per].max(),1), axis=1)
    usage_distribution.sort_values(by=['bound_avg_lower'], inplace=True)

def build_arrival_and_departure_rates_per_label(usage_distribution : pd.DataFrame, trace_df_labeled : pd.DataFrame,
                    col_vm_created : str = 'vmcreated', col_vm_deleted : str = 'vmdeleted',
                    scope_duration : int = 86400): #3600*24

    start = np.min([trace_df_labeled[col_vm_created].min(), trace_df_labeled[col_vm_deleted].min()])
    end = np.max([trace_df_labeled[col_vm_created].max(), trace_df_labeled[col_vm_deleted].max()])

    iteration = math.ceil((end - start)/scope_duration)

    range_list_min = list(range(start, start+iteration*scope_duration, scope_duration))

    range_list_max = list(range_list_min)
    del range_list_min[-1]
    range_list_min[0]=1 # to manage previously existing VM, displayed as starting at 0
    del range_list_max[0]
    interval_list = list(zip(range_list_min, range_list_max))

    ratios = usage_distribution.apply(
        lambda row : __compute_departure_and_arrival_rate_for_given_label(trace_df_labeled=trace_df_labeled, 
                        interval_list=interval_list, label=row["label"],
                        col_vm_created=col_vm_created, col_vm_deleted=col_vm_deleted),
        axis=1)

    usage_distribution_with_ratio = usage_distribution
    usage_distribution_with_ratio["ratio_arriving"] = usage_distribution_with_ratio.apply(
        lambda row : ratios[row["label"]]["arriving"], axis=1)
    usage_distribution_with_ratio["ratio_leaving"] = usage_distribution_with_ratio.apply(
        lambda row : ratios[row["label"]]["leaving"], axis=1)

def __compute_departure_and_arrival_rate_for_given_label(trace_df_labeled : pd.DataFrame, interval_list : list, label : str,
                    col_vm_created : str, col_vm_deleted : str):
    leaving_ratios = list()
    arriving_ratios = list()

    for min_timestamp, max_timestamp in interval_list:
        # Dataset containing all VM alive in current range (deleted after min, created before max)

        trace_filtered_df = \
            trace_df_labeled.loc[ \
                    (trace_df_labeled["label"] == label) \
                 & (trace_df_labeled[col_vm_deleted] >= min_timestamp) \
                 & (trace_df_labeled[col_vm_created] <= max_timestamp)]
        count = len(trace_filtered_df)
        # Computing newly arrived ones
        newly_count = len(trace_filtered_df.loc[trace_filtered_df[col_vm_created] >= min_timestamp])
        arriving_ratios.append(round(newly_count/count, 2))
        # Computing newly departed ones
        leaving_count = len(trace_filtered_df.loc[trace_filtered_df[col_vm_deleted]< max_timestamp])
        leaving_ratios.append(round(leaving_count/count, 2))
    
    return {'arriving' : np.median(arriving_ratios), 'leaving' : np.median(leaving_ratios)}

def build_periodicity_rate_per_label(usage_distribution : pd.DataFrame, label_dataset : pd.DataFrame, cpu_traces_dataset : pd.DataFrame,
                                        timestamp_per_hour : int,
                                        detect_periodicity_on_hour : int = 24,
                                        lifetime_condition : int = -np.inf, 
                                        max_number_of_tests : int = 500,
                                        set_of_ids_in_cpu_traces : set = None, # to speed up process
                                        sensibility : int = 1, # [0;100] value to set the periodicity (later translated into a percentile using 100-periodicity), should not be very high
                                        col_vm_created : str = 'vmcreated', col_vm_deleted : str = 'vmdeleted',
                                        col_vm_id : str = "vmid", col_vm_cpu : str = "cpu_avg"):
    
    if set_of_ids_in_cpu_traces is None:
        set_of_ids_in_cpu_traces = set(cpu_traces_dataset[col_vm_id].unique()) # taking a long time on large dataset
    
    periodicity_ratio_list = list()
    for index, row in usage_distribution.iterrows():
        considered_label = int(row["label"])
        print("Computing periodicity ratio for label", considered_label)
        begin = time.time_ns()
        periodic_r = __compute_periodicity_rate_for_given_label(label_dataset=label_dataset, cpu_traces_dataset=cpu_traces_dataset,
                                    label=considered_label,
                                    timestamp_per_hour=timestamp_per_hour,
                                    detect_periodicity_on_hour=detect_periodicity_on_hour,
                                    lifetime_condition = lifetime_condition,
                                    max_number_of_tests = max_number_of_tests,
                                    set_of_ids_in_cpu_traces=set_of_ids_in_cpu_traces,
                                    sensibility=sensibility,
                                    col_vm_created=col_vm_created, col_vm_deleted=col_vm_deleted,
                                    col_vm_id=col_vm_id, col_vm_cpu=col_vm_cpu
                                    )
        periodicity_ratio_list.append(periodic_r)
        print("Ratio computed for label", considered_label, ":", periodic_r, "(elapsed time:", round((time.time_ns()-begin)/10**9), "s)")
        
    usage_distribution["ratio_periodicity"] = periodicity_ratio_list

def __compute_periodicity_rate_for_given_label(label_dataset : pd.DataFrame, cpu_traces_dataset : pd.DataFrame,
                                         label : int,
                                         timestamp_per_hour : int,
                                         detect_periodicity_on_hour,
                                         lifetime_condition : int, 
                                         max_number_of_tests : int, # to speed up process
                                         set_of_ids_in_cpu_traces : set,
                                         sensibility : int,
                                         col_vm_created : str, col_vm_deleted : str,
                                         col_vm_id : str, col_vm_cpu : str):
    # List of matching VM
    matching_vms = list(label_dataset.loc[(label_dataset["label"] == label) &\
                              (label_dataset[col_vm_deleted] - label_dataset[col_vm_created] >= lifetime_condition)][col_vm_id])
    matching_vms_count = len(matching_vms)
    excluded_vms_count = len(label_dataset.loc[(label_dataset["label"] == label) &\
                              (label_dataset[col_vm_deleted] - label_dataset[col_vm_created] < lifetime_condition)][col_vm_id])
    # In matching VM, we only consider VM presents in cpu traces dataset
    considered_vms = list()
    for vmid in matching_vms:
        if vmid in set_of_ids_in_cpu_traces: considered_vms.append(vmid)
    del matching_vms
    considered_vms_count = len(considered_vms)
    # Post consideration on quantity
    if considered_vms_count > max_number_of_tests:
        print(">Number of VM exceeds max number of test, reducing to", max_number_of_tests, "instead of", considered_vms_count)
        considered_vms = considered_vms[:max_number_of_tests]
        considered_vms_count = max_number_of_tests
    considered_vms = set(considered_vms) # convert to set to speed up following iteration
    if considered_vms_count < 10:
        print(">Warning : low number of VM matching condition (", len(considered_vms), ")")

    # Convert to a dict as it tends to be more efficient for vmid based accesss (however isin() method is quite slow)
    filtered_cpu_traces_dict = defaultdict(list)
    filtered_cpu_traces_df = cpu_traces_dataset.loc[cpu_traces_dataset[col_vm_id].isin(considered_vms)][[col_vm_id, col_vm_cpu]]
    for index, row in filtered_cpu_traces_df.iterrows():
        filtered_cpu_traces_dict[row[col_vm_id]].append(row[col_vm_cpu])
    # Iterate through vmid to compute periodicity
    considered_vms_periodic_count = 0
    for vmid, values in filtered_cpu_traces_dict.items():
        mean_val = np.mean(values)
        bool_res = __is_periodic([val - mean_val for val in values], scope=detect_periodicity_on_hour, timestamp_per_hour=timestamp_per_hour, percentile=(100-sensibility))
        if bool_res: considered_vms_periodic_count+=1
    # Compute results as ratio
    ratio_on_considered_vms = considered_vms_periodic_count/considered_vms_count
    ratio_on_overall = (matching_vms_count*ratio_on_considered_vms)/(matching_vms_count+excluded_vms_count)
    
    return round(ratio_on_overall,3)

def __find_nearest(array, value):
    array = np.asarray(array)
    return (np.abs(array - value)).argmin()

def __is_periodic(values : pd.core.series.Series, scope : int, timestamp_per_hour : int, percentile : int):

    f, Pxx_den  = signal.periodogram(values, fs=timestamp_per_hour)
    fprime = [1/x if x !=0 else np.inf for x in f]

    closest_x = __find_nearest(fprime, value=scope)
    val = Pxx_den[closest_x]
    threshold = np.max([np.percentile(Pxx_den, percentile),1])
    
    if val > threshold:
        return True
    return False

def convert_usage_to_scenario(usage_distribution : pd.DataFrame,
                            col_bound_cpu_avg_min : str = 'bound_avg_lower', col_bound_cpu_avg_max : str = 'bound_avg_higher',
                            col_bound_cpu_per_min : str = 'bound_per_lower', col_bound_cpu_per_max : str = 'bound_per_higher',
                            col_freq  : str = 'freq',
                            col_rate_arrival : str = 'ratio_arriving', col_rate_departure  : str = 'ratio_leaving',
                            col_rate_periodicity : str = 'ratio_periodicity',
                            col_label  : str = 'label',
                            output_file : str = 'scenario-vm-usage.yml'):
    
    ordered_usage_distribution = usage_distribution.sort_values(by=[col_bound_cpu_avg_min])
    ordered_usage_distribution["profile_name"] = ordered_usage_distribution.apply(lambda x : "profile" + str(int(x[col_label])), axis=1)
    ordered_usage_distribution.set_index("profile_name", inplace=True)
    
    def convert_line_to_dict(row : pd.core.series.Series):
        line_dict = dict()
        line_dict["avg"] = {'min': float(row[col_bound_cpu_avg_min]), 'max' : float(row[col_bound_cpu_avg_max])}
        line_dict["per"] = {'min': float(row[col_bound_cpu_per_min]), 'max' : float(row[col_bound_cpu_per_max])}
        line_dict["rate"] = {'arrival' : float(row[col_rate_arrival]), 'departure' : float(row[col_rate_departure]), 'periodicity' : float(row[col_rate_periodicity])}
        line_dict["freq"] = float(row["freq"])
        return line_dict
    
    yml_dict = dict()
    yml_dict["vm_usage"] = ordered_usage_distribution.apply(
        lambda row : convert_line_to_dict(row), axis=1).to_dict()
    
    with open(output_file, 'w') as outfile:
        yaml.dump(yml_dict, outfile, default_flow_style=False)