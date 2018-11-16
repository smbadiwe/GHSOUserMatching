# Probabilistic Joint Dataset of GitHub and Stack Overflow

* Copyright (c) 2017 Takahiro Komamizu
* License: CC-BY-SA-4.0
* [Author homepage](http://taka-coma.pro/)
* Resaerch paper > http://dx.doi.org/10.18293/SEKE2017-109
* Please cite
```
Takahiro Komamizu, Yasuhiro Hayase, Toshiyuki Amagasa, Hiroyuki Kitagawa, 
“Exploring Identical Users on GitHub and Stack Overflow”, 
in Proc. the 29th International Conference on Software Engineering and Knowledge Engineering (SEKE 2017), 
pp.584-589, Pittsburgh, USA, July 5-7, 2017
```

## Data 
- Dump of SO (PostgreSQL dump)
  - http://2013.msrconf.org/challenge_data/201208_stack_overflow_postgres_dump.tar.bz
- Dump of GH (mySQL dump)
  - source: ~~http://ghtorrent.org/downloads/msr14-mysql.gz~~ (no more available)
  	- Instead, you can get from GHTorrent (http://ghtorrent.org/downloads.html)
	- mysql-postgresql-converter to make it PostgreSQL dump
		- https://github.com/lanyrd/mysql-postgresql-converter
- User pairs from SO and GH, who have same email (through MD5 hashing)
  - data/common_users.csv


## Learning

### Assumption
- Both dumps of SO and GH are in the same database (namely, gh_so).
	- Rename tables in SO into "so_" + original name.
	- Because easy to join tables between SO and GH.
- Common users are stored in the database (gh_so).
	- Table: gh_so_common_users (so_user_id, gh_user_id) 

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
