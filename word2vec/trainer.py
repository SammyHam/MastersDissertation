import torch
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm
from enum import IntEnum

from word2vec.dataReaderDoc import DataReader, Word2vecDataset
from word2vec.word2vec import SkipGramModel

class VecTrain(IntEnum):
    combined  = 0
    primary   = 1
    secondary = 2

class Word2VecTrainer:
    def __init__(self, primary_files, emb_dimension=10, batch_size=32, window_size=5,
                 iterations=3, initial_lr=0.001, min_count=1, supporting_files=None):

        self.data = DataReader(primary_files, min_count, supporting_files)

        # data sets with different target files
        dataset = Word2vecDataset(self.data, window_size, custom_files=None)
        primary = Word2vecDataset(self.data, window_size, custom_files=primary_files)
        support = Word2vecDataset(self.data, window_size, custom_files=supporting_files)

        # combined, main and secondary data loaders
        self.dataloader    = DataLoader(dataset, batch_size, shuffle=False, num_workers=0, collate_fn=dataset.collate)
        self.dataprimary   = DataLoader(primary, batch_size, shuffle=False, num_workers=0, collate_fn=dataset.collate)
        self.datasecondary = DataLoader(support, batch_size, shuffle=False, num_workers=0, collate_fn=dataset.collate)

        self.emb_size = len(self.data.word2id)
        self.emb_dimension = emb_dimension
        self.batch_size = batch_size
        self.iterations = iterations
        self.initial_lr = initial_lr
        self.skip_gram_model = SkipGramModel(self.emb_size, self.emb_dimension)

        self.use_cuda = torch.cuda.is_available()
        self.device = torch.device("cuda" if self.use_cuda else "cpu")

        if self.use_cuda:
            self.skip_gram_model.cuda()


    def train(self, train_mode, output_file):

        dataloader = None
        if train_mode == VecTrain.combined:
            dataloader = self.dataloader
        if train_mode == VecTrain.primary:
            dataloader = self.dataprimary
        if train_mode ==VecTrain.secondary:
            dataloader = self.datasecondary

        for iteration in tqdm(range(self.iterations)):

            optimizer = optim.SparseAdam(self.skip_gram_model.parameters(), lr=self.initial_lr)
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, len(dataloader))

            running_loss = 0.0
            for i, sample_batched in enumerate(dataloader):

                if len(sample_batched[0]) > 1:
                    pos_u = sample_batched[0].to(self.device)
                    pos_v = sample_batched[1].to(self.device)
                    neg_v = sample_batched[2].to(self.device)

                    scheduler.step()
                    optimizer.zero_grad()
                    loss = self.skip_gram_model.forward(pos_u, pos_v, neg_v)
                    loss.backward()
                    optimizer.step()

                    running_loss = running_loss * 0.9 + loss.item() * 0.1
                    if i > 0 and i % 500 == 0:
                        print(" Loss: " + str(running_loss))

        self.skip_gram_model.save_embedding(self.data.id2word, output_file, self.data.max_num_words_file)
