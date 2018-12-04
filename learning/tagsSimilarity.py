# -*- coding: utf-8 -*-

import psycopg2 as psql
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from nameSimilarity import buildTrigram, vectorizeNamesByTrigram
from appUtils import getDbConfig


def generateTagsSimilarity(redoSimilarity=False):
    print("\n===========\nRUNNING generateTagsSimilarity()\n===========\n")
    cfg = getDbConfig()
    con = psql.connect(host=cfg["host"], user=cfg["user"], database=cfg["database"], password=cfg["password"])
    cur = con.cursor()

    # check if done before
    if redoSimilarity:
        cur.execute('delete from similarities_among_tags')
        con.commit()
    else:
        cur.execute('select g_id from similarities_among_tags limit 1')
        existing = [r[0] for r in cur.fetchall()]
        if len(existing) > 0:
            print("similarities_among_tags has already been generated")
            return

    print("created table similarities_among_tags")

    gh_user_tags = {}
    # GH user tags based on projects they own
    cur.execute('''
    select l.g_id, lower(p.language) as tag
    from labeled_data l, projects p
    where p.owner_id = l.g_id and p.language is not null
    ''')
    for p in cur.fetchall():
        if gh_user_tags.get(p[0]) is None:
            gh_user_tags[p[0]] = set([p[1]])
        else:
            gh_user_tags[p[0]].add(p[1])
    print("gotten tags for gh users based on projects they own")

    # GH user tags based on projects they don't own but are part of
    cur.execute('''
    select r.user_id as g_id, lower(pr.language) as tag from 
    (
        select p.user_id, p.repo_id
        from  project_members p, labeled_data l
        where p.user_id = l.g_id
    ) r, projects pr
    where pr.id = r.repo_id and pr.language is not null
    ''')
    for p in cur.fetchall():
        if gh_user_tags.get(p[0]) is None:
            gh_user_tags[p[0]] = set([p[1]])
        else:
            gh_user_tags[p[0]].add(p[1])
    print("gotten tags for gh users based on projects they DON'T own")

    print("Tags gotten for {} GH users".format(len(gh_user_tags)))

    cur.execute('select distinct lower(language) from projects where language is not null')
    tags = set([r[0] for r in cur.fetchall()])
    print("{} tags to be considered for our work are now loaded".format(len(tags)))

    # SO user tags

    so_user_tags = {}
    # cur.execute('''
    # select p.post_type_id, p.owner_user_id, p.last_editor_user_id, lower(p.tags)
    # from labeled_data l, so_posts p
    # where (l.s_id = p.owner_user_id or l.s_id = p.last_editor_user_id) and p.tags is not null
    # ''')
    # The above query takes forever to run. This one below is quite faster
    cur.execute('''
    select p.post_type_id, p.owner_user_id, p.last_editor_user_id, lower(p.tags) from so_posts p
    where (p.owner_user_id in (select s_id from labeled_data)
    or p.last_editor_user_id in (select s_id from labeled_data))
    and p.tags is not null
    ''')
    for p in cur.fetchall():
        if p[1] is None:
            continue
        so_tags = p[3].replace("><", ",").replace("<", "").replace(">", "").split(",")

        # from the tag lists, we only pick those that are in our 'tags' list
        used_tags = []
        for so_tag in so_tags:
            if so_tag in tags:
                used_tags.append(so_tag)
        if len(used_tags) == 0:
            continue

        # FOR p.owner_user_id
        if so_user_tags.get(p[1]) is None:
            so_user_tags[p[1]] = set(used_tags)
        else:
            for tg in used_tags:
                so_user_tags[p[1]].add(tg)
        # FOR p.last_editor_user_id
        if p[2] is not None and p[1] != p[2]:
            if so_user_tags.get(p[2]) is None:
                so_user_tags[p[2]] = set(used_tags)
            else:
                for tg in used_tags:
                    so_user_tags[p[2]].add(tg)

    # set each user tag list as a string with the tags sorted
    # print()
    for key in gh_user_tags:
        gh_user_tags[key] = ",".join(map(str, sorted(gh_user_tags[key])))
    #     print("gh_user_tags: key: {}. val: {}".format(key, gh_user_tags[key]))
    # print()
    for key in so_user_tags:
        so_user_tags[key] = ",".join(map(str, sorted(so_user_tags[key])))
        # print("so_user_tags: key: {}. val: {}".format(key, so_user_tags[key]))

    users_tags = []
    users_tags.extend(gh_user_tags.values())
    users_tags.extend(so_user_tags.values())
    print("Combined tags list. Total: {} (with duplicates)".format(len(users_tags)))

    name_trigrams, trigrams = buildTrigram(set(users_tags))
    # print("\ntrigrams")
    # print(trigrams)
    # print("\nname_trigrams")
    # print(name_trigrams)
    # print("\ngh_user_tags")
    # print(gh_user_tags)
    # print("\nso_user_tags")
    # print(so_user_tags)

    vectors = vectorizeNamesByTrigram(trigrams, name_trigrams)
    # print("\nvectors")
    # print(vectors)

    print("\nConstructed vectors for vectorizing tag-list by trigram. length of vectors dict: {}".format(len(vectors)))
    # similarities between names
    cur.execute('select distinct g_id, s_id from labeled_data')
    n_errors = 0
    len_trigrams = len(trigrams)
    pairs = cur.fetchall()
    for p in pairs:
        try:
            # print("p[0] = {}, p[1] = {}".format(p[0], p[1]))
            gv_key = gh_user_tags.get(p[0])
            if gv_key is not None:
                # print("\tgv_key = {}.".format(gv_key))
                gv = np.array(vectors[gv_key]).reshape(1, -1)
            else:
                gv = np.array([0] * len_trigrams).reshape(1, -1)
            sv_key = so_user_tags.get(p[1])
            if sv_key is not None:
                # print("\tsv_key = {}".format(sv_key))
                sv = np.array(vectors[sv_key]).reshape(1, -1)
            else:
                sv = np.array([0] * len_trigrams).reshape(1, -1)
            # if gv_key is not None and sv_key is not None:
            #     print("p[0] = {}, p[1] = {}".format(p[0], p[1]))
            #     print("\tgv_key = {}. sv_key = {}".format(gv_key, sv_key))
        except Exception as ex:
            n_errors += 1
            print("\tError: {}".format(ex))
            continue

        sim = cosine_similarity(gv, sv)
        cur.execute('''
			insert into similarities_among_tags
			values (%s, %s, %s)
		''', (p[0], p[1], sim[0][0]))

    print("similarities_among_tags processed. {} names not found in vectors dictionary".format(n_errors))

    print("Close connection")
    con.commit()
    cur.close()
    con.close()
    print("=======End=======")
