# -*- coding: utf-8 -*-
from sklearn.externals import joblib
from scipy.sparse import lil_matrix
import threading
import psycopg2 as psql
import math

import numpy as np
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine

def main():
	### model selection
	model = "../models/gbdt.pkl"
	#model = "../models/knn.pkl"
	#model = "../models/lg.pkl"
	#model = "../models/lr.pkl"
	#model = "../models/rf.pkl"

	con = psql.connect('dbname=gh_so')
	cur = con.cursor()

	### Candidate generation
	counter = 100
	cur.execute('''
		create temp table pairs as
		select a.id as g_id, b.id as s_id
		from (
			select *
			from (
				select distinct id
				from users 
				except
				select distinct g_id
				from processed
				except 
				select distinct g_id 
				from predicted
			) a
			order by random()
			limit %d
		) a, (
			select *
			from (
				select distinct id
				from so_users 
				except
				select distinct s_id
				from processed
				except 
				select distinct s_id 
				from predicted
			) a
			order by random()
			limit %d
		) b
	''' % (counter, counter))

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
	sims = {}
	for attr in attrs:
		sims[attr] = {}
		t = threading.Thread(target=similarity, args=(attr, con, sims))
		t.start()

	main_thread = threading.current_thread()
	for t in threading.enumerate():
		if t is main_thread:
			continue
		t.join()

	cur.execute('''
		select g_id, s_id
		from pairs
		order by g_id, s_id
	''')
	pairs = [(c[0], c[1]) for c in cur.fetchall()]

	S = lil_matrix((counter*counter, len(attrs)))
	for attr in sims.keys():
		for c in sims[attr]:
			if not math.isnan(sims[attr][c]):
				S[pairs.index((c[0], c[1])), attrs.index(attr)] = sims[attr][c]
	S = S.toarray()

	clf = joblib.load(model)
	scores = clf.predict_proba(S)
	cc = 0
	for p in zip(pairs, scores):
		query = "insert into predicted values (" + str(p[0][0]) + "," + str(p[0][1]) + ", 1, " + str(p[1][1]) + ")"
		cur.execute(query)

		cc += 1
		if cc % 10:
			con.commit()

	con.commit()
	cur.close()
	con.close()


### Similarity computation hub based on attributes
def similarity(attr, con, sims):
	if attr == 'dates':
		dateSimilarity(con.cursor(), con, sims)
	elif attr == 'desc_aboutme':
		descAboutmeSimilarity(con.cursor(), con, sims)
	elif attr == 'desc_comment':
		descCommentSimilarity(con.cursor(), con, sims)
	elif attr == 'desc_pbody':
		descPBodySimilarity(con.cursor(), con, sims)
	elif attr == 'desc_ptitle':
		descPTitleSimilarity(con.cursor(), con, sims)
	elif attr == 'desc_ptags':
		descPTagsSimilarity(con.cursor(), con, sims)
	elif attr == 'locations':
		locationSimilarity(con.cursor(), con, sims)
	elif attr == 'user_names':
		nameSimilarity(con.cursor(), con, sims)


### Similarity computation on dates
def dateSimilarity(cur, con, sims):
	cur.execute('''
		select distinct l.g_id, l.s_id, g.created_at::date, s.creation_date
		from users g, pairs l, so_users s
		where g.created_at is not null and g.id = l.g_id
			and s.creation_date is not null and s.id = l.s_id
	''')
	for p in cur.fetchall():
		g_date, s_date  = p[2], p[3]
		if g_date > s_date:
			num = g_date - s_date
		else:
			num = s_date - g_date
		if num.days == 0:
			sim = 1
		else:
			sim = 1.0/num.days
		sims['dates'][(p[0], p[1])] = sim
	cur.close()


### Similarity computation on names 
def nameSimilarity(cur, con, sims):
	cur.execute('''
		select distinct g.name
		from pairs l, users g
		where l.g_id = g.id and g.name != ''
		union
		select distinct s.display_name
		from pairs l, so_users s
		where l.s_id = s.id and s.display_name != ''
	''')
	users = list(set([c[0] for c in cur.fetchall()]))
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
	vectors = {}
	for name in name_trigrams.keys():
		vec = np.zeros(len(trigrams))
		for tri in name_trigrams[name]:
			vec[trigrams.index(tri)] = 1
		vectors[name] = vec
	cur.execute('''
		select distinct l.g_id, l.s_id, g.name, s.display_name
		from pairs l, users g, so_users s
		where l.g_id = g.id and l.s_id = s.id
			and g.name != '' and s.display_name != ''
	''')
	pairs = cur.fetchall()
	for p in pairs:
		gv = vectors[p[2]]
		sv = vectors[p[3]]
		sim = 1- cosine(gv, sv)
		sims['user_names'][(p[0], p[1])] = sim
	cur.close()


### Similarity computation between locations
def locationSimilarity(cur, con, sims):
	cur.execute('''
		select l.g_id, u.location
		from pairs l, users u
		where l.g_id = u.id
			and u.location != ''
	''')
	g_users = cur.fetchall()
	g_keys = [c[0] for c in g_users]
	g_values = [c[1] for c in g_users]

	cur.execute('''
		select l.s_id, u.location
		from pairs l, so_users u
		where l.s_id = u.id
			and u.location != ''
	''')
	s_users = cur.fetchall()
	s_keys = [c[0] for c in s_users]
	s_values = [c[1] for c in s_users]

	if len(g_values) == 0 or len(s_values) == 0:
		return
	sims_tmp = tfidfSimilarities(g_values, s_values)

	cur.execute('''
		select distinct l.g_id, l.s_id
		from pairs l, users g, so_users s
		where l.g_id = g.id and l.s_id = s.id
			and g.location != '' and s.location != ''
	''')
	pairs = cur.fetchall()
	for p in pairs:
		sims["locations"][(p[0], p[1])] = 1 - sims_tmp[g_keys.index(p[0])][s_keys.index(p[1])]
	cur.close()


### Similarity computation between project descriptions and post bodies
def descPBodySimilarity(cur, con, sims):
	g_keys, g_values = loadDescription(cur)

	### Load user info of Stack Overflow
	cur.execute('''
		select distinct l.s_id, u.body
		from so_posts u, pairs l
		where u.body != '' and u.owner_user_id = l.s_id
	''')
	s_users = {}
	for c in cur.fetchall():
		if c[0] in s_users:
			s_users[c[0]] += " " + c[1]
		else:
			s_users[c[0]] = c[1]
	s_keys = s_users.keys()

	if len(g_values) == 0 or len(s_keys) == 0:
		return
	sims_tmp = tfidfSimilarities(g_values, s_users.values())

	cur.execute('''
		select distinct l.g_id, l.s_id
		from user_project_description g, pairs l, so_posts s
		where g.description != '' and g.user_id = l.g_id
			and s.body != '' and s.owner_user_id = l.s_id
	''')
	pairs = cur.fetchall()
	for p in pairs:
		sims['desc_pbody'][(p[0], p[1])] = 1 - sims_tmp[g_keys.index(p[0])][s_keys.index(p[1])]
	cur.close()



### Similarity computation between project descriptions and post titles
def descPTitleSimilarity(cur, con, sims):
	g_keys, g_values = loadDescription(cur)

	### Load user info of Stack Overflow
	cur.execute('''
		select distinct l.s_id, u.title
		from so_posts u, pairs l
		where u.title != '' and u.owner_user_id = l.s_id
	''')
	s_users = {}
	for c in cur.fetchall():
		if c[0] in s_users:
			s_users[c[0]] += " " + c[1]
		else:
			s_users[c[0]] = c[1]
	s_keys = s_users.keys()

	if len(g_values) == 0 or len(s_keys) == 0:
		return
	sims_tmp = tfidfSimilarities(g_values, s_users.values())

	cur.execute('''
		select distinct l.g_id, l.s_id
		from user_project_description g, pairs l, so_posts s
		where g.description != '' and g.user_id = l.g_id
			and s.title != '' and s.owner_user_id = l.s_id
	''')
	pairs = cur.fetchall()
	for p in pairs:
		sims['desc_ptitle'][(p[0], p[1])] = 1 - sims_tmp[g_keys.index(p[0])][s_keys.index(p[1])]
	cur.close()



### Similarity computation between project descriptions and post tags
def descPTagsSimilarity(cur, con, sims):
	g_keys, g_values = loadDescription(cur)

	### Load user info of Stack Overflow
	cur.execute('''
		select distinct l.s_id, u.tags
		from so_posts u, pairs l
		where u.tags != '' and u.owner_user_id = l.s_id
	''')
	s_users = {}
	for c in cur.fetchall():
		if c[0] in s_users:
			s_users[c[0]] += " " + c[1]
		else:
			s_users[c[0]] = c[1]
	s_keys = s_users.keys()

	if len(g_values) == 0 or len(s_keys) == 0:
		return
	sims_tmp = tfidfSimilarities(g_values, s_users.values())

	cur.execute('''
		select distinct l.g_id, l.s_id
		from user_project_description g, pairs l, so_posts s
		where g.description != '' and g.user_id = l.g_id
			and s.tags != '' and s.owner_user_id = l.s_id
	''')
	pairs = cur.fetchall()
	for p in pairs:
		sims['desc_ptags'][(p[0], p[1])] = 1 - sims_tmp[g_keys.index(p[0])][s_keys.index(p[1])]
	cur.close()



### Similarity computation between project descriptions and comments
def descCommentSimilarity(cur, con, sims):
	g_keys, g_values = loadDescription(cur)

	### Load user info of Stack Overflow
	cur.execute('''
		select distinct l.s_id, u.text
		from so_comments u, pairs l
		where u.text != '' and u.user_id = l.s_id
	''')
	s_users = {}
	for c in cur.fetchall():
		if c[0] in s_users:
			s_users[c[0]] += " " + c[1]
		else:
			s_users[c[0]] = c[1]
	s_keys = s_users.keys()

	if len(g_values) == 0 or len(s_keys) == 0:
		return
	sims_tmp = tfidfSimilarities(g_values, s_users.values())

	cur.execute('''
		select distinct l.g_id, l.s_id
		from user_project_description g, pairs l, so_comments s
		where g.description != '' and g.user_id = l.g_id
			and s.text != '' and s.user_id = l.s_id
	''')
	pairs = cur.fetchall()
	for p in pairs:
		sims['desc_comment'][(p[0], p[1])] = 1 - sims_tmp[g_keys.index(p[0])][s_keys.index(p[1])]
	cur.close()



### Similarity computation between project descriptions and about me 
def descAboutmeSimilarity(cur, con, sims):
	g_keys, g_values = loadDescription(cur)

	### Load user info of Stack Overflow
	cur.execute('''
		select distinct l.s_id, u.about_me
		from so_users u, pairs l
		where u.about_me != '' and u.id = l.s_id
	''')
	s_users = {}
	for c in cur.fetchall():
		s_users[c[0]] = c[1]
	s_keys = s_users.keys()

	if len(g_values) == 0 or len(s_keys) == 0:
		return
	sims_tmp = tfidfSimilarities(g_values, s_users.values())

	cur.execute('''
		select distinct l.g_id, l.s_id
		from user_project_description g, pairs l, so_users s
		where g.description != '' and g.user_id = l.g_id
			and s.about_me != '' and s.id = l.s_id
	''')
	pairs = cur.fetchall()
	for p in pairs:
		sims['desc_aboutme'][(p[0], p[1])] = 1 - sims_tmp[g_keys.index(p[0])][s_keys.index(p[1])]
	cur.close()


### distance computation among vectors
def tfidfSimilarities(g_values, s_values):
	tfidf = TfidfVectorizer(stop_words='english')
	values = []
	values.extend(g_values)
	values.extend(s_values)
	vecs = tfidf.fit_transform(values)
	g_vecs = vecs[:len(g_values),:]
	s_vecs = vecs[len(g_values):,:]
	return pairwise_distances(g_vecs, s_vecs, metric='cosine')


### loading descriptions
def loadDescription(cur):
	cur.execute('''
		select distinct l.g_id, u.description
		from user_project_description u, pairs l 
		where u.description != '' and u.user_id = l.g_id
	''')
	g_users = {}
	for c in cur.fetchall():
		if c[0] in g_users:
			g_users[c[0]] += " " + c[1]
		else:
			g_users[c[0]] = c[1]	
	return g_users.keys(), g_users.values()


if __name__ == "__main__":
    main()
