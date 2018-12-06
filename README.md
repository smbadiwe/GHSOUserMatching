# Predicting Whether a GitHub and Stack Overflow Account Belong to the same person

## Summary
The sections below are only for those who need more detail. If you, like me, are in a hurry, simply do the following: 
* Setup your data in a postgresql database (See [the section on Data](#Data)). 
* Make a copy of `config.example.yml` and rename the copy to `config.yml`
* Edit `config.yml`, specifying the correct values for you database and the other settings.
* Run `learning\start.py`. In fact, you can simply study the code there and get the top-level implementation detail.

## Data 

### Loading Github data
- source: ~~http://ghtorrent.org/downloads/msr14-mysql.gz~~ (no more available)
- Instead, you can get from GHTorrent (http://ghtorrent.org/downloads.html)

### Loading StackOverflow data
To load the StackOverflow (in postgresql) data into the common postgre db (`gh_so`):
- Download the Postgresq dump from http://2013.msrconf.org/challenge_data/201208_stack_overflow_postgres_dump.tar.bz
- Unzip the `.tar.bz` file (I use Winrar)
- Unzip the `.tar` file you get from unzipping in the step above
- Install PostgreSql. Add it to `PATH` (in Environment Variable)
- Create a database called `gh_so`
- Create a role called "ponza". The role should AT LEAST have the privilege to create databases. You can ignore this instruction if you like seeing error messages
- Open command prompt (CMD or terminal; but NOT Powershell). 
- Run the following script
```bash
psql -U postgres gh_so < "path-to-the-file-you-unzipped"
```
NB: It will ask you for password. Enter the password you created when installing the database.

To rename the relevant SO tables to the required format, run the following script:
```sql
ALTER TABLE comments
RENAME TO so_comments;
ALTER TABLE posts
RENAME TO so_posts;
ALTER TABLE users
RENAME TO so_users;
ALTER TABLE votes
RENAME TO so_votes;
```

### Merging Github and Stack Overflow Data
To dump GH data from MySql in a postgre-compatible format, run the script in CMD or terminal:
```bash
mysqldump --compatible=ansi --default-character-set=utf8 -r gh_db.mysql -u root -p gh_db
```

NB: The dump will be in the directory from where you're running the command. It'll be named `gh_db.mysql`

To migrate data from mysql to postgresql:
	https://github.com/AnatolyUss/nmig works like charm. Node.js required.

- User pairs from SO and GH, who have same email (through MD5 hashing)
  - data/common_users.csv

## Learning

### Assumption
- Both dumps of SO and GH are in the same database (namely, `gh_so`).
- Common users are stored in the database (`gh_so`).
	- Table: `gh_so_common_users (so_user_id, gh_user_id)`

### Preparation
- Down sampling of negative data
	- Making pairs of GH (resp. SO) users in gh_so_common_users with SO (resp. GH) users not in gh_so_users 
		- Find same numbers of pairs in gh_so_common_users for GH and SO, respectively.
	- Tool:
		- learning/negativeDataGen.py
- Project descriptions as GH users' feature
	- Project decriptions are considered to reflect interests of GH users 
	- Tool:
		- learning/user_project_dec_mapping.sql
- Labeled data
	- Label positive pairs and negative pairs with 1 and 0 respectively.
	- Tool or data:
		- learning/createView.sql
		- data/labeled_data.csv

### Similarity computations
- Similarity on date attributes
	- Inverse of date duration
	- GH: created_at (timestamp)
	- SO: creation_date (date)
	- Tool:
		- learning/dateSimilarity.py
- Similarity on name attribute
	- Trigram-based similarity
	- GH: name (text)
	- SO: display_name (text)
	- Tool:
		- learning/nameSimilarity.py
- Similarity on location attributes
	- TFIDF-based similarity 
	- GH: location (text)
	- SO: location (text)
	- Tool:
		- learning/locationSimilarity.py
- Similarity on descriptive attributes
	- TFIDF-based similarity
	- GH: project description (text)
	- SO:
		- aboutme (text)
		- comments (text)
		- post body (text)
		- post title (text)
		- post tags (text)
	- Tool:
		- learning/descVsAboutme.py
		- learning/descVsComment.py
		- learning/descVsPosts.py

### Learning classifiers
- Similarity matrix construction
	- For each pair of GH user and SO user, above similarities are associated as features. 
	- To learn classification models, features of all learning pairs are made as matrix.
	- Tool:
		- learning/similarityMatrixGen.py
		- data/s.mtx
- Learning classifiers
	- Methods: linear regression (lr), k-nearest neighbor klnn), logistic regrassion (lg),
		random forest (rf), and gradient boosting decision tree (gndt)
	- Tool:
		- learning/classifierLearning.py
		- models.zip
			- models/*.pkl
				- Learned models


## Prediction

### Requirement
- Learned model in models/xxx.pkl
	- In this project, the models directory is zipped due to the file size limitation,
		so users have to unzip it first.
- Prediction module
	- The module using a selected model predicts identities of randomly selected pairs of users. 
		- This process is time-comsuming if the number of pairs is large, so, by default,
			only 50000 pairs are computed. 
	- Tool:
		- predict/predict.py
		- predict/writePredicted.py
			- data/predicted.tsv
				- the predicted user pairs with probability


## Acknowledgement
This work is inspired by the ideas in [this paper by Takahiro Komamizu](http://dx.doi.org/10.18293/SEKE2017-109) [1]. We used [their code](https://github.com/Taka-Coma/PJD_GHSO) as starting point, but our final codebase is substantially different - and better (sshhh... don't say it loud!)

## Reference
[1] Takahiro Komamizu, Yasuhiro Hayase, Toshiyuki Amagasa, Hiroyuki Kitagawa, 
“Exploring Identical Users on GitHub and Stack Overflow”, 
in Proc. the 29th International Conference on Software Engineering and Knowledge Engineering (SEKE 2017), 
pp.584-589, Pittsburgh, USA, July 5-7, 2017