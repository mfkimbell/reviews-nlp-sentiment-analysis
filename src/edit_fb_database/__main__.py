import os
import json
import asyncpg
import asyncio
import nltk

nltk.download(
    [
        "names",
        "stopwords",
        "state_union",
        "twitter_samples",
        "movie_reviews",
        "averaged_perceptron_tagger",
        "vader_lexicon",
        "punkt",
    ]
)

# doppler run -- pdm add nltk

from nltk.sentiment import SentimentIntensityAnalyzer

sia = SentimentIntensityAnalyzer()

from toolset.FileIO import load_yml_file

from toolset.PSQL.AsyncPSQLConnect import connect

# from transformers import pipeline

user_username = INSERT USER NAME
user_password = INSERT PASSWORD

database_url = (
    INSERT DATABASE
)

config = load_yml_file("./local_config.yml")

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
# supposedly this should limit some of the warnings caused by tensor


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


# def polarity(sentence) -> float:
#     """returns exact polarity score of a sentence"""
#     MAX_LEN = 725
#     if len(sentence) > MAX_LEN:
#         sentence = sentence[:MAX_LEN]
#     return sentiment_pipeline(sentence)  # type: ignore


def polarity(sentence) -> float:
    """returns exact polarity score of a sentence"""
    results = sia.polarity_scores(sentence)
    return results["compound"]


def test_polarity() -> float:
    """used for testing purposes"""
    return 1.1


async def amain():
    conn = await asyncpg.connect(
        database_url, user=user_username, password=user_password
    )

    max_id = await get_max_id(conn)
    min_id = await get_min_id(conn)

    # testing ids
    # max_id = 10159433081801772
    # min_id = 1015943308180167

    difference = max_id - min_id
    window = difference // 10000
    print("window: ", window)

    for i in range(min_id, max_id, window):
        posts = await get_posts(i, window, conn)
        if len(posts) > 0:
            print(posts)
        else:
            print(f"No posts for window: {i} - {i+window}")
        for post in posts:
            if post[1] != None:
                await update_post_sentiment(post[0], post[1], conn)


if __name__ == "__main__":
    print("begin __name__ function")
    loop = asyncio.new_event_loop()
    loop.run_until_complete(amain())
    print("end __name__ function")

    