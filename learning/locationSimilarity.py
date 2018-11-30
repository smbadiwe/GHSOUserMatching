# -*- coding: utf-8 -*-

import psycopg2 as psql
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.feature_extraction.text import TfidfVectorizer
from dbConnection import get_db_config


def generateLocationSimilarity(redoSimilarity=False):
    print("\n===========\nRUNNING generateLocationSimilarity()\n===========\n")
    cfg = get_db_config()
    con = psql.connect(host=cfg["host"], user=cfg["user"], database=cfg["database"], password=cfg["password"])
    cur = con.cursor()

    ### create table for location similarity
    cur.execute('''
		create table if not exists similarities_among_locations
			(g_id int, s_id int, similarity float8, primary key(g_id, s_id))
	''')

    # Check if done before
    if not redoSimilarity:
        cur.execute('select g_id from similarities_among_locations limit 1')
        existing = [r[0] for r in cur.fetchall()]
        if len(existing) > 0:
            print("similarities_among_locations has already been generated")
            return

    ### TF-IDF vectorizer
    tfidf = TfidfVectorizer(stop_words='english')

    ### Load user info of GitHub
    cur.execute('''
		select distinct l.g_id, u.location
		from labeled_data l, users u
		where l.g_id = u.id and u.location != ''
	''')
    g_users = {}
    for c in cur.fetchall():
        g_users[c[0]] = c[1]
    g_keys = g_users.keys()

    ### Load user info of Stack Overflow
    cur.execute('''
		select distinct l.s_id, u.location
		from labeled_data l, so_users u
		where l.s_id = u.id and u.location != ''
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

    ### vectors of GH users
    g_vecs = vecs[:len(g_keys), :]

    ### vectors of SO users
    s_vecs = vecs[len(g_keys):, :]

    ### similarities between vectors
    sims = pairwise_distances(g_vecs, s_vecs, metric='cosine')

    ### store similarities
    cur.execute('''
		select distinct g_id, s_id
		from labeled_data l, users g, so_users s
		where l.g_id = g.id and l.s_id = s.id
			and g.location != ''
			and s.location != ''
	''')

    for p in cur.fetchall():
        cur.execute('''
			insert into similarities_among_locations
			values (%s, %s, %s)
		''', (p[0], p[1], 1 - sims[g_keys.index(p[0])][s_keys.index(p[1])]))

    con.commit()
    cur.close()
    con.close()
    print("=======End=======")


if __name__ == "__main__":
	generateLocationSimilarity()
