from urllib.request import urlretrieve
from pathlib import Path
import zipfile
import tarfile
from glob import glob
import argparse
import random

import pandas as pd
import numpy as np


def download_metadata(metadata_url, metadata_name):
    outdir = Path("data")
    metadata_path = outdir / metadata_name
    metadata_arch = metadata_path.with_suffix(".tar.gz")
    # download .tar.gz file
    urlretrieve(metadata_url, metadata_arch)
    # extract
    with tarfile.open(metadata_arch, "r:*") as t:
        t.extractall(outdir)
    # remove archive
    metadata_arch.unlink()
    # convert xlsx to csv
    xlsx_path = (outdir / metadata_name).with_suffix(".xlsx")
    meta = ""
    xls = pd.ExcelFile(xlsx_path)
    for sheet in xls.sheet_names:
        if sheet in ('cohort', 'legend'):
            continue
        df = pd.read_excel(xls, sheet)
        meta = metadata_path.with_suffix(".csv")
        df.to_csv(meta, index=False)
    xlsx_path.unlink()
    assert meta
    assert meta.is_file()
    return meta



def download_data(batch_url, batch_name, data_name):
    outdir = Path("data")
    batch_path = outdir / batch_name
    batch_arch = batch_path.with_suffix(".zip")
    data_csv = Path(data_name).with_suffix(".csv")
    # download .zip file
    urlretrieve(batch_url, batch_arch)
    # extract
    with zipfile.ZipFile(batch_arch, "r") as z:
        z.extractall(outdir)

    globbed = glob(str(outdir / '*' / data_csv))
    # move to outdir
    Path(globbed[0]).rename(outdir / data_csv)
    # remove the extracted folder
    extracted_folder = Path(globbed[0]).parent
    for item in extracted_folder.iterdir():
        item.unlink()
    extracted_folder.rmdir()
    # remove archive
    batch_arch.unlink()
    data = outdir / data_csv
    assert data
    assert data.is_file()
    return data



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

    # write to files for training and testing
    # shuffle the samples
    data = data.sample(frac=1, random_state=99)
    # write 80% of the samples to the training file and 20% to the testing file
    ntrain = int(split * data.shape[0])
    data_train = data.iloc[:ntrain]
    data_test = data.iloc[ntrain:]
    # write training and testing files
    data_train_path = outpath / "input_train.csv"
    data_test_path = outpath / "input_test.csv"
    data_train.to_csv(data_train_path, sep=',', index=index, header=header)
    data_test.to_csv(data_test_path, sep=',', index=index, header=header)
    # write full file
    # data_path = outpath / "input.csv"
    # data.to_csv(data_path, sep=',', index=index, header=header)
    print(f"total: {nsamples}, 0: {nsamples - psum}, 1: {psum}, feat: {nfeat}")
    
    


def downsample(downsample_features, downsample_samples, data):
     # downsample features and samples
    if downsample_features:
        k_feat = int(data.shape[1] * downsample_features)
        feat_keep = random.sample(data.columns.tolist(), k=k_feat)
        # always keep the health_status column
        feat_keep.extend(['health_status', 'gender', 'age', 'bmi'])
        data = data[feat_keep]
    if downsample_samples:
        k_samp = int(data.shape[0] * downsample_samples)
        samp_keep = random.sample(data.index.tolist(), k=k_samp)
        data = data.loc[samp_keep]
    return data


def get_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--acc", type=str, required=True)
    parser.add_argument("--tool", type=str, required=True)
    # parser.add_argument("--outdir", type=str, required=True)
    parser.add_argument("--downsample-samples", type=float, default=None)
    parser.add_argument("--downsample-features", type=float, default=None)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    # set random seed
    random.seed(99)
        
    # URL and name of the metadata file from the public cohort data
    metadata_url = "https://entrepot.recherche.data.gouv.fr/api/access/datafile/:persistentId?persistentId=doi:10.57745/LCAR4M"
    metadata_name = "metadata_2340_CRC_cohort_20240704"

    # for the species counts we use the batch effect corrected data
    # specifically the "combat" corrected with prevalence filtering at 0
    batch_url = " https://entrepot.recherche.data.gouv.fr/api/access/datafile/:persistentId?persistentId=doi:10.57745/GDKNAI"
    batch_name = "batch_effect_corrected_species_prev_0_2340_ech"
    data_name = "species_signal_2340_CRC_cohort_20240617_combat_prev0"


    outdir = Path('data')
    outdir.mkdir(parents=True, exist_ok=True)

    metadata_path = outdir / metadata_name
    meta = metadata_path.with_suffix(".csv")

    data_csv = Path(data_name).with_suffix(".csv")
    data = outdir / data_csv

    if not meta.is_file() or not data.is_file():
        print("Downloading public cohort data.")
        # download the public cohort files
        meta = download_metadata(
            metadata_url=metadata_url,
            metadata_name=metadata_name
        )

        data = download_data(
            batch_url=batch_url,
            batch_name=batch_name,
            data_name=data_name
        )
    else:
        print("Using existing public cohort data.")



    # get the sample accessions to keep according to the project accessions to keep
    samples_set, samples = filter_sample_ids(meta, acc_to_keep=args.acc)
    # filter the data to only those samples
    data_filt = filter_data(data, samples_set, samples)
    # select the samples (rows) for th accession
    data_acc = data_filt.loc[list(samples_set)]


    # downsample if specified
    if args.downsample_features or args.downsample_samples:
        data_acc = downsample(
            downsample_features=args.downsample_features,
            downsample_samples=args.downsample_samples,
            data=data_acc
        )

    outpath = outdir / args.tool / args.acc

    if args.tool == "federated-svd":    
        separate_data(
            data=data_acc,
            outpath=outpath,
            nostatus=True,
            header=True,
            index=True,
            transpose=True, 
            split=1
        )

    elif args.tool == "ada-boost" or args.tool == "random-forest":
        separate_data(
            data=data_acc,
            outpath=outpath,
            nostatus=False,
            header=True,
            index=False,
            transpose=False,
            split=0.8
        )
         


if __name__ == "__main__":
    main()

