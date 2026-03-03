from urllib.request import urlretrieve
from pathlib import Path
import zipfile
import tarfile
from glob import glob

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




def main():    
    # URL and name of the metadata file from the public cohort data
    metadata_url = "https://entrepot.recherche.data.gouv.fr/api/access/datafile/:persistentId?persistentId=doi:10.57745/LCAR4M"
    metadata_name = "metadata_2340_CRC_cohort_20240704"

    # for the species counts we use the batch effect corrected data
    # specifically the "combat" corrected with prevalence filtering at 0
    batch_url = " https://entrepot.recherche.data.gouv.fr/api/access/datafile/:persistentId?persistentId=doi:10.57745/GDKNAI"
    batch_name = "batch_effect_corrected_species_prev_0_2340_ech"
    data_name = "species_signal_2340_CRC_cohort_20240617_combat_prev0"


    meta = download_metadata(
        metadata_url=metadata_url,
        metadata_name=metadata_name
    )

    data = download_data(
        batch_url=batch_url,
        batch_name=batch_name,
        data_name=data_name
    )


if __name__ == "__main__":
    main()
