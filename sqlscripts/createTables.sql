create table if not exists gh_so_common_users
  (gh_user_id int, so_user_id int );

create table if not exists negative_user_pairs
  (gh_user_id int, so_user_id int );

create table if not exists similarities_among_dates
  (g_id int, s_id int, similarity float8, primary key(g_id, s_id));

create table if not exists similarities_among_desc_aboutme
  (g_id int, s_id int, similarity float8, primary key(g_id, s_id));

create table if not exists similarities_among_desc_comment
    (g_id int, s_id int, similarity float8, primary key(g_id, s_id));

create table if not exists similarities_among_locations
  (g_id int, s_id int, similarity float8, primary key(g_id, s_id));

create table if not exists similarities_among_user_names
  (g_id int, s_id int, similarity float8, primary key(g_id, s_id));

create table if not exists similarities_among_tags
  (g_id int, s_id int, similarity float8, primary key(g_id, s_id));

create table if not exists predictions
  (g_id int, s_id int, model character varying(5), pred int, proba float8, primary key(g_id, s_id, model));
