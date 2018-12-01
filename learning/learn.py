from nameSimilarity import generateNameSimilarity
from locationSimilarity import generateLocationSimilarity
from tagsSimilarity import generateTagsSimilarity
from negativeDataGen import generateNegativeDataPairs
from similarityMatrixGen import generateSimilarityMatrix


if __name__ == "__main__":
    redo = True

    # --- data pre-processing ---

    generateNegativeDataPairs()

    generateNameSimilarity(redo)
    generateTagsSimilarity(redo)
    # generateLocationSimilarity(redo)

    generateSimilarityMatrix()
