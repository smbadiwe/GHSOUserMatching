# -*- coding: utf-8 -*-
import psycopg2 as psql
from appUtils import getDbConnection, tfidfSimilarities, loadGithubProjectDescription


def generateDescAboutMeSimilarity(cfg, redoSimilarity = False):
	print("\n===========\nRUNNING generateDescAboutMeSimilarity()\n===========\n")
	con, cur = getDbConnection(cfg)
	# check if done before
	if redoSimilarity:
		cur.execute('delete from similarities_among_desc_aboutme')
		con.commit()
	else:
		cur.execute('select g_id from similarities_among_desc_aboutme limit 1')
		existing = [r[0] for r in cur.fetchall()]
		if len(existing) > 0:
			print("similarities_among_desc_aboutme has already been generated")
			return

	print("created table similarities_among_desc_aboutme")

	### Load user info of GitHub
	g_users = loadGithubProjectDescription(cur, "labeled_data")

	### Load user info of Stack Overflow
	cur.execute('''
		select distinct l.s_id, u.about_me
		from so_users u, labeled_data l
		where u.about_me != '' and u.id = l.s_id
	''')
	s_users = {}
	for c in cur.fetchall():
		s_users[c[0]] = c[1]

	### TF-IDF computation
	distances, g_key_indices, s_key_indices = tfidfSimilarities(g_users, s_users)
	print("shape - distances: {}.\n".format(distances.shape))

	### store similarities
	cur.execute('''
		select distinct l.g_id, l.s_id
		from user_project_description g, labeled_data l, so_users s
		where g.description != '' and g.user_id = l.g_id
			and s.about_me != '' and s.id = l.s_id
	''')
	pairs = cur.fetchall()
	good = 0
	bad = 0
	for p in pairs:
		# print("p[0]: {}, p[1]: {}".format(p[0], p[1]))
		g_ind = g_key_indices.get(p[0])
		s_ind = s_key_indices.get(p[1])

		if g_ind is not None and s_ind is not None:
			distance = distances[g_ind][s_ind]
			# print("\t1-similarity_val: {}".format(1-distance))
			good += 1
		else:
			# print("\tg_ind: {}, s_ind: {}".format(g_ind, s_ind))
			bad += 1
			continue

		cur.execute('''
			insert into similarities_among_desc_aboutme
			values (%s, %s, %s)
		''', (p[0], p[1], 1-distance))

	con.commit()
	cur.close()
	con.close()
	print("\nAll done. #good ones: {}, #bad ones: {}".format(good, bad))
	print("=======End=======")

