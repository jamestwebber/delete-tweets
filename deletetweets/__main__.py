#!/usr/bin/env python

import json
import logging
import sys

import click
import click_log

from deletetweets import deletetweets


__author__ = "Koen Rouwhorst + James Webber"
__version__ = "1.0.6"


log = logging.getLogger("deletetweets")


def create_logger():
    root_log = logging.getLogger()
    click_log.basic_config(root_log)

    root_log.handlers[0].setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )


@click.group()
@click.option("--config", type=click.Path(), default="credentials.json")
@click_log.simple_verbosity_option(log, default="WARNING")
@click.pass_context
def cli(ctx, config):
    create_logger()
    ctx.ensure_object(dict)

    with open(config) as f:
        ctx.obj["credentials"] = json.load(f)

    if set(ctx.obj["credentials"]) != {
        "consumer_key",
        "consumer_secret",
        "access_token_key",
        "access_token_secret",
    }:
        log.error("Twitter API credentials not set.")
        sys.exit(1)

    log.debug(f"Loaded credentials from {config}")


@cli.command(help="Delete old tweets")
@click.option(
    "-j",
    "--tweetjs-path",
    required=True,
    type=click.Path(exists=True),
    help="The tweet.js file from Twitter data archive",
)
@click.option("-s", "--since", type=click.DateTime(), help="Inclusive")
@click.option("-u", "--until", type=click.DateTime())
@click.option(
    "-f",
    "--filters",
    multiple=True,
    type=click.Choice(["reply", "retweet"]),
    help="Restrict to replies and/or retweets",
)
@click.option("--spare-ids", type=click.Path(exists=True))
@click.option("--spare-min-likes", "min_likes", type=int, default=0)
@click.option("--spare-min-retweets", "min_rts", type=int, default=0)
@click.option(
    "--dry-run", is_flag=True, help="Don't do anything, just see what would happen"
)
@click.pass_context
def delete(
    ctx,
    tweetjs_path,
    since=None,
    until=None,
    filters=None,
    spare_ids=None,
    min_likes=0,
    min_rts=0,
    dry_run=False,
):
    if spare_ids is not None:
        with open(spare_ids) as fh:
            spare_ids = {line.strip() for line in fh}
        log.debug(f"Loaded {len(spare_ids)}")
    else:
        spare_ids = set()

    filters = set(filters) if filters is not None else set()

    deletetweets.delete(
        ctx.obj["credentials"],
        tweetjs_path,
        since,
        until,
        filters,
        spare_ids,
        min_likes,
        min_rts,
        dry_run,
    )


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
