# load a large data matrix and split it into smaller chunks for distributed processing
import pandas as pd

file_path = 'apps/federated_svd/data/mnist_export/mnist.tsv'

data = pd.read_csv(file_path, sep='\t', index_col=0)
data.shape
data.head(10)


num_splits = 3
split_size = data.shape[0] // num_splits

for i in range(num_splits):
    start_idx = i * split_size
    end_idx = (i + 1) * split_size if i < num_splits - 1 else data.shape[0]
    split_data = data.iloc[start_idx:end_idx]
    split_file_path = f'apps/federated_svd/data/mnist_export/mnist_split_{i}.tsv'
    split_data.to_csv(split_file_path, sep='\t')
    print(f'Saved split {i+1} to {split_file_path} with shape {split_data.shape}')


