from nameSimilarity import generateNameSimilarity
from locationSimilarity import generateLocationSimilarity
from descVsComment import generateDescCommentSimilarity
from descVsAboutme import generateDescAboutMeSimilarity
from dateSimilarity import generateDateSimilarity
from tagsSimilarity import generateTagsSimilarity
from negativeDataGen import generateNegativeDataPairs
from similarityMatrixGen import generateSimilarityMatrix
from classifierLearning import startLearning

if __name__ == "__main__":
    redo = True

    # --- data pre-processing ---

    #generateNegativeDataPairs(redo)

    #generateDateSimilarity(redo)
    #generateDescCommentSimilarity(redo)
    #generateNameSimilarity(redo)
    #generateTagsSimilarity(redo)
    #generateLocationSimilarity(redo)
    #generateDescAboutMeSimilarity(redo)

    #generateSimilarityMatrix()

    # --- end data pre-processing ---

    startLearning()
