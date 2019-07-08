import torch
import numpy as np
from torch.utils.data import Dataset
from collections import defaultdict, OrderedDict

class VectorDataset(Dataset):

    def __init__(self, file_paths, labels, seq_dim, batch_size=1):
        self.file_paths = file_paths
        self.num_files  = len(file_paths)
        self.batch_size = batch_size
        self.labels     = np.asarray(labels)
        self.seq_dim    = seq_dim

        # print label distribution
        self.labelHistogram()


    def __len__(self):
        return self.num_files/self.batch_size


    def labelHistogram(self):
        lbl_hist = defaultdict(int)
        for label in self.labels:
            lbl_hist[label] += 1

        lbl_hist = OrderedDict(sorted(lbl_hist.items()))
        print("| ---- Label Frequency ----  |")
        print("|                            |")
        for item in lbl_hist:
                print("| Label: {:2d}, Frequency: {:4d} |".format(item, lbl_hist[item]))
        print("|                            |")


    def __getitem__(self, idx):

        randindex = np.random.randint(low=0, high=self.num_files)
        file   = open(self.file_paths[randindex], 'r', encoding='utf8')

        vectors   = list()
        for i in range(0, self.seq_dim):
            arr = np.fromstring(file.readline(), dtype=float, sep=" ")
            vectors.append(arr)

        label = 1
        if self.labels[randindex] < 5:
            label = 0

        return torch.tensor([np.asarray(vectors)]).float(), torch.tensor([label]).long()

