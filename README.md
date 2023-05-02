# natural-language-processing-sentiment-analysis-for-twitter-sql-database
The purpose of this project was to investigate different methods of adding sentiments to Twitter posts and implement the preferrred method. Specifically, I wanted to add a sentiment section to an SQL database of Tweets, and populate those with sentiment polaritys based off the content of the tweet. Additionally, I wanted to update them in a batch format to make the program run faster.

**Tools Used:**

* `tensorflow` and `numpy` for machine learning and scientific computing
* `spaCY`, `NLTK` and `Transformers` for Natural Language Processing
* `PostgreSQL` for storing data
* `asyncpg` for getting data from SQL to Python
* `asyncio` for sending concurrent requests to an event loop, which delivers them to be processed (not useful here but could be scaled up in the future)
*  `docker` for containerizing the project
* `.toml` for storing configuration data
* `.yml` for storing configuration data for docker and postgres
* `makefile` for creating shortcuts for rerunning and rebuilding the docker container
* `pdm` for installing and managing dependencies


First, I researched different methods of NLP for sentiment analysis on sentences. I choose `spaCY`, `NLTK`, and HuggingFace's `Transformers`. Specifically, the model I used for Transformers was `"finiteautomata/bertweet-base-sentiment-analysis"`.

I tested the accuracy of the sentiment for some random sentences I constructed. 

| spaCY | NLTK | HuggingFace Transformers                 | Content for Polarity Measurement                                                                                                          |
|----------------|---------------|---------------------------------------|------------------------------------------------------------------------------------------------------------------|
|           0.18 |       -0.4215 | NEG', 'score': 0.50719153881073}      | A very, very, very slow-moving, aimless movie about a distressed, drifting young man.                            |   |
|  0.01458333333 |       -0.5507 | NEG', 'score': 0.8558710813522339}]   | Not sure who was more lost - the flat characters or the audience, nearly half of whom walked out.                |   |
|  -0.1229166667 |       -0.7178 | NEG', 'score': 0.9835329055786133}]   | Attempting artiness with black & white and clever camera angles, the movie disappointed.                         |   |
|       -0.24375 |             0 | NEG', 'score': 0.5657512545585632}]   | Very little music or anything to speak of.                                                                       |   |
|              1 |        0.6369 | POS', 'score': 0.9857653975486755}]   | The best scene in the movie was when Gerardo is trying to find a song that keeps running through his head.       |   |
|           -0.1 |         -0.25 | NEU', 'score': 0.61434406042099}]     | The rest of the movie lacks art, charm, meaning... If it's about emptiness, it works I guess because it's empty. |   |
|           -0.2 |       -0.4939 | NEG', 'score': 0.9729021787643433}]   | Wasted two hours                                                                                                 |   |
|            0.7 |        0.7003 | POS', 'score': 0.9911397099494934}]   | Saw the movie today and thought it was a good effort, good messages for kids.                                    |   |
|              0 |             0 | NEU', 'score': 0.9503368139266968}]   | A bit                                                                                                            |   |
|            0.7 |        0.5994 | POS', 'score': 0.9787101745605469}]   | Loved the casting of Jimmy Buffet as the lead.                                                                   |   |
|          -0.25 |       -0.2411 | NEU', 'score': 0.7688046097755432}]   | i'm not sure what those guys are up to.                                                                          |   |
|           -0.4 |       -0.4404 | NEG', 'score': 0.9838539958000183}]   | I'm tired of these people.                                                                                       |   |
|              0 |             0 | NEG', 'score': 0.9542802572250366}]   | America just isn't what it used to be.                                                                           |   |
|              0 |             0 |  'POS', 'score': 0.9923742413520813}] | Can't wait for this weekend!                                                                                     |   |
|              0 |             0 | NEU', 'score': 0.8812552690505981}]   | What were these people thinking?                                                                                 |   |
|              0 |             0 |  'POS', 'score': 0.9917930960655212}] | I'm stoked about the concert.                                                                                    |   |
|            0.2 |             0 |  'NEG', 'score': 0.961385190486908}]  | I can't believe people stood in front of me the whole time.                                                      |   |
|            0.5 |        0.4404 | POS', 'score': 0.971764326095581}]    | This is something that gets better with age.                                                                     |   |
|           -0.4 |       -0.4767 | NEG', 'score': 0.9818474650382996}]   | This is something that gets worse with age.                                                                      |   |
|              0 |             0 |  'NEU', 'score': 0.9516934752464294}] | Something feels different about this.                                                                            |   |

Here is my implementation of a polarity() function for each tool.

Transformers polarity()
```Python import os
from transformers import pipeline
from transformers import AutoTokenizer

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

model = "finiteautomata/bertweet-base-sentiment-analysis"
tokenizer = AutoTokenizer.from_pretrained(model)

def polarity(sentence) -> float:
    """returns exact polarity score of a sentence"""
    MAX_LEN = 725
    if len(sentence) > MAX_LEN:
        sentence = sentence[:MAX_LEN]
    return sentiment_pipeline(sentence)  # type: ignore

sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
```
NLTK polarity()
```Python import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

sia = SentimentIntensityAnalyzer()

nltk.download([  "vader_lexicon", ])

def polarity(sentence) -> dict:
    """returns exact polarity score of a sentence"""
    return sia.polarity_scores(sentence)
```

spaCY polarity()
```Python import spacy
from spacytextblob.spacytextblob import SpacyTextBlob

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("spacytextblob")

def polarity(sentence) -> float:
    """returns exact polarity score of a sentence"""
    doc = nlp(sentence)
    return doc._.blob.polarity
```

Second, I measured to see the speed of each model with different amounts of sentences.

| Sentences | spaCY (sec) | NLTK (sec) | Transformers (sec) |
|--------------|------------|-----------|--------------------|
|           10 |      1.196 |   0.00226 |              1.196 |
|         1000 |     7.9415 |   0.23229 |            102.747 |
|        10000 |     73.708 |    2.6488 |           1130.609 |

The way `polarity` is measured in `spaCY`, you are given a ***composite polarity***, meaning the polarity's value would be a spectrum between -1 and 1. -1 would be considered extremely negative, 1 would be considered extremely positive, and 0 would be considered neutral. The way `polarity` is measured in `NLTK` is very similar, except you are given the **positive**, **negative**, **neutral** and *composite* values. The way the `polarity` is calculated for `Transformers`, it has three different sentiments, **positive**, **negative**, and **neutral** and returns the largest polarity of the three. I investigated meticulously and could not find any way to achieve a **composite** polarity value in Transformer. While I found Transformers to be the most accurate of the three, ***I decided to go with NLTK*** because I wanted to be able to distinguish between "slightly positive" and "slightly negative" values when looking at individual posts and averages of large numbers of posts. Plus, there is the added bonus that it was the fastest of the three and more accurate than spaCY based on my prompts. 

**Things I noted while working through this project:**

* When deciding on how many to process at once in a batch, it needs to be calculated dynamically since the size of a database will change if we want to reuse this
* The size of the entry matters for some NLP tools like Transformers, but it doesn't for NLTK, which I ended up using
* Using the **Type()** function is helpful when using `Asyncpg` because sometimes its not clear what you are fetching
* In `Asyncpg`, you use `fetchrow()` for one row, and you use `fetch()` for sql queries that get multiple rows

Originally, I added the sentiment column with the following command.
```
ALTER TABLE TESTING.POST
ADD COLUMN sentiment NUMERIC
```
This is what one of the records looked like before the program runs. 

```
-[ RECORD 1 ]+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
id           | 10112943025779381
type         | 4
author       | 4
text         | "Interesting milestone: Workplace, our business communication tool, has hit 7 million paid subscribers -- a 40% increase in the last year." 
last_seen_at | 2021-08-17 14:55:26.348302
sentiment    | Null

```
Here is the same post after running the program, this ran for all posts in the postgres database. The sentiment for this is 0.905, very positive.
```
-[ RECORD 1 ]+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
id           | 10112943025779381
type         | 4
author       | 4
text         | "Interesting milestone: Workplace, our business communication tool, has hit 7 million paid subscribers -- a 40% increase in the last year." 
last_seen_at | 2021-08-17 14:55:26.348302
sentiment    | 0.905
```


Here are some of the psql and asyncpg related functions:
```python
async def get_post_text(id: int, conn):
    row = await conn.fetchrow("SELECT details FROM testing.post WHERE ID = $1", id)
    json_row = json.loads(str(row[0]))
    text = json_row["text"]
    return text

async def update_post_sentiment(id: int, text, conn):
    sentiment = polarity(text)
    QUERY = f"UPDATE testing.post SET sentiment = {sentiment} WHERE ID = {id};"
    await conn.execute(QUERY)

async def get_posts(i, window, conn):
    posts = await conn.fetch(
        f"SELECT * FROM testing.post WHERE ID BETWEEN {i} AND {i+window}"
    )
    posts_list = []

    for post in posts:
        json_row = json.loads(str(post["details"]))
        text = json_row["text"]

        id = post["id"]
        posts_list.append([id, text])

    return posts_list

async def get_max_id(conn):
    max_query = await conn.fetchrow(f"SELECT MAX(ID) from testing.post;")
    id = json.loads(str(max_query["max"]))
    return id

async def get_min_id(conn):
    min_query = await conn.fetchrow(f"SELECT MIN(ID) from testing.post;")
    id = json.loads(str(min_query["min"]))
    return id
    ```
