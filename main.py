import torch
import time
import ndjson
import jsonlines
from enum import IntEnum
from utilities.utilities import Mode, weightInit, Vec, labelType
from utilities import utilities, plotgraphs, paths, display, duplicator, output
from word2vec.trainer import Word2VecTrainer
from lstm.trainer import LSTMTrainer
from similarity.cosine import CosineSimilarity

class labelType(IntEnum):
    property_type     = 0
    tenement_steading = 1 
    exclusive_strata  = 2                       
    exclusive_solum   = 3
    common_strata     = 4
    common_solum      = 5
    additional_info   = 6
    char_count        = 7  


if __name__ == '__main__':

    start   = time.time()
    loading = start
    
    # init paths
    ros = paths.RosDataPaths(100, 100)
    
    # set mode of operation
    mode       = Mode.lstm
    save_model = True
    confusion  = True
    
    #train = output.OutputMatrix('./data/lstm/training/vectors/trainsetlabels/')
    #test  = output.OutputMatrix('./data/lstm/training/vectors/testsetlabels/')
    
    if mode == Mode.display:
        display = display.Display(ros.docpath, ros.docfile_flats, 200, houses=False)
        display.run()
        #display.displayAnnotationInfo()
        exit(0)
    
    
    if mode == Mode.word2vec:
    
        # word2vec training parameters
        w2v = Word2VecTrainer(ros.keyword_path,
                              primary_files=ros.docfile_flats,
                              emb_dimension=50,
                              batch_size=32,
                              window_size=7,
                              initial_lr=0.01,
                              min_count=1)
                              
        # train standard word2vec -> train function outputs dictionary at the end
        loading  = time.time()
        parcel_0 = w2v.train(ros.docfile_flats, ros.dict_file, num_epochs=100)
        
        # write training results (learning curve) to csv
        utilities.resultsToCSV(parcel_0, w2v.toString(), ros.w2v_csv_lss_dir)
        
        # save model if specified
        if save_model:
            path = ros.w2v_model_param + w2v.toString() + '_date_' + utilities.timeStampedFileName()
            torch.save(w2v.skip_gram_model.state_dict(), path)
        

    if mode == Mode.conversion:
    
        # convert documents into vector representation and save to different file location                
        duplication = duplicator.Duplicate(ros.docfile_flats, 1)    # 31 and 59
        duplication.convert(100, ros.dict_file, ros.vec_files_train, ros.vec_files_train_labels,   0, labelSelection=None)
        duplication.convert(100, ros.dict_file, ros.vec_files_test,  ros.vec_files_test_labels,  100, labelSelection=None)
        
        # utilities.ndjsonVectorisation(ros.testing,  ros.vec_files_test,  ros.vec_files_test_labels  ,ros.dict_file, unknown_vec=Vec.skipVec)
        # utilities.ndjsonVectorisation(ros.training, ros.vec_files_train, ros.vec_files_train_labels, ros.dict_file, unknown_vec=Vec.skipVec)
        exit(0)


    if mode == Mode.lstm:

        # lstm training parameters
        lstm = LSTMTrainer(ros.vec_files_train,
                           ros.vec_files_train_labels,
                           ros.vec_files_test,
                           ros.vec_files_test_labels,
                           learning_rate=0.01,
                           iterations_per_epoch=100,
                           input_dim=75,
                           category=labelType.exclusive_strata,
                           hidden_dim=30,
                           layer_dim=1,
                           output_dim=2)

        # train lstm
        loading = time.time()
        parcel  = lstm.train(num_epochs=100, compute_accuracies=False)

        # save model if specified
        if save_model:
            path = ros.lstm_model_param + lstm.to_string + '_date_' + utilities.timeStampedFileName()
            torch.save(lstm.model.state_dict(), path)

        # write results to csv
        utilities.resultsToCSV(parcel, lstm.to_string, ros.lstm_csv_lss_dir, ros.lstm_csv_acc_dir)

        # write confusion matrix as image to output
        if confusion:
            
            # test set
            labels, accuracy = lstm.evaluateModel(test_samples=100, test=True)
            print("Accuracy Test Set: {}".format(accuracy))
            class_names = [0, 1]
            plotgraphs.plot_confusion_matrix(labels[0], labels[1], ros.confusion_matrix, classes=class_names,
                                                title='Confusion matrix, without normalization')
            
            # training set
            labels, accuracy = lstm.evaluateModel(test_samples=100, test=False)
            print("Accuracy Training Set: {}".format(accuracy))
            plotgraphs.plot_confusion_matrix(labels[0], labels[1], ros.confusion_matrix, classes=class_names,
                                                title='Confusion matrix, without normalization')
            
            
    if mode == Mode.similarity:
        path = ros.sim_img_dir + utilities.timeStampedFileName() + '.bmp'
        measure_similarity = CosineSimilarity(p.imdb_files_neg_train, ros.dict_file)
        measure_similarity.angularDistancesToFile(path)
            
            
    if mode == Mode.plot:
        
        w2v_lss_y_range  = [ 0.0, 4.0]
        lstm_lss_y_range = [-0.2, 2.0]
        lstm_acc_y_range = [-0.1, 1.1]
        
        plotgraphs.convertCsvToGraphs(ros.w2v_csv_lss_dir,  ros.w2v_graph_lss_dir,  w2v_lss_y_range,  'Log-sigmoid loss')
        plotgraphs.convertCsvToGraphs(ros.lstm_csv_lss_dir, ros.lstm_graph_lss_dir, lstm_lss_y_range, 'Cross-entropy loss')
        plotgraphs.convertCsvToGraphs(ros.lstm_csv_acc_dir, ros.lstm_graph_acc_dir, lstm_acc_y_range, 'Accuracy in percent')
        
        
    end = time.time()
    
    print("Time needed for loading data {} seconds".format(round(loading - start)))
    print("Time needed for processing {} seconds".format(round(end - loading)))
    print("Total time {} seconds".format(round(end - start)))
