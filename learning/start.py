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
import gc

if __name__ == "__main__":
    redo = True  # if true, all data is deleted and regenerated
    train_size = 10000  # #train data samples
    prediction_size = 200  # #prediction data samples
    model = "rf"
    # model = "lr"
    # model = "lg"
    # model = "knn"
    # model = "gbdt"
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

    # --- data pre-processing ---
    runSqlScripts(train_size, prediction_size)
    generateNegativeDataPairs(redo)

    generateDateSimilarity(redo)
    gc.collect()
    generateDescCommentSimilarity(redo)
    gc.collect()
    generateNameSimilarity(redo)
    gc.collect()
    generateTagsSimilarity(redo)
    gc.collect()
    generateLocationSimilarity(redo)
    gc.collect()
    generateDescAboutMeSimilarity(redo)
    gc.collect()

    generateSimilarityMatrix(features)
    gc.collect()

    # --- end data pre-processing ---

    startLearning()
    gc.collect()

    # Make predictions

    makePrediction(model, features, prediction_size)
