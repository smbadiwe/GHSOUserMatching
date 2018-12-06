from nameSimilarity import generateNameSimilarity
from locationSimilarity import generateLocationSimilarity
from descVsComment import generateDescCommentSimilarity
from descVsAboutme import generateDescAboutMeSimilarity
from dateSimilarity import generateDateSimilarity
from tagsSimilarity import generateTagsSimilarity
from negativeDataGen import generateNegativeDataPairs
from similarityMatrixGen import generateSimilarityMatrix
from classifierLearning import startLearning
from runSqlCreateScripts import runSqlScripts
from predict import makePrediction, generatePredictionsCsvFile
from plots import getData, plotRocCurve, plotConfusionMatrix
from timeit import default_timer as timer
import os
import yaml


if __name__ == "__main__":
    file = os.path.join(os.path.dirname(__file__), "../config.yml")
    with open(file, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    rerun = bool(cfg["rerun"])  # if true, all data is deleted and regenerated
    train_size = int(cfg["train_size"])  # number of train data samples
    prediction_size = int(cfg["test_size"])   # number of test data samples
    models = cfg["models"]
    features = cfg["features"]
    print("Config file loaded.\nrerun: {}\nfeatures: {}.\nmodels: {}\ntrain_size: {}, test_size: {}".format(rerun, features, models, train_size, prediction_size))

    total_time = 0
    # --- data pre-processing ---
    start = timer()
    runSqlScripts(cfg, train_size, prediction_size)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    start = timer()
    generateNegativeDataPairs(cfg, rerun)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    if "dates" in features:
        start = timer()
        generateDateSimilarity(cfg, rerun)
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    if "desc_comment" in features:
        start = timer()
        generateDescCommentSimilarity(cfg, rerun)
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    if "user_names" in features:
        start = timer()
        generateNameSimilarity(cfg, rerun)
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    if "tags" in features:
        start = timer()
        generateTagsSimilarity(cfg, rerun)
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    if "locations" in features:
        start = timer()
        generateLocationSimilarity(cfg, rerun)
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    if "desc_aboutme" in features:
        start = timer()
        generateDescAboutMeSimilarity(cfg, rerun)
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    start = timer()
    generateSimilarityMatrix(cfg, features)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    # --- end data pre-processing ---

    start = timer()
    startLearning(cfg)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    # Make predictions
    for model in models:
        start = timer()
        try:
            makePrediction(cfg, model, features, prediction_size, delete_old_data=True, save_to_file=False)
        except Exception as ex:
            print("Failure making prediction using {} model.\n{}\n".format(model, ex))
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    # generate the predictions as CSV file for analyses

    start = timer()
    generatePredictionsCsvFile(cfg)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    # generate charts and save to file

    for model in models:
        start = timer()
        try:
            data = getData(model, prediction_size)
            plotConfusionMatrix(data, model)
            plotRocCurve(data, model)
        except Exception as ex:
            print("Failure generating plots for {} model.\n{}\n".format(model, ex))
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    print("Total time taken: {} seconds\n=== ALL DONE!===".format(total_time))
