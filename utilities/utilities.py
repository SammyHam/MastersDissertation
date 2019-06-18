import torch
import re
import csv
import time
import datetime
import numpy as np
import os
from string import punctuation
from lstm.file2VecConverter import File2VecConverter
from lstm.dataReaderVec import VectorDataset

from enum import IntEnum

class Mode(IntEnum):
    word2vec   = 0
    conversion = 1
    lstm       = 2
    similarity = 3
    plot       = 4

class weightInit(IntEnum):
    fromScratch = 0
    load        = 1
    inherit     = 2

# cleans a line of text from punctuation and other special characters before processing
def parseLine(line):
    line = line.lower()
    line = re.sub(r'\(.*?\)', '', line) #remove special characters
    line = ''.join([c for c in line if c not in punctuation])
    line = re.sub(r'[^\x00-\x7f]', r'', line) #remove hex characters
    return line


# returns a list of file paths from the same directory to avoid manual initialisation
def generateFilePaths(path, number_of_docs, extension):
    paths = list()
    for i in range(0, number_of_docs):
        paths.append(path + str(i) + extension)
    return paths


# convert documents into vector representations and write them to files
def documentVectorisation(doc_files, vec_files, dict_file, debug=False):
    converter = File2VecConverter(doc_files, dict_file)
    converter.convertDocuments(vec_files)

    if debug:
        dataReader = VectorDataset(vec_files)
        reverse_dict = converter.readVectorsDict(reverse=True)

        for vector_doc in dataReader:
            printVecToWords(reverse_dict, vector_doc)
            exit(0)


# reconverts vectors to words for debugging/checking purposes
def printVecToWords(reverse_dict,vectors):
    for vector in vectors:
        count = 0
        for element in vector:
            if len(str(element)) > 5:
                vector[count] = str(element)[0:5]
            count += 1
        key = str(vector).replace("\n", "").replace(" ", "").replace("0","")
        if key in reverse_dict:
            print(reverse_dict[key])
        else:
            print(key)


# returns the maximum number of words observed in a single document
def getMaxDocumentLength(dict_file):
    with open(dict_file,'r') as f:
        header = f.readline()
        return int(header.split()[2])


# saves accuracy measures obtained during training to csv file
def writeDataToCSV(data, filename):
    x_axis = np.arange(len(data))
    with open(filename, mode='w', newline='') as csv_file:
        accuracy_writer = csv.writer(csv_file, delimiter=',')
        for i in range(0, len(data)):
            accuracy_writer.writerow([x_axis[i],data[i]])


# reads accuracy value from csv; needed for plotting a graph with matplotlib
def readAccuraciesFromCSV(filename):
    x_axis = list()
    y_axis = list()
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for line in csv_reader:
            x_axis.append(int(line[0]))
            y_axis.append(float(line[1]))

    return x_axis, y_axis


# generates time stamp
def timeStampedFileName():
    fmt = '%Y_%m_%d_%H_%M_%S'
    time.sleep(1.1) # -> make sure no equivalent time stamp is given out
    return datetime.datetime.now().strftime(fmt)


# returns names of all files in given directory
def getFilesInDirectory(directory):
    return os.listdir(directory)


# write lstm or word2vec accuracies and losses to csv
def resultsToCSV(parcel, lstm_info, csv_losses_dir, csv_accuracies_dir=None):

    timestamp = timeStampedFileName()

    losses = parcel[0] if csv_accuracies_dir else parcel
    lss_csv_file = csv_losses_dir + 'lss_' + lstm_info + '_date_' + timestamp + '.csv'
    writeDataToCSV(losses, lss_csv_file)

    if csv_accuracies_dir:

        if len(parcel) == 1:
            return

        accuracies   = parcel[1]
        acc_csv_file = csv_accuracies_dir + 'acc_' + lstm_info + '_date_' + timestamp + '.csv'
        writeDataToCSV(accuracies, acc_csv_file)


# read file containing mapping of words to (pretrained) vectors
def readVectorsDict(dict_file_path, reverse=False):

    lines = []
    for line in open(dict_file_path, encoding="utf8"):
        lines.append(line)

    num_vectors = np.int_(lines[0].split()[0])
    vector_size = np.int_(lines[0].split()[1])
    num_vec_req = np.int_(lines[0].split()[2])

    vector_dict = dict()
    for i in range(1,num_vectors+1):
        vector = lines[i].split()
        if not reverse:
            vector_dict[vector[0]] = vector[1:]
        if reverse:
            key = getReverseDictKey(vector)
            vector_dict[key] = vector[0]

    return vector_dict, (num_vectors, vector_size, num_vec_req)


# returns the vector in form of a parsed string, which is then used as the reverse ditionary key
def getReverseDictKey(vector):

    count = 0
    for element in vector:
        if len(element) > 5 and count > 0:
            vector[count] = element[0:5]
        count += 1
    key = str(vector[1:]).replace("'", "").replace(",", "").replace(" ", "").replace("0", "")

    return key


# read the words to be replaced in the primary vector file
def readKeyTable(replacement_table_file_path):
    table = []
    for line in open(replacement_table_file_path, encoding="utf8"):
        table.append(line.replace("\n",""))
    return table


# read the first x files in a directory
def readSpecifiedNumberOfFiles(numFiles,path):
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

    for i in range(0,numFiles):
        files[i] = path + files[i]

    return files[0:numFiles]