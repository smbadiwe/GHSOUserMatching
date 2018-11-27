# -*- coding: utf-8 -*-
import psycopg2 as psql
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.feature_extraction.text import TfidfVectorizer
import sys
sys.path.insert(0, '../db_utils')
from db_utils.dbConnection import get_db_config

def main():
	cfg = get_db_config()
	con = psql.connect(host=cfg["host"], user=cfg["user"], database=cfg["database"], password=cfg["password"])
	cur = con.cursor()
	# con = psql.connect(host="localhost", user='postgres', database="gh_so", password="123andro321")
	# cur = con.cursor()

	### create table for description-vs-aboutme similarity
	cur.execute('''
		create table similarities_among_desc_aboutme
			(g_id int, s_id int, similarity float8, primary key(g_id, s_id))
	''')

	### TF-IDF vectorizer
	tfidf = TfidfVectorizer(stop_words='english')

	### Load user info of GitHub
	cur.execute('''
		select distinct l.g_id, u.description
		from user_project_description u, labeled_data l 
		where u.description != '' and u.user_id = l.g_id
	''')
	g_users = {}
	for c in cur.fetchall():
		if c[0] in g_users:
			g_users[c[0]] += " " + c[1]
		else:
			g_users[c[0]] = c[1]
	g_keys = g_users.keys()

	### Load user info of Stack Overflow
	cur.execute('''
		select distinct l.s_id, u.about_me
		from so_users u, labeled_data l
		where u.about_me != '' and u.id = l.s_id
	''')
	s_users = {}
	for c in cur.fetchall():
		s_users[c[0]] = c[1]
	s_keys = s_users.keys()

	### TF-IDF computation
	values = []
	values.extend(g_users.values())
	values.extend(s_users.values())
	vecs = tfidf.fit_transform(values)

	### TF-IDF vectors of GH users
	g_vecs = vecs[:len(g_keys),:]

	### TF-IDF vectors of SO users
	s_vecs = vecs[len(g_keys):,:]

	### similarities between vectors
	sims = pairwise_distances(g_vecs, s_vecs, metric='cosine')

	### store similarities
	cur.execute('''
		select distinct l.g_id, l.s_id
		from user_project_description g, labeled_data l, so_users s
		where g.description != '' and g.user_id = l.g_id
			and s.about_me != '' and s.id = l.s_id
	''')
	pairs = cur.fetchall()
	for p in pairs:
		cur.execute('''
			insert into similarities_among_desc_aboutme
			values (%s, %s, %s)
		''', (p[0], p[1], 1-sims[g_keys.index(p[0])][s_keys.index(p[1])]) )

	con.commit()
	con.commit()
	cur.close()
	con.close()


if __name__ == "__main__":
	main()
	print("Done")
