from nameSimilarity import generateNameSimilarity
from negativeDataGen import generateNegativeDataPairs


if __name__ == "__main__":
    generateNegativeDataPairs()

    redoSimilarity = False
    generateNameSimilarity(redoSimilarity)
    generateLocationSimilarity(redoSimilarity)
