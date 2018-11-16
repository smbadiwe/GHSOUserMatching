# -*- coding: utf-8 -*-

import psycopg2 as psql
from scipy.sparse import lil_matrix
from scipy import io

def main():
	con = psql.connect('dbname=gh_so')
	cur = con.cursor()

	### Load pairs of GH users and SO users
	cur.execute('''
		select g_id, s_id
		from labeled_data
		order by g_id, s_id
	''')
	pairs = [(x[0], x[1]) for x in cur.fetchall()]

	### Features of pairs
	attrs = [
		'dates',
		'desc_aboutme',
		'desc_comment',
		'desc_pbody',
		'desc_ptitle',
		'desc_ptags',
		'locations',
		'user_names'
	]

	### Matrix generation
	S = lil_matrix((len(pairs), len(attrs)))
	for attr in attrs:
		cur.execute('''
			select g_id, s_id, similarity
			from similarities_among_%s
		''' % attr)
		for c in cur.fetchall():
			S[pairs.index((c[0], c[1])), attrs.index(attr)] = c[2]
	io.mmwrite('s.mtx', S)

	cur.close()
	con.close()



if __name__ == "__main__":
    main()
