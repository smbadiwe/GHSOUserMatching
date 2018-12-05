# -*- coding: utf-8 -*-
from sklearn.externals import joblib
from scipy.sparse import lil_matrix
import threading
import math
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from appUtils import getDbConfig, computeDateSim, buildTrigram, vectorizeNamesByTrigram, tfidfSimilarities, loadGithubProjectDescription


def get_model_path(model):
    return "../models/{}.pkl".format(model)


def makePrediction(model, features, n_samples, delete_old_data, save_to_file=False):
    print("\n===========\nRUNNING makePrediction()\n===========\n")
    print("model: {}. n_samples: {}. save_to_file: {}".format(model, n_samples, save_to_file))
    ### model selection
    if not os.path.isdir("../models"):
        raise Exception("You need to run learning/learn.py first before running this file")

    con, cur = getDbConfig()

    if delete_old_data:
        cur.execute("delete from predictions where model = '{}'".format(model))
        con.commit()

    ### Candidate generation: test data
    print("Candidate generation: # test data = {}".format(n_samples))

    sims = {}
    for attr in features:
        sims[attr] = {}
        t = threading.Thread(target=similarity, args=(attr, con, sims))
        t.start()

    main_thread = threading.current_thread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        t.join()

    print("All thread returned")
    cur.execute('''
		select g_id, s_id
		from labeled_data_test
		order by g_id, s_id
	''')
    pairs = [(c[0], c[1]) for c in cur.fetchall()]

    print("Generate input data matrix")
    S = lil_matrix((n_samples * n_samples, len(features)))
    for attr in sims.keys():
        for c in sims[attr]:
            if not math.isnan(sims[attr][c]) and (c[0], c[1]) in pairs:
                S[pairs.index((c[0], c[1])), features.index(attr)] = sims[attr][c]
    S = S.toarray()

    print("Load and predict")

    clf = joblib.load(get_model_path(model))
    scores = clf.predict_proba(S)
    print("Done. scores - shape: {}. Classes: {}".format(scores.shape, clf.classes_))
    cc = 0

    for p in zip(pairs, scores):
        # pred = clf.classes_[0] if p[1][0] >= 0.5 else clf.classes_[1]
        pred = clf.classes_[1] if p[1][1] > 0.5 else clf.classes_[0]
        proba = p[1][0] if pred == clf.classes_[0] else p[1][1]
        query = "insert into predictions values ({},{},'{}',{},{})".format(p[0][0], p[0][1], model, pred, proba)
        cur.execute(query)
        cc += 1
        if cc % 10:
            con.commit()

    con.commit()

    if save_to_file:
        print("Saving predictions to file")
        cur.execute("select g_id, s_id, pred, proba from predictions where model = '{}'".format(model))
        with open("../data/predicted_{}.tsv".format(model), 'w') as w:
            w.write("g_id\ts_id\tpred\tproba\n")
            for row in cur.fetchall():
                w.write("\t".join([str(r) for r in row]) + "\n")

    cur.close()
    con.close()
    print("==========End makePrediction() for model: {}==========".format(model))


### Similarity computation hub based on attributes
def similarity(attr, con, sims):
    if attr == 'dates':
        dateSimilarity(con.cursor(), con, sims)
    elif attr == 'desc_aboutme':
        descAboutmeSimilarity(con.cursor(), sims)
    elif attr == 'desc_comment':
        descCommentSimilarity(con.cursor(), sims)
    elif attr == 'locations':
        locationSimilarity(con.cursor(), sims)
    # elif attr == 'desc_pbody':
    #     descPBodySimilarity(con.cursor(), sims)
    # elif attr == 'desc_ptitle':
    #     descPTitleSimilarity(con.cursor(), sims)
    # elif attr == 'desc_ptags':
    #     descPTagsSimilarity(con.cursor(), sims)
    elif attr == 'user_names':
        nameSimilarity(con.cursor(), sims)


### Similarity computation on dates
def dateSimilarity(cur, con, sims):
    cur.execute('''
		select distinct l.g_id, l.s_id, g.created_at::date, s.creation_date
		from users g, labeled_data_test l, so_users s
		where g.created_at is not null and g.id = l.g_id
			and s.creation_date is not null and s.id = l.s_id
	''')
    for p in cur.fetchall():
        sims['dates'][(p[0], p[1])] = computeDateSim(p[2], p[3])
    cur.close()


### Similarity computation on names 
def nameSimilarity(cur, sims):
    cur.execute('''
		select distinct g_name as username from labeled_data_test
		union
		select distinct s_name as username from labeled_data_test
	''')
    users = list(set([c[0] for c in cur.fetchall()]))

    name_trigrams, trigrams = buildTrigram(users)

    vectors = vectorizeNamesByTrigram(trigrams, name_trigrams)

    cur.execute('''
		select distinct l.g_id, l.s_id, l.g_name, l.s_name
		from labeled_data_test l
	''')
    for p in cur.fetchall():
        try:
            gv = np.array(vectors[p[2]]).reshape(1, -1)
            sv = np.array(vectors[p[3]]).reshape(1, -1)
        except:
            continue

        sims['user_names'][(p[0], p[1])] = cosine_similarity(gv, sv)
    cur.close()


### Similarity computation between locations
def locationSimilarity(cur, sims):
    cur.execute('''
		select l.g_id, u.location
		from labeled_data_test l, users u
		where l.g_id = u.id and u.location != ''
	''')
    g_users = {}
    for c in cur.fetchall():
        g_users[c[0]] = c[1]

    cur.execute('''
		select l.s_id, u.location
		from labeled_data_test l, so_users u
		where l.s_id = u.id and u.location != ''
	''')
    s_users = {}
    for c in cur.fetchall():
        s_users[c[0]] = c[1]

    if len(g_users) == 0 or len(s_users) == 0:
        return
    distances, g_key_indices, s_key_indices = tfidfSimilarities(g_users, s_users)

    cur.execute('''
		select distinct l.g_id, l.s_id
		from labeled_data_test l, users g, so_users s
		where l.g_id = g.id and l.s_id = s.id
			and g.location != '' and s.location != ''
	''')
    for p in cur.fetchall():
        g_ind = g_key_indices.get(p[0])
        s_ind = s_key_indices.get(p[1])

        if g_ind is not None and s_ind is not None:
            distance = distances[g_ind][s_ind]
        else:
            continue
        sims['locations'][(p[0], p[1])] = 1 - distance

    cur.close()


### Similarity computation between project descriptions and comments
def descCommentSimilarity(cur, sims):
    g_users = loadGithubProjectDescription(cur, "labeled_data_test") 

    ### Load user info of Stack Overflow
    cur.execute('''
		select distinct l.s_id, u.text
		from so_comments u, labeled_data_test l
		where u.text != '' and u.user_id = l.s_id
	''')
    s_users = {}
    for c in cur.fetchall():
        if c[0] in s_users:
            s_users[c[0]] += " " + c[1]
        else:
            s_users[c[0]] = c[1]

    if len(g_users) == 0 or len(s_users) == 0:
        return
    distances, g_key_indices, s_key_indices = tfidfSimilarities(g_users, s_users)

    cur.execute('''
		select distinct l.g_id, l.s_id
		from user_project_description g, labeled_data_test l, so_comments s
		where g.description != '' and g.user_id = l.g_id
			and s.text != '' and s.user_id = l.s_id
	''')
    for p in cur.fetchall():
        g_ind = g_key_indices.get(p[0])
        s_ind = s_key_indices.get(p[1])

        if g_ind is not None and s_ind is not None:
            distance = distances[g_ind][s_ind]
        else:
            continue
        sims['desc_comment'][(p[0], p[1])] = 1 - distance

    cur.close()


### Similarity computation between project descriptions and about me
def descAboutmeSimilarity(cur, sims):
    g_users = loadGithubProjectDescription(cur, "labeled_data_test") 
    ### Load user info of Stack Overflow
    cur.execute('''
		select distinct l.s_id, u.about_me
		from so_users u, labeled_data_test l
		where u.about_me != '' and u.id = l.s_id
	''')
    s_users = {}
    for c in cur.fetchall():
        s_users[c[0]] = c[1]

    if len(g_users) == 0 or len(s_users) == 0:
        return
    distances, g_key_indices, s_key_indices = tfidfSimilarities(g_users, s_users)

    cur.execute('''
		select distinct l.g_id, l.s_id
		from user_project_description g, labeled_data_test l, so_users s
		where g.description != '' and g.user_id = l.g_id
			and s.about_me != '' and s.id = l.s_id
	''')
    for p in cur.fetchall():
        g_ind = g_key_indices.get(p[0])
        s_ind = s_key_indices.get(p[1])

        if g_ind is not None and s_ind is not None:
            distance = distances[g_ind][s_ind]
        else:
            continue
        sims['desc_aboutme'][(p[0], p[1])] = 1 - distance

    cur.close()


### NOT USED - Similarity computation between project descriptions and post bodies
def descPBodySimilarity(cur, sims):
    g_keys, g_values = loadGithubProjectDescription(cur, "labeled_data_test") 

    ### Load user info of Stack Overflow
    cur.execute('''
		select distinct l.s_id, u.body
		from so_posts u, labeled_data_test l
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


### NOT USED - Similarity computation between project descriptions and post titles
def descPTitleSimilarity(cur, sims):
    g_keys, g_values = loadGithubProjectDescription(cur, "labeled_data_test") 

    ### Load user info of Stack Overflow
    cur.execute('''
		select distinct l.s_id, u.title
		from so_posts u, labeled_data_test l
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


### NOT USED - Similarity computation between project descriptions and post tags
def descPTagsSimilarity(cur, sims):
    g_keys, g_values = loadGithubProjectDescription(cur, "labeled_data_test") 

    ### Load user info of Stack Overflow
    cur.execute('''
		select distinct l.s_id, u.tags
		from so_posts u, labeled_data_test l
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
		from user_project_description g, labeled_data_test l, so_posts s
		where g.description != '' and g.user_id = l.g_id
			and s.tags != '' and s.owner_user_id = l.s_id
	''')
    for p in cur.fetchall():
        sims['desc_ptags'][(p[0], p[1])] = 1 - sims_tmp[g_keys.index(p[0])][s_keys.index(p[1])]
    cur.close()


def generatePredictionsCsvFile():
    print("\n===========\nRUNNING generatePredictionsCsvFile()\n===========\n")

    con, cur = getDbConfig()
    cur.execute('''
    SELECT p.g_id, p.s_id, l.label, p.model, p.pred, p.proba
    FROM predictions p LEFT JOIN labeled_data_test l
    ON p.g_id = l.g_id and p.s_id = l.s_id
    ''')

    with open('../data/predictions_all.csv', 'w') as w:
        w.write("g_id,s_id,true_label,model,predicted_label,probability\n")
        for row in cur.fetchall():
            w.write(",".join([str(r) for r in row]) + "\n")

    cur.close()
    con.close()
