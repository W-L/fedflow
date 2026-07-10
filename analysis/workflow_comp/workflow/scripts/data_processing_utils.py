import random

import pandas as pd
import numpy as np



def filter_sample_ids(metadata, acc_to_keep):
    meta_df = pd.read_csv(metadata)
    samples_set = set()
    samples = dict()  # sample to metadata dict
    samples["sid"] = []
    samples["health_status"] = []
    samples["gender"] = []
    samples["age"] = []
    samples["bmi"] = []

    for _, row in meta_df.iterrows():
        acc = row['study_accession']
        if acc == acc_to_keep:
            sid = row['sample']
            samples_set.add(sid)
            samples["sid"].append(sid)
            # convert health status to binary
            status = -1
            if row['health_status'] == 'H':
                status = 0
            elif row['health_status'] == 'P':
                status = 1
            else:
                print('Unknown health status:', row['health_status'])
            assert status in (0, 1)
            samples["health_status"].append(status)
            # convert gender to binary
            gender = -1
            if row['gender'] == 'male':
                gender = 0
            elif row['gender'] == 'female':
                gender = 1
            else:
                gender = 2
            samples["gender"].append(gender)
            # get age
            age = row['age']
            if pd.isna(age):
                age = -1
            samples["age"].append(int(age))
            # get bmi
            bmi = row['bmi']
            if pd.isna(bmi):
                bmi = -1
            samples["bmi"].append(float(bmi))

    # summary of health status
    psum = sum(list(samples["health_status"]))
    print(f"0: {len(samples_set) - psum}, 1: {psum}")
    # summary of gender
    gender_arr = np.array(samples["gender"])
    values, counts = np.unique(gender_arr, return_counts=True)
    print(f"gender summary: {dict(zip(values, counts))}")
    # summary of age
    age_arr = np.array(samples["age"])
    print(f"age summary: min={age_arr.min()}, max={age_arr.max()}, mean={age_arr.mean()}")
    print(f"age missing: {(age_arr < 0).sum()} out of {len(age_arr)}")
    # summary of bmi
    bmi_arr = np.array(samples["bmi"])
    print(f"bmi summary: min={bmi_arr.min()}, max={bmi_arr.max()}, mean={bmi_arr.mean()}")
    print(f"bmi missing: {(bmi_arr < 0).sum()} out of {len(bmi_arr)}")
    # impute missing values with mean for age and bmi
    age_mean = age_arr[age_arr >= 0].mean()
    bmi_mean = bmi_arr[bmi_arr >= 0].mean()
    samples["age"] = [age if age >= 0 else age_mean for age in samples["age"]]
    samples["bmi"] = [bmi if bmi >= 0 else bmi_mean for bmi in samples["bmi"]]
    return samples_set, samples



def filter_data(data, samples_set, samples):
    data_df = pd.read_csv(data, index_col=0, sep='\t')
    # filter to the samples
    cols_to_keep = data_df.columns.intersection(samples_set)
    data_df_filt = data_df[cols_to_keep]  # type: ignore
    assert data_df_filt.shape[1] == len(samples_set)
    # flip axes
    data_df_filt = data_df_filt.transpose()
    # add column with health status
    samples_status = dict(zip(samples["sid"], samples["health_status"]))
    data_df_filt['health_status'] = data_df_filt.index.map(samples_status)
    # add column with gender
    samples_gender = dict(zip(samples["sid"], samples["gender"]))
    data_df_filt['gender'] = data_df_filt.index.map(samples_gender)
    # add column with age
    samples_age = dict(zip(samples["sid"], samples["age"]))
    data_df_filt['age'] = data_df_filt.index.map(samples_age)
    # add column with bmi
    samples_bmi = dict(zip(samples["sid"], samples["bmi"]))
    data_df_filt['bmi'] = data_df_filt.index.map(samples_bmi)
    # ensure the index has a column name
    data_df_filt.index.name = 'sample_id'
    return data_df_filt




def split_data(data, nrep, train_split=0.8):
    # sample nrep intergers for the random_state for shuffling
    random_states = [random.randint(0, 1000) for _ in range(nrep)]
    data_train_list = []
    data_test_list = []

    for n in range(nrep):
        # shuffle the samples
        data = data.sample(frac=1, random_state=random_states[n])
        # write train_split (80%) of the samples to the training file and rest to the testing file
        ntrain = int(train_split * data.shape[0])
        data_train = data.iloc[:ntrain]
        data_test = data.iloc[ntrain:]
        data_train_list.append(data_train)
        data_test_list.append(data_test)
        
    return data_train_list, data_test_list
    

