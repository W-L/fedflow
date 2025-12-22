from urllib.request import urlretrieve
from pathlib import Path
import zipfile
import tarfile
from glob import glob
from collections import defaultdict
import argparse
import random

import pandas as pd



def download_metadata(metadata_url, outdir, metadata_name):
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



def download_signal(batch_url, outdir, batch_name, species_name):
    batch_path = outdir / batch_name
    batch_arch = batch_path.with_suffix(".zip")
    species_csv = Path(species_name).with_suffix(".csv")
    # download .zip file
    urlretrieve(batch_url, batch_arch)
    # extract
    with zipfile.ZipFile(batch_arch, "r") as z:
        z.extractall(outdir)

    globbed = glob(str(outdir / '*' / species_csv))
    # move to outdir
    Path(globbed[0]).rename(outdir / species_csv)
    # remove the extracted folder
    extracted_folder = Path(globbed[0]).parent
    for item in extracted_folder.iterdir():
        item.unlink()
    extracted_folder.rmdir()
    # remove archive
    batch_arch.unlink()
    species = outdir / species_csv
    assert species
    assert species.is_file()
    return species



def filter_sample_ids(metadata, accessions_to_keep):
    meta_df = pd.read_csv(metadata)
    
    # fill a dictionary with the study_accession and lists of sample_ids
    acc_set = set(accessions_to_keep)
    samples_dict = defaultdict(list)
    samples_set = set()
    samples_status = dict()

    for _, row in meta_df.iterrows():
        acc = row['study_accession']
        if acc in acc_set:
            sid = row['sample']
            samples_dict[acc].append(sid)
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
    return samples_dict, samples_set, samples_status



def filter_species_counts(species, samples_set, samples_status):
    species_df = pd.read_csv(species, index_col=0, sep='\t')
    # filter to the samples
    cols_to_keep = species_df.columns.intersection(samples_set)
    species_df_filt = species_df[cols_to_keep]  # type: ignore
    assert species_df_filt.shape[1] == len(samples_set)
    # flip axes
    species_df_filt = species_df_filt.transpose()
    # add column with health status
    species_df_filt['health_status'] = species_df_filt.index.map(samples_status)
    # ensure the index has a column name
    species_df_filt.index.name = 'sample_id'
    return species_df_filt


def separate_species_counts(samples_dict, species_filt, outdir):
    out_paths = []
    for acc, sample_ids in samples_dict.items():
        # select the samples (rows) for this accession
        species_acc = species_filt.loc[sample_ids]
        Path(outdir / acc).mkdir(parents=True, exist_ok=True)
        species_acc_path = outdir / acc / "species.csv"
        # write to csv without the sample names as a column
        species_acc.to_csv(species_acc_path, sep=',', index=False)
        out_paths.append(species_acc_path)
        # print summary
        psum = species_acc['health_status'].sum()
        nsamples = species_acc.shape[0]
        nfeat = species_acc.shape[1] 
        print(f"Accession: {acc}, total: {nsamples}, 0: {nsamples - psum}, 1: {psum}, feat: {nfeat}")
    return out_paths


def separate_species_counts_with_header_and_index(samples_dict, species_filt, outdir):
    out_paths = []
    for acc, sample_ids in samples_dict.items():
        # select the samples (rows) for this accession
        species_acc = species_filt.loc[sample_ids]
        # exclude the health status column from the features
        species_acc = species_acc.drop(columns=['health_status'])
        Path(outdir / acc).mkdir(parents=True, exist_ok=True)
        species_acc_path = outdir / acc / "species_header_index_nostatus.csv"
        # transpose so that samples are columns
        species_acc = species_acc.transpose()
        species_acc.to_csv(species_acc_path, sep=',', index=True, header=True)
        out_paths.append(species_acc_path)
        # print summary
        nsamples = species_acc.shape[0]
        nfeat = species_acc.shape[1] 
        print(f"Accession: {acc}, total: {nsamples}, feat: {nfeat}")
    # also save the combined file with header and index, without health status
    combined_path = outdir / "species_header_index_nostatus.csv"
    species_filt_nostatus = species_filt.drop(columns=['health_status'])
    # transpose so that samples are columns
    species_filt_nostatus = species_filt_nostatus.transpose()
    species_filt_nostatus.to_csv(combined_path, sep=',', index=True, header=True)
    return out_paths



def downsample(downsample_features, downsample_samples, species_filt):
     # downsample features and samples
    if downsample_features:
        k_feat = int(species_filt.shape[1] * downsample_features)
        feat_keep = random.sample(species_filt.columns.tolist(), k=k_feat)
        # always keep the health_status column
        feat_keep.append('health_status')
        species_filt = species_filt[feat_keep]
    if downsample_samples:
        k_samp = int(species_filt.shape[0] * downsample_samples)
        samp_keep = random.sample(species_filt.index.tolist(), k=k_samp)
        species_filt = species_filt.loc[samp_keep]
    return species_filt


def get_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=str, required=True)
    parser.add_argument("--skip-download", action='store_true', default=False)
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
    species_name = "species_signal_2340_CRC_cohort_20240617_combat_prev0"

    # these are the project accessions we want to keep
    # i.e. the public cohorts deemed high quality
    # limited to 5 for now
    accessions_to_keep = [
        "PRJEB10878",
        "PRJEB6070",
        "PRJEB7774",
        "PRJNA429097",
        "PRJNA731589",
    ]

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)



    if args.skip_download:
        print("Skipping download of public cohort data.")

        metadata_path = outdir / metadata_name
        meta = metadata_path.with_suffix(".csv")

        species_csv = Path(species_name).with_suffix(".csv")
        species = outdir / species_csv
    else:
        # download the public cohort files
        meta = download_metadata(
            metadata_url=metadata_url,
            outdir=outdir,
            metadata_name=metadata_name
        )

        species = download_signal(
            batch_url=batch_url,
            outdir=outdir,
            batch_name=batch_name,
            species_name=species_name
        )



    # get the sample accessions to keep according to the project accessions to keep
    samples_dict, samples_set, samples_status = filter_sample_ids(meta, accessions_to_keep)

    # filter the species counts to only those samples
    species_filt = filter_species_counts(species, samples_set, samples_status)
    # save them to csv file
    species_filt_path = outdir / f"{species_name}.filt.csv"
    species_filt.to_csv(species_filt_path, sep=',')

    # downsample if specified
    if args.downsample_features or args.downsample_samples:
        species_filt = downsample(
            downsample_features=args.downsample_features,
            downsample_samples=args.downsample_samples,
            species_filt=species_filt
        )

    # separate the species counts into different files per project accession
    acc_paths = separate_species_counts(samples_dict, species_filt, outdir)
    # also save with header and index, without health status
    acc_paths_hi = separate_species_counts_with_header_and_index(samples_dict, species_filt, outdir)



if __name__ == "__main__":
    main()

