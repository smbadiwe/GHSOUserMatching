# -*- coding: utf-8 -*-

import psycopg2 as psql
from appUtils import getDbConfig, tfidfSimilarities, loadGithubProjectDescription


def generateDescCommentSimilarity(redoSimilarity=False):
    print("\n===========\nRUNNING generateDescCommentSimilarity()\n===========\n")
    con, cur = getDbConfig()
    
    # check if done before
    if redoSimilarity:
        cur.execute('delete from similarities_among_desc_comment')
        con.commit()
    else:
        cur.execute('select g_id from similarities_among_desc_comment limit 1')
        existing = [r[0] for r in cur.fetchall()]
        if len(existing) > 0:
            print("similarities_among_desc_comment has already been generated")
            return

    print("created table similarities_among_desc_comment")

    ### Load user info of GitHub
    g_users = loadGithubProjectDescription(cur, "labeled_data")

    ### Load user info of Stack Overflow
    cur.execute('''
		select distinct l.s_id, u.text
		from so_comments u, labeled_data l
		where u.text != '' and u.user_id = l.s_id
	''')
    s_users = {}
    for c in cur.fetchall():
        if c[0] in s_users:
            s_users[c[0]] += " " + c[1]
        else:
            s_users[c[0]] = c[1]

    ### TF-IDF computation
    distances, g_key_indices, s_key_indices = tfidfSimilarities(g_users, s_users)

    print("shape - distances: {}.\n".format(distances.shape))

    ### store similarities
    cur.execute('''
		select distinct l.g_id, l.s_id
		from user_project_description g, labeled_data l, so_comments s
		where g.description != '' and g.user_id = l.g_id
			and s.text != '' and s.user_id = l.s_id
	''')
    good = 0
    bad = 0
    for p in cur.fetchall():
        g_ind = g_key_indices.get(p[0])
        s_ind = s_key_indices.get(p[1])

        if g_ind is not None and s_ind is not None:
            distance = distances[g_ind][s_ind]
            print("\t1-similarity_val: {}".format(1 - distance))
            good += 1
        else:
            print("p[0]: {}, p[1]: {}".format(p[0], p[1]))
            print("\tg_ind: {}, s_ind: {}".format(g_ind, s_ind))
            bad += 1
            continue

        cur.execute('''
			insert into similarities_among_desc_comment
			values (%s, %s, %s)
		''', (p[0], p[1], 1 - distance))

    print("Close connection")
    con.commit()
    cur.close()
    con.close()
    print("\nAll done. #good ones: {}, #bad ones: {}".format(good, bad))
    print("=======End generateDescCommentSimilarity()=======")
