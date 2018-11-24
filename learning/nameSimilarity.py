# -*- coding: utf-8 -*-

import psycopg2 as psql
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def main():
	con =psql.connect(host="localhost", user='postgres', database="gh_so", password="123andro321")
	cur = con.cursor()

	### create table for name similarity
	cur.execute('''
		create table similarities_among_user_names
			(g_id int, s_id int, similarity float8, primary key(g_id, s_id))
	''')

	cur.execute('''
		create temp table similarities_among_names
			(g_name text, s_name text, similarity float8)
	''')

	### names of GH users
	cur.execute('''
		select distinct u.name
		from labeled_data l, users u
		where l.g_id = u.id and u.name != ''
	''')
	gh_users = [r[0] for r in cur.fetchall()]

	### names of SO users
	cur.execute('''
		select distinct u.display_name
		from labeled_data  l, so_users u
		where l.s_id = u.id and u.display_name != ''
	''')
	so_users = [r[0] for r in cur.fetchall()]

	### combining all names to construct a trigram space
	users = []
	users.extend(gh_users)
	users.extend(so_users)
	users = list(set(users))

	### trigrams for each text
	trigrams = []
	name_trigrams = {}
	for txt in users:
		t = list(txt)
		name_trigrams[txt] = [] 
		for i in range(0, len(t) - 3):
			tg = "".join(t[i:i+3])
			trigrams.append(tg)
			name_trigrams[txt].append(tg)
	trigrams = list(set(trigrams))

	### vectorizing names by trigram
	vectors = {}
	for name in name_trigrams.keys():
		vec = np.zeros(len(trigrams))
		for tri in name_trigrams[name]:
			vec[trigrams.index(tri)] = 1
		vectors[name] = vec

	### similarities between names
	cur.execute('''
		select distinct g_name, s_name
		from labeled_data
		where g_name != ''
			and s_name != ''
	''')
	pairs = cur.fetchall()
	for p in pairs:
		gv = np.array(vectors[p[0]]) 
		sv = np.array(vectors[p[1]])
		sim = cosine_similarity(gv, sv)
		cur.execute('''
			insert into similarities_among_names
			values (%s, %s, %s)
		''', (p[0], p[1], sim[0][0]))
		con.commit()

	### store similarities between GH and SO users	
	cur.execute('''
		insert into similarities_among_user_names
		select g.id, s.id, c.similarity
		from users g, so_users s, similarities_among_names c
		where g.name = c.g_name and s.name = c.s_name
	''')

	con.commit()
	cur.close()
	con.close()

if __name__ == "__main__":
    main()
