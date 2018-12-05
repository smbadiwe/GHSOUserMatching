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


if __name__ == "__main__":
    redo = True  # if true, all data is deleted and regenerated
    train_size = 10000  # #train data samples
    prediction_size = 200  # #prediction data samples
    models = ["rf", "gbdt", "knn", "lg"]
    # NB: linear regression - lr - does not have probabilities. It'll fail if you use it
    features = [
        'dates',
        'desc_aboutme',
        'desc_comment',
        # 'desc_pbody',
        # 'desc_ptitle',
        'locations',
        'tags',
        'user_names'
    ]

    total_time = 0
    # --- data pre-processing ---
    start = timer()
    runSqlScripts(train_size, prediction_size)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    start = timer()
    generateNegativeDataPairs(redo)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    if "dates" in features:
        start = timer()
        generateDateSimilarity(redo)
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    if "desc_comment" in features:
        start = timer()
        generateDescCommentSimilarity(redo)
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    if "user_names" in features:
        start = timer()
        generateNameSimilarity(redo)
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    if "tags" in features:
        start = timer()
        generateTagsSimilarity(redo)
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    if "locations" in features:
        start = timer()
        generateLocationSimilarity(redo)
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    if "desc_aboutme" in features:
        start = timer()
        generateDescAboutMeSimilarity(redo)
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    start = timer()
    generateSimilarityMatrix(features)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    # --- end data pre-processing ---

    start = timer()
    startLearning()
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    # Make predictions
    for model in models:
        start = timer()
        try:
            makePrediction(model, features, prediction_size, delete_old_data=True, save_to_file=False)
        except Exception as ex:
            print("Failure making prediction using {} model.\n{}\n".format(model, ex))
        end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    # generate the predictions as CSV file for analyses

    start = timer()
    generatePredictionsCsvFile()
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
