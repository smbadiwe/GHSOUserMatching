# -*- coding: utf-8 -*-

import psycopg2 as psql
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
# import gc
from appUtils import getDbConfig, buildTrigram, vectorizeNamesByTrigram


def generateNameSimilarity(redoSimilarity=False):
    print("\n===========\nRUNNING generateNameSimilarity()\n===========\n")
    con, cur = getDbConfig()
    
    # check if done before
    if redoSimilarity:
        cur.execute('delete from similarities_among_user_names')
        con.commit()
    else:
        cur.execute('select g_id from similarities_among_user_names limit 1')
        existing = [r[0] for r in cur.fetchall()]
        if len(existing) > 0:
            print("similarities_among_user_names has already been generated")
            return

    print("created table similarities_among_user_names")
    cur.execute('''
		drop table if exists similarities_among_names;
		create temp table similarities_among_names
			(g_name text, s_name text, similarity float8);
	''')
    print("created table similarities_among_names")
    # names of GH users
    cur.execute('''
		select distinct g_name as username from labeled_data
		union
		select distinct s_name as username from labeled_data
	''')
    gh_and_so_users = [r[0] for r in cur.fetchall()]

    print("Combined users list. Total: {}".format(len(gh_and_so_users)))

    name_trigrams, trigrams = buildTrigram(gh_and_so_users)

    vectors = vectorizeNamesByTrigram(trigrams, name_trigrams)

    print("Constructed vectors for vectorizing names by trigram. length of vectors dict: {}".format(len(vectors)))
    # similarities between names
    cur.execute('''
		select distinct g_name, s_name
		from labeled_data where g_name != '' and s_name != ''
	''')
    n_errors = 0
    pairs = cur.fetchall()
    for p in pairs:
        try:
            gv = np.array(vectors[p[0]]).reshape(1, -1)
            sv = np.array(vectors[p[1]]).reshape(1, -1)
        except:
            n_errors += 1
            continue
        sim = cosine_similarity(gv, sv)
        cur.execute('''
			insert into similarities_among_names
			values (%s, %s, %s)
		''', (p[0], p[1], sim[0][0]))
        con.commit()

    print("similarities_among_names processed. {} names not found in vectors dictionary".format(n_errors))
    ### store similarities between GH and SO users
    cur.execute('''
		insert into similarities_among_user_names
		select g.id, s.id, c.similarity
		from users g, so_users s, similarities_among_names c
		where g.name = c.g_name and s.display_name = c.s_name
	''')

    print("Delete temp table: similarities_among_names")
    cur.execute('drop table if exists similarities_among_names')
    con.commit()

    print("similarities_among_user_names processed")
    print("Close connection")
    cur.close()
    con.close()
    print("=======End=======")
