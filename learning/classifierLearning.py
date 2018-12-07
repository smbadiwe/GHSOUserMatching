# -*- coding: utf-8 -*-

import psycopg2 as psql
from scipy.sparse import lil_matrix
from scipy import io
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from appUtils import getDbConnection
from sklearn.externals import joblib
import os


root_dir = os.path.join(os.path.dirname(__file__), "../")


def startLearning(cfg, file_append):
	print("\n===========\nRUNNING startLearning()\n===========\n")
	model_dir = "{}models/{}".format(root_dir, file_append)
	if not os.path.isdir(model_dir):
		os.makedirs(model_dir)

	con, cur = getDbConnection(cfg)
	
	### Preparing labels of pairs
	print("Preparing labels of pairs")
	cur.execute('''
		select g_id, s_id, label
		from labeled_data
		order by g_id, s_id
	''')
	label_list = [x[2] for x in cur.fetchall()] 
	labels = lil_matrix((len(label_list), 1))
	for i in range(len(label_list)):
		labels[i, 0] = label_list[i]
	labels = labels.toarray().ravel()

	### Load similarity matrix
	print("Load similarity matrix")
	S = io.mmread(root_dir + 'data/{}.s.mtx'.format(file_append))
	S = S.toarray()

	### Learn linear regression classifier
	print("Learn linear regression classifier")
	clf = LinearRegression()
	clf.fit(S, labels)
	joblib.dump(clf, model_dir + '/lr.pkl')

	### Learn kNN classifier
	print("Learn kNN classifier")
	clf = KNeighborsClassifier()
	clf.fit(S, labels)
	joblib.dump(clf, model_dir + '/knn.pkl')

	### Learn logistic regression classifier
	print("Learn logistic regression classifier")
	clf = LogisticRegression()
	clf.fit(S, labels)
	joblib.dump(clf, model_dir + '/lg.pkl')

	### Learn random forest classifier
	print("Learn random forest classifier")
	clf = RandomForestClassifier(n_estimators=100)
	clf.fit(S, labels)
	joblib.dump(clf, model_dir + '/rf.pkl')

	### Learn gradient boosting decision tree classifier
	print("Learn gradient boosting decision tree classifier")
	clf = GradientBoostingClassifier(n_estimators=100)
	clf.fit(S, labels)
	joblib.dump(clf, model_dir + '/gbdt.pkl')

	cur.close()
	con.close()

	if bool(cfg["zipModel"]):
		try:
			print("\nDone. Now zip the models")
			import zipfile
			with zipfile.ZipFile(model_dir + "_models.zip", "w", zipfile.ZIP_DEFLATED) as zf:
				abs_src = os.path.abspath(model_dir)
				for dirname, subdirs, files in os.walk(model_dir):
					for filename in files:
						absname = os.path.abspath(os.path.join(dirname, filename))
						arcname = absname[len(abs_src) + 1:]
						print('zipping %s as %s' % (os.path.join(dirname, filename), arcname))
						zf.write(absname, arcname)
		except Exception as ex:
			print(ex)
			print("That was error zipping file. Continuing...")
		
	print("===========End startLearning()============")
