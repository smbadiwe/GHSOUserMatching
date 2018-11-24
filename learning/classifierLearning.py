# -*- coding: utf-8 -*-

import psycopg2 as psql
from scipy.sparse import lil_matrix
from scipy import io
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

from sklearn.externals import joblib

def main():
	con = psql.connect('dbname=gh_so')
	cur = con.cursor()

	### Prepating labels of pairs
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
	S = io.mmread('../data/s.mtx')
	S = S.toarray()

	### Learn linear regression classifier
	clf = LinearRegression()
	clf.fit(S, labels)
	joblib.dump(clf, '../models/lr.pkl')

	### Learn kNN classifier
	clf = KNeighborsClassifier()
	clf.fit(S, labels)
	joblib.dump(clf, '../models/knn.pkl')

	### Learn logistic regression classifier
	clf = LogisticRegression()
	clf.fit(S, labels)
	joblib.dump(clf, '../models/lg.pkl')

	### Learn random foresrt classifier
	clf = RandomForestClassifier(n_estimators=100)
	clf.fit(S, labels)
	joblib.dump(clf, '../models/rf.pkl')

	### Learn gradient boosting decision tree classifier
	clf = GradientBoostingClassifier(n_estimators=100)
	clf.fit(S, labels)
	joblib.dump(clf, '../models/gbdt.pkl')


	cur.close()
	con.close()




if __name__ == "__main__":
    main()
