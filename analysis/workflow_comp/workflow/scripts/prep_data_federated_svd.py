from pathlib import Path
import argparse
import random

import data_processing_utils as dpu



def get_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--acc", type=str, required=True)
    parser.add_argument("--msp", type=str, required=True)
    parser.add_argument("--meta", type=str, required=True)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    # set random seed
    random.seed(99)
    # create output dir
    outpath = Path('data') / "federated-svd" / "fed" / args.acc / "000"
    outpath.mkdir(parents=True, exist_ok=True)
    
    # get the sample accessions to keep according to the project accessions to keep
    samples_set, samples = dpu.filter_sample_ids(args.meta, acc_to_keep=args.acc)
    # filter the data to only those samples
    data_filt = dpu.filter_data(args.msp, samples_set, samples)
    # select the samples (rows) for th accession
    data_acc = data_filt.loc[list(samples_set)]
    # TOOL-SPECIFIC processing
    # exclude the health status column from the features
    data_acc = data_acc.drop(columns=['health_status'])
    # transpose so that samples are columns
    data_acc = data_acc.transpose()
    # write output
    data_path = outpath / "input.csv"
    data_acc.to_csv(data_path, sep=',', index=True, header=True)


if __name__ == "__main__":
    main()

