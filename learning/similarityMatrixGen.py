# -*- coding: utf-8 -*-

import psycopg2 as psql
from scipy.sparse import lil_matrix
from scipy import io
from appUtils import getDbConfig


def generateSimilarityMatrix(features):
	print("\n===========\nRUNNING generateSimilarityMatrix()\n===========\n")
	cfg = getDbConfig()
	con = psql.connect(host=cfg["host"], user=cfg["user"], database=cfg["database"], password=cfg["password"])
	cur = con.cursor()

	### Load pairs of GH users and SO users
	cur.execute('''
		select g_id, s_id
		from labeled_data
		order by g_id, s_id
	''')
	pairs = [(x[0], x[1]) for x in cur.fetchall()]

	### Matrix generation
	S = lil_matrix((len(pairs), len(features)))
	for attr in features:
		print("Processing {} similarity".format(attr))
		cur.execute('''
			select g_id, s_id, similarity
			from similarities_among_%s
		''' % attr)
		for c in cur.fetchall():
			if (c[0], c[1]) in pairs:
				S[pairs.index((c[0], c[1])), features.index(attr)] = c[2]
	io.mmwrite('../data/s.mtx', S)

	cur.close()
	con.close()
	print("=========End generateSimilarityMatrix()========")
