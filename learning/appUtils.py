import psycopg2 as psql
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.feature_extraction.text import TfidfVectorizer


### loading descriptions
def loadGithubProjectDescription(cur, viewOrTable):
    cur.execute('''
		select distinct l.g_id, u.description
		from user_project_description u, {} l 
		where u.description != '' and u.user_id = l.g_id
	'''.format(viewOrTable))
    g_users = {}
    for c in cur.fetchall():
        if c[0] in g_users:
            g_users[c[0]] += " " + c[1]
        else:
            g_users[c[0]] = c[1]
    return g_users


def buildTrigram(list_of_texts):
    # trigrams for each text
    trigrams = []
    name_trigrams = {}
    for txt in list_of_texts:
        if txt is None:
            continue
        i_count = len(txt) - 2
        name_trigrams[txt] = [None] * i_count
        for i in range(0, i_count):
            tg = txt[i:i + 3]
            trigrams.append(tg)
            name_trigrams[txt][i] = tg
    trigrams = list(set(trigrams))
    return name_trigrams, trigrams


def vectorizeNamesByTrigram(trigrams, name_trigrams):
    # vectorizing names by trigram
    len_trigrams = len(trigrams)
    print("constructed trigram. len_trigrams = {}. len_name_trigrams = {}".format(len_trigrams, len(name_trigrams)))

    vectors = {}
    cnt = 0
    for name in list(name_trigrams.keys()):
        vec = [0] * len_trigrams
        for tri in name_trigrams[name]:
            vec[trigrams.index(tri)] = 1
        vectors[name] = vec
        if cnt % 5000 == 0 or (cnt > 70000 and cnt % 1000 == 0):
            print("Iteration: {}. Name: {}".format(cnt, name))
        cnt += 1
    return vectors


def getDbConnection(cfg):
    con = psql.connect(host=cfg["host"], user=cfg["user"], database=cfg["database"], password=cfg["password"])
    cur = con.cursor()

    return con, cur


### distance computation among vectors
def tfidfSimilarities(g_users, s_users):
    if not g_users or not s_users or len(g_users) == 0 or len(s_users) == 0:
        raise Exception("Both dictionaries must be non-null and with at least one item in each")

    values, g_key_indices, s_key_indices = genetate_params_for_tf_idf(g_users, s_users)

    tfidf = TfidfVectorizer(stop_words='english')

    vecs = tfidf.fit_transform(values)

    ### TF-IDF vectors of GH users
    g_vecs = vecs[:len(g_users), :]

    ### TF-IDF vectors of SO users
    s_vecs = vecs[len(g_users):, :]

    ### distances between vectors
    distances = pairwise_distances(g_vecs, s_vecs, metric='cosine')

    return distances, g_key_indices, s_key_indices


def genetate_params_for_tf_idf(g_users, s_users):
    """

    :param g_users: Dictionary
    :param s_users: Dictionary
    :return: values, g_key_indices, s_key_indices
    g_key_indices & s_key_indices are basically a mapping of g_users & s_users
    dictionary key to its position in the dictionary
    """
    len_g_users = len(g_users)
    len_s_users = len(s_users)
    values = [None] * (len_g_users + len_s_users)
    global_ind = 0

    g_key_indices = {}
    ind = 0
    for user_id, val in g_users.items():
        g_key_indices[user_id] = ind
        values[global_ind] = val
        ind += 1
        global_ind += 1

    s_key_indices = {}
    ind = 0
    for user_id, val in s_users.items():
        s_key_indices[user_id] = ind
        values[global_ind] = val
        ind += 1
        global_ind += 1

    return values, g_key_indices, s_key_indices


def computeDateSim(date1, date2):
    if date1 > date2:
        num = date1 - date2
    else:
        num = date2 - date1
    if num.days == 0:
        return 1
    return 1.0 / num.days


class DbConnection(object):
    """
     Abstraction for database connections
    """
    __con = None
    __cur = None

    def DbConnection(self):
        return self

    def create(self):
        print("Creating DbConnection")
        con, cur = getDbConnection(cfg)

        # self.__con = psql.connect(database=cfg['database'], user=cfg['user'], host=cfg['host'], port=cfg['port'], password=cfg['password'])
        connStr = "dbname={} user={} password={} host={} port={}"\
            .format(cfg['database'], cfg['user'], cfg['password'], cfg['host'], cfg['port'])
        self.__con = psql.connect(connStr)
        self.__cur = self.__con.cursor()
        print("Created DbConnection. {}".format(connStr))

    def executeScript(self, sqlScript, queryParams=None):
        print("Executing script")
        if queryParams is None:
            self.__cur.execute(sqlScript)
        else:
            self.__cur.execute(sqlScript, queryParams)
        print("Done executing script")

    def fetchData(self, sqlSelectScript, queryParams=None):
        print("Executing SELECT script")
        self.executeScript(sqlSelectScript, queryParams)
        return self.__cur.fetchall()

    def commit(self):
        print("Committing DbConnection")
        self.__con.commit()

    def close(self):
        print("Closing DbConnection")
        self.__con.commit()
        self.__cur.close()
        self.__con.close()
        print("Closed DbConnection")
