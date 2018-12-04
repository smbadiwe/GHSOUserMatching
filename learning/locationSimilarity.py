# -*- coding: utf-8 -*-

import psycopg2 as psql
from appUtils import getDbConfig, tfidfSimilarities


def generateLocationSimilarity(redoSimilarity=False):
    print("\n===========\nRUNNING generateLocationSimilarity()\n===========\n")
    con, cur = getDbConfig()
    
    # check if done before
    if redoSimilarity:
        cur.execute('delete from similarities_among_locations')
        con.commit()
    else:
        cur.execute('select g_id from similarities_among_locations limit 1')
        existing = [r[0] for r in cur.fetchall()]
        if len(existing) > 0:
            print("similarities_among_locations has already been generated")
            return

    ### Load user info of GitHub
    cur.execute('''
		select distinct l.g_id, u.location
		from labeled_data l, users u
		where l.g_id = u.id and u.location != ''
	''')
    g_users = {}
    for c in cur.fetchall():
        g_users[c[0]] = c[1]

    ### Load user info of Stack Overflow
    cur.execute('''
		select distinct l.s_id, u.location
		from labeled_data l, so_users u
		where l.s_id = u.id and u.location != ''
	''')
    s_users = {}
    for c in cur.fetchall():
        s_users[c[0]] = c[1]

    ### TF-IDF computation
    distances, g_key_indices, s_key_indices = tfidfSimilarities(g_users, s_users)

    print("shape - distances: {}.\n".format(distances.shape))

    ### store similarities
    cur.execute('''
		select distinct g_id, s_id
		from labeled_data l, users g, so_users s
		where l.g_id = g.id and l.s_id = s.id
			and g.location != '' and s.location != ''
	''')
    good = 0
    bad = 0
    for p in cur.fetchall():
        # print("p[0]: {}, p[1]: {}".format(p[0], p[1]))
        g_ind = g_key_indices.get(p[0])
        s_ind = s_key_indices.get(p[1])

        if g_ind is not None and s_ind is not None:
            distance = distances[g_ind][s_ind]
            # print("\t1-similarity_val: {}".format(1 - distance))
            good += 1
        else:
            # print("\tg_ind: {}, s_ind: {}".format(g_ind, s_ind))
            bad += 1
            continue

        cur.execute('''
			insert into similarities_among_locations
			values (%s, %s, %s)
		''', (p[0], p[1], 1 - distance))

    print("Close connection")
    con.commit()
    cur.close()
    con.close()
    print("\nAll done. #good ones: {}, #bad ones: {}".format(good, bad))
    print("=======End=======")
