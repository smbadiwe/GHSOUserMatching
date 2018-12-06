import matplotlib.pyplot as plt
import scikitplot as skplt
import csv
import numpy as np
import os


root_dir = os.path.join(os.path.dirname(__file__), "../")


def getData(model, n_samples):
    # w.write("g_id, s_id, true_label, model, predicted_label, probability\n")
    res = {
        "g_id": [None] * n_samples,
        "s_id": [None] * n_samples,
        "true_label": [None] * n_samples,
        "predicted_label": [None] * n_samples,
        "probability": [None] * n_samples
    }
    i = -1
    j = 0
    with open(root_dir + "data/predictions_all.csv", 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            i += 1
            if row[3] != model or i == 0:
                continue
            res["g_id"][j] = int(row[0])
            res["s_id"][j] = int(row[1])
            res["true_label"][j] = int(row[2])
            res["predicted_label"][j] = int(row[4])
            res["probability"][j] = float(row[5])
            j += 1
    return res


def getProba(data):
    length = len(data["g_id"])
    res = np.empty(shape=(length, 2))
    for i in range(length):
        proba = data["probability"][i]
        if data["predicted_label"][i] == 0:
            res[i] = [proba, 1 - proba]
        else:
            res[i] = [1 - proba, proba]
    return res


def plotConfusionMatrix(data, model):
    print("Generating Confusion Matrix for {}".format(model))
    skplt.metrics.plot_confusion_matrix(data["true_label"], data["predicted_label"],
                                        labels=[0,1], title="Confusion Matrix - {}".format(model))
    plt.savefig(root_dir + "data/confusion_matrix_{}.png".format(model))
    print("Confusion Matrix for {} generated and saved to file".format(model))


def plotRocCurve(data, model):
    print("Generating ROC Curve for {}".format(model))
    skplt.metrics.plot_roc(data["true_label"], getProba(data),
                           title="ROC Curve - {}".format(model))
    plt.savefig(root_dir + "data/roc_curve_{}.png".format(model))
    print("ROC Curve for {} generated and saved to file".format(model))
