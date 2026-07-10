from pathlib import Path
import argparse
import random

import data_processing_utils as dpu






def separate_data(data, outpath, nostatus, header, index, transpose, split, nrep):
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
        # sample nrep intergers for the random_state for shuffling
        random_states = [random.randint(0, 1000) for _ in range(nrep)]

        for n in range(nrep):
            rep_outpath = outpath / f"rep_{n}"
            rep_outpath.mkdir(parents=True, exist_ok=True)
            # write to files for training and testing
            # shuffle the samples
            data = data.sample(frac=1, random_state=random_states[n])
            # write 80% of the samples to the training file and 20% to the testing file
            ntrain = int(0.8 * data.shape[0])
            data_train = data.iloc[:ntrain]
            data_test = data.iloc[ntrain:]
            # write training and testing files
            data_train_path = rep_outpath / "input.csv"
            data_test_path = rep_outpath / "input_test.csv"
            data_train.to_csv(data_train_path, sep=',', index=index, header=header)
            data_test.to_csv(data_test_path, sep=',', index=index, header=header)
    else:
        # write full file
        rep_outpath = outpath / f"rep_0"
        rep_outpath.mkdir(parents=True, exist_ok=True)
        data_path = rep_outpath / "input.csv"
        data.to_csv(data_path, sep=',', index=index, header=header)
    print(f"total: {nsamples}, 0: {nsamples - psum}, 1: {psum}, feat: {nfeat}")
    
    


def get_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--acc", type=str, required=True)
    parser.add_argument("--msp", type=str, required=True)
    parser.add_argument("--meta", type=str, required=True)
    parser.add_argument("--nrep", type=int, required=True)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    # set random seed
    random.seed(99)
    # create output dir
    outpath = Path('data') / "random-forest" / "fed" / args.acc 
    outpath.mkdir(parents=True, exist_ok=True)
    
    # get the sample accessions to keep according to the project accessions to keep
    samples_set, samples = dpu.filter_sample_ids(args.meta, acc_to_keep=args.acc)
    # filter the data to only those samples
    data_filt = dpu.filter_data(args.msp, samples_set, samples)
    # select the samples (rows) for th accession
    data_acc = data_filt.loc[list(samples_set)]

    # TOOL-SPECIFIC processing
    data_train_list, data_test_list = dpu.split_data(data_acc, nrep=args.nrep)

    # write training and testing data to files
    for n in range(args.nrep):
        rep_outpath = outpath / f"{n:03d}"
        rep_outpath.mkdir(parents=True, exist_ok=True)
        data_train_path = rep_outpath / "input.csv"
        data_test_path = rep_outpath / "input_test.csv"
        data_train_list[n].to_csv(data_train_path, sep=',', index=False, header=True)
        data_test_list[n].to_csv(data_test_path, sep=',', index=False, header=True)



if __name__ == "__main__":
    main()

