from pathlib import Path
import argparse
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


def separate_data(data, outpath, nostatus, header, index, transpose, split):
    # create output dir
    outpath.mkdir(parents=True, exist_ok=True)
    nsamples = data.shape[0]
    nfeat = data.shape[1] 

    if nostatus:
        # exclude the health status column from the features
        data = data.drop(columns=['health_status'])
        psum = 0
    else:
        psum = data['health_status'].sum()
    if transpose:
        # transpose so that samples are columns
        data = data.transpose()

    if split:
        # write to files for training and testing
        # shuffle the samples
        data = data.sample(frac=1, random_state=99)
        # write 80% of the samples to the training file and 20% to the testing file
        ntrain = int(0.8 * data.shape[0])
        data_train = data.iloc[:ntrain]
        data_test = data.iloc[ntrain:]
        # write training and testing files
        data_train_path = outpath / "input.csv"
        data_test_path = outpath / "input_test.csv"
        data_train.to_csv(data_train_path, sep=',', index=index, header=header)
        data_test.to_csv(data_test_path, sep=',', index=index, header=header)
    else:
        # write full file
        data_path = outpath / "input.csv"
        data.to_csv(data_path, sep=',', index=index, header=header)
    print(f"total: {nsamples}, 0: {nsamples - psum}, 1: {psum}, feat: {nfeat}")
    
    


def get_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--acc", type=str, required=True)
    parser.add_argument("--tool", type=str, required=True)
    parser.add_argument("--msp", type=str, required=True)
    parser.add_argument("--meta", type=str, required=True)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    # set random seed
    random.seed(99)
    
    # get the sample accessions to keep according to the project accessions to keep
    samples_set, samples = filter_sample_ids(args.meta, acc_to_keep=args.acc)
    # filter the data to only those samples
    data_filt = filter_data(args.msp, samples_set, samples)
    # select the samples (rows) for th accession
    data_acc = data_filt.loc[list(samples_set)]

    outpath = Path('data') / args.tool / args.acc

    if args.tool == "federated-svd":    
        separate_data(
            data=data_acc,
            outpath=outpath,
            nostatus=True,
            header=True,
            index=True,
            transpose=True, 
            split=False
        )

    elif args.tool == "ada-boost" or args.tool == "random-forest":
        separate_data(
            data=data_acc,
            outpath=outpath,
            nostatus=False,
            header=True,
            index=False,
            transpose=False,
            split=True
        )
         


if __name__ == "__main__":
    main()

