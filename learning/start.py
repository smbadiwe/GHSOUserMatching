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
from predict import makePrediction
from timeit import default_timer as timer
#import gc

if __name__ == "__main__":
    redo = True  # if true, all data is deleted and regenerated
    train_size = 10000  # #train data samples
    prediction_size = 200  # #prediction data samples
    models = ["rf", "lr", "lg", "knn", "gbdt"]
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

    start = timer()
    generateDateSimilarity(redo)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    start = timer()
    generateDescCommentSimilarity(redo)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    start = timer()
    generateNameSimilarity(redo)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    start = timer()
    generateTagsSimilarity(redo)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    start = timer()
    generateLocationSimilarity(redo)
    end = timer()
    elapsed = end - start
    total_time += elapsed
    print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

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
        makePrediction(model, features, prediction_size, redo)end = timer()
        elapsed = end - start
        total_time += elapsed
        print("Time taken: {}. Total Time Taken: {}".format(elapsed, total_time))

    print("=== ALL DONE!===")
