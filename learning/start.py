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


def preProcess(cfg):
    total_time = 0
    # --- data pre-processing ---
    rerun = bool(cfg["rerun"])  # if true, all data is deleted and regenerated
    features = cfg["features"]
    train_size = int(cfg["train_size"])  # number of train data samples
    prediction_size = int(cfg["test_size"])  # number of test data samples

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

    # --- end data pre-processing ---
    return total_time


def generateCharts(models, prediction_size, total_time, file_append):
    # generate charts and save to file
    for model in models:
        start = timer()
        try:
            data = getData(model, prediction_size, file_append)
            plotConfusionMatrix(data, model, file_append)
            plotRocCurve(data, model, file_append)
        except Exception as ex:
            print("Failure generating plots for {} model.\n{}\n".format(model, ex))
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))
    return total_time


def testModels(cfg, features, total_time):
    file_append = "with_tags" if "tags" in features else "without_tags"
    print("making predictions - {}".format(file_append))
    models = cfg["models"]
    prediction_size = int(cfg["test_size"])  # number of test data samples
    for model in models:
        start = timer()
        try:
            makePrediction(cfg, model, features, prediction_size, file_append, delete_old_data=True, save_to_file=False)
        except Exception as ex:
            print("Failure making prediction {} using {} model.\n{}\n".format(file_append, model, ex))
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    # generate the predictions as CSV file for analyses
    start = timer()
    generatePredictionsCsvFile(cfg, file_append)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    do_charts = bool(cfg["doCharts"])
    if do_charts:
        # Generate charts
        total_time = generateCharts(models, prediction_size, total_time, file_append)

    return total_time


def learnAndPredict(cfg, features, total_time):
    file_append = "with_tags" if "tags" in features else "without_tags"

    start = timer()
    generateSimilarityMatrix(cfg, features)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    # train
    start = timer()
    startLearning(cfg, file_append)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    # Make predictions
    total_time = testModels(cfg, features, total_time)
    
    return total_time


if __name__ == "__main__":
    root = os.path.join(os.path.dirname(__file__), "../")
    with open(root + "config.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    rerun = bool(cfg["rerun"])  # if true, all data is deleted and regenerated
    models = cfg["models"]
    features = cfg["features"]
    train_size = int(cfg["train_size"])  # number of train data samples
    prediction_size = int(cfg["test_size"])  # number of test data samples
    print("Config file loaded.\nrerun: {}\nfeatures: {}.\nmodels: {}\ntrain_size: {}, test_size: {}"
          .format(rerun, features, models, train_size, prediction_size))

    # pre-process
    total_time = preProcess(cfg)

    # train, learn and predict

    # with tags
    total_time = learnAndPredict(cfg, features, total_time)
    
    if "tags" in features:
        # without tags
        features = features.remove("tags")
        print("\n=======Rerunning WITHOUT tags============\n")
        total_time = learnAndPredict(cfg, features, total_time)

    print("Total time taken: {} seconds\nAll generated files are in '{}' folder\n\n=== ALL DONE!===".format(total_time, root + "data"))
