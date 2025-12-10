from urllib.request import urlretrieve
from pathlib import Path
import zipfile
import tarfile
from glob import glob
from collections import defaultdict

import pandas as pd

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


# -------------------- END OF PARAMETERS --------------------


outdir = Path("../test_data/public_cohorts")
outdir.mkdir(parents=True, exist_ok=True)


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

    for _, row in meta_df.iterrows():
        acc = row['study_accession']
        if acc in acc_set:
            samples_dict[acc].append(row['sample'])
            samples_set.add(row['sample'])

    return samples_dict, samples_set


def filter_species_counts(species, samples):
    species_df = pd.read_csv(species, index_col=0, sep='\t')
    # filter to the samples
    cols_to_keep = species_df.columns.intersection(samples)
    species_df_filt = species_df[cols_to_keep]  # type: ignore
    assert species_df_filt.shape[1] == len(samples)
    return species_df_filt


def separate_species_counts(samples_dict, species_filt, outdir):
    out_paths = []
    for acc, sample_ids in samples_dict.items():
        species_acc = species_filt[sample_ids]
        Path(outdir / acc).mkdir(parents=True, exist_ok=True)
        species_acc_path = outdir / acc / "species.csv"
        species_acc.to_csv(species_acc_path, sep=',')
        out_paths.append(species_acc_path)
    return out_paths



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
samples_dict, samples = filter_sample_ids(meta, accessions_to_keep)

# filter the species counts to only those samples
species_filt = filter_species_counts(species, samples)
# save them to csv file
species_filt_path = outdir / f"{species_name}.filt.csv"
species_filt.to_csv(species_filt_path, sep=',')

# separate the species counts into different files per project accession
acc_paths = separate_species_counts(samples_dict, species_filt, outdir)



