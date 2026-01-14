from urllib.request import urlretrieve
from pathlib import Path
import zipfile
import tarfile
from glob import glob
import argparse
import random

import pandas as pd



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
    samples_status = dict()

    for _, row in meta_df.iterrows():
        acc = row['study_accession']
        if acc == acc_to_keep:
            sid = row['sample']
            samples_set.add(sid)
            status = -1
            if row['health_status'] == 'H':
                status = 0
            elif row['health_status'] == 'P':
                status = 1
            else:
                print('Unknown health status:', row['health_status'])
            assert status in (0, 1)
            samples_status[sid] = status
    # summary of health status
    psum = sum(list(samples_status.values()))
    print(f"0: {len(samples_set) - psum}, 1: {psum}")
    return samples_set, samples_status



def filter_data(data, samples_set, samples_status):
    data_df = pd.read_csv(data, index_col=0, sep='\t')
    # filter to the samples
    cols_to_keep = data_df.columns.intersection(samples_set)
    data_df_filt = data_df[cols_to_keep]  # type: ignore
    assert data_df_filt.shape[1] == len(samples_set)
    # flip axes
    data_df_filt = data_df_filt.transpose()
    # add column with health status
    data_df_filt['health_status'] = data_df_filt.index.map(samples_status)
    # ensure the index has a column name
    data_df_filt.index.name = 'sample_id'
    return data_df_filt


def separate_data(data, outpath, nostatus, header, index, transpose):
    # create output dir
    outpath.mkdir(parents=True, exist_ok=True)
    data_path = outpath / "input.csv"
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

    # write to file
    data.to_csv(data_path, sep=',', index=index, header=header)
    print(f"total: {nsamples}, 0: {nsamples - psum}, 1: {psum}, feat: {nfeat}")
    
    


def downsample(downsample_features, downsample_samples, data):
     # downsample features and samples
    if downsample_features:
        k_feat = int(data.shape[1] * downsample_features)
        feat_keep = random.sample(data.columns.tolist(), k=k_feat)
        # always keep the health_status column
        feat_keep.append('health_status')
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
    samples_set, samples_status = filter_sample_ids(meta, acc_to_keep=args.acc)
    # filter the data to only those samples
    # TODO grab clinical data as well
    data_filt = filter_data(data, samples_set, samples_status)
    # select the samples (rows) for th accession
    data_acc = data_filt.loc[list(samples_set)]


    # downsample if specified  TODO make sure the random seed works
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
            transpose=True
        )

    elif args.tool == "ada-boost" or args.tool == "random-forest":
        separate_data(
            data=data_acc,
            outpath=outpath,
            nostatus=False,
            header=True,
            index=False,
            transpose=False
        )
         


if __name__ == "__main__":
    main()

