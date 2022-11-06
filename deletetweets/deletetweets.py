import io
import json
import logging

import twitter
from datetime import datetime
from dateutil.parser import parse

log = logging.getLogger(__name__)


class TweetDestroyer(object):
    def __init__(self, twitter_api, dry_run=False):
        self.twitter_api = twitter_api
        self.dry_run = dry_run

    def destroy(self, tweet_id):
        try:
            log.debug(f"delete tweet {tweet_id}")
            if not self.dry_run:
                self.twitter_api.DestroyStatus(tweet_id)
        except twitter.TwitterError as err:
            log.exception(f"Exception: {err.message}\n")


class TweetReader(object):
    def __init__(
        self,
        reader,
        since_date=None,
        until_date=None,
        filters=None,
        spare=None,
        min_likes=0,
        min_retweets=0,
    ):
        self.reader = reader
        self.since_date = datetime.min if since_date is None else since_date
        self.until_date = datetime.now() if until_date is None else until_date
        self.filters = filters or set()
        self.spare = spare or set()
        self.min_likes = 0 if min_likes is None else min_likes
        self.min_retweets = 0 if min_retweets is None else min_retweets

    def read(self):
        for row in self.reader:
            if row["tweet"].get("created_at", "") != "":
                tweet_date = parse(row["tweet"]["created_at"], ignoretz=True)
                if tweet_date >= self.until_date or tweet_date <= self.since_date:
                    continue

            if (
                "retweets" in self.filters
                and not row["tweet"].get("full_text").startswith("RT @")
            ) or (
                "replies" in self.filters
                and row["tweet"].get("in_reply_to_user_id_str") == ""
            ):
                continue

            if row["tweet"].get("id_str") in self.spare:
                continue

            if (
                self.min_likes
                and int(row["tweet"].get("favorite_count")) >= self.min_likes
            ) or (
                self.min_retweets
                and int(row["tweet"].get("retweet_count")) >= self.min_retweets
            ):
                continue

            yield row


def delete(
    credentials,
    tweetjs_path,
    since_date,
    until_date,
    filters,
    spare_ids,
    min_likes,
    min_rts,
    dry_run=False,
):
    with io.open(tweetjs_path, mode="r", encoding="utf-8") as tweetjs_file:
        count = 0

        api = twitter.Api(**credentials, sleep_on_rate_limit=True)
        destroyer = TweetDestroyer(api, dry_run)

        tweets = json.loads(tweetjs_file.read()[25:])
        for row in TweetReader(
            tweets, since_date, until_date, filters, spare_ids, min_likes, min_rts
        ).read():
            destroyer.destroy(row["tweet"]["id_str"])
            count += 1

        log.info(f"Number of deleted tweets: {count}\n")
