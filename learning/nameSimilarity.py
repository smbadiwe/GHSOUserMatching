# -*- coding: utf-8 -*-

import psycopg2 as psql
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import gc
import sys
sys.path.insert(0, '../db_utils')
from db_utils.dbConnection import get_db_config

def main():
	cfg = get_db_config()
	con = psql.connect(host=cfg["host"], user=cfg["user"], database=cfg["database"], password=cfg["password"])
	cur = con.cursor()

	### create table for name similarity
	cur.execute('''
		create table if not exists similarities_among_user_names
			(g_id int, s_id int, similarity float8, primary key(g_id, s_id))
	''')
	print("created table similarities_among_user_names")
	cur.execute('''
		drop table if exists similarities_among_names
	''')
	cur.execute('''
		create temp table similarities_among_names
			(g_name text, s_name text, similarity float8)
	''')
	print("created table similarities_among_names")
	### names of GH users
	cur.execute('''
		select distinct u.name
		from labeled_data l, users u
		where l.g_id = u.id and u.name != ''
	''')
	gh_users = [r[0] for r in cur.fetchall()]
	print("read names of GH users")
	### names of SO users
	cur.execute('''
		select distinct u.display_name
		from labeled_data  l, so_users u
		where l.s_id = u.id and u.display_name != ''
	''')
	so_users = [r[0] for r in cur.fetchall()]
	print("read names of SO users")
	### combining all names to construct a trigram space
	users = []
	users.extend(gh_users)
	users.extend(so_users)
	users = list(set(users))
	print("combined users list")

	### trigrams for each text
	trigrams = []
	name_trigrams = {}
	for txt in users:
		i_count = len(txt) - 3
		name_trigrams[txt] = [None] * i_count
		for i in range(0, i_count):
			tg = txt[i:i+3]
			trigrams.append(tg)
			name_trigrams[txt][i] = tg
	trigrams = list(set(trigrams))

	### vectorizing names by trigram
	len_trigrams = len(trigrams)
	print("constructed trigram. len_trigrams = {}. len_name_trigrams = {}".format(len_trigrams, len(name_trigrams)))
	vectors = {}
	cnt = 0
	for name in list(name_trigrams.keys()):
		vec = [0] * len_trigrams
		for tri in name_trigrams[name]:
			vec[trigrams.index(tri)] = 1
		vectors[name] = vec
		del name_trigrams[name]
		del vec
		if cnt % 2500 == 0 or (cnt > 70000 and cnt % 1000 == 0):
			print("Iteration: {}. Name: {}".format(cnt, name))
		if cnt % 10000 == 0:
			print("Collecting GC at Iteration: {}. Name: {}".format(cnt, name))
			gc.collect()
		cnt += 1
	gc.collect()

	print("constructed vectors for vectorizing names by trigram")
	### similarities between names
	cur.execute('''
		select distinct g_name, s_name
		from labeled_data
		where g_name != ''
			and s_name != ''
	''')
	pairs = cur.fetchall()
	for p in pairs:
		gv = np.array(vectors[p[0]]).reshape(-1, 1)
		sv = np.array(vectors[p[1]]).reshape(-1, 1)
		sim = cosine_similarity(gv, sv)
		cur.execute('''
			insert into similarities_among_names
			values (%s, %s, %s)
		''', (p[0], p[1], sim[0][0]))
		con.commit()

	print("similarities_among_names processed")
	### store similarities between GH and SO users	
	cur.execute('''
		insert into similarities_among_user_names
		select g.id, s.id, c.similarity
		from users g, so_users s, similarities_among_names c
		where g.name = c.g_name and s.name = c.s_name
	''')

	print("similarities_among_user_names processed")
	print("Commit and close connection")
	con.commit()
	cur.close()
	con.close()
	print("End")

if __name__ == "__main__":
    main()
