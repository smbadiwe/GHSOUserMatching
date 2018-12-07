# -*- coding: utf-8 -*-

import psycopg2 as psql
from scipy.sparse import lil_matrix
from scipy import io
from appUtils import getDbConnection
import os

def generateSimilarityMatrix(cfg, features):
	print("\n===========\nRUNNING generateSimilarityMatrix()\n===========\n")
	con, cur = getDbConnection(cfg)
	### Load pairs of GH users and SO users
	cur.execute('''
		select g_id, s_id
		from labeled_data
		order by g_id, s_id
	''')
	pairs = [(x[0], x[1]) for x in cur.fetchall()]

	### Matrix generation
	S = lil_matrix((len(pairs), len(features)))
	with_tags = False
	for attr in features:
		print("Processing {} similarity".format(attr))
		if attr == "tags":
			with_tags = True
		cur.execute('''
			select g_id, s_id, similarity
			from similarities_among_%s
		''' % attr)
		for c in cur.fetchall():
			if (c[0], c[1]) in pairs:
				S[pairs.index((c[0], c[1])), features.index(attr)] = c[2]

	file_append = "with_tags" if with_tags else "without_tags"
	print("Writing similarity matrix to file")
	root_dir = os.path.join(os.path.dirname(__file__), "../")
	io.mmwrite(root_dir + 'data/{}/s.mtx'.format(file_append), S)

	print("Closing connection")
	cur.close()
	con.close()
	print("=========End generateSimilarityMatrix()========")
