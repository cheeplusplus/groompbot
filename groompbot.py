#!/usr/bin/env python
# Posts YouTube videos from a channel to a subreddit

# Imports
import sys
import logging
import argparse
import json
import praw
import gdata.youtube.service

# YouTube functions
def get_playlist_uploads(username):
    """Get YouTube uploads by username."""
    yt_service = gdata.youtube.service.YouTubeService()
    uri = "http://gdata.youtube.com/feeds/api/users/%s/uploads" % username
    return yt_service.GetYouTubeVideoFeed(uri)

def get_videoId_from_entry(entry):
    """Get video ID from a YouTube entry."""
    return entry.id.text.split("/")[-1]

# Reddit functions
def get_reddit(settings):
    """Get a reference to Reddit."""
    r = praw.Reddit(user_agent=settings["reddit_ua"])
    try:
        r.login(settings["reddit_username"], settings["reddit_password"])
    except:
        logging.exception("Error logging into Reddit.")
        exit_app()
    return r

def submit_content(subreddit, title, link, fake_post=False):
    """Submit a link to a subreddit."""
    logging.info("Submitting %s (%s)" % (title, link))
    if fake_post:
        return

    try:
        subreddit.submit(title, url=link)
    except praw.errors.APIException:
        logging.exception("Error on link submission.")

def get_past_video_urls(subreddit):
    """Get all YouTube videos posted in the past hour."""
    hour = subreddit.get_new()
    for video in hour:
        if ("youtube" in video.url) or ("youtu.be" in video.url):
            yield video.url

# Main functions
def submit_feed_to_subreddit(subreddit, feed, repost_protection=False, fake_post=False):
    """Iterate through each YouTube feed entry and submit to Reddit."""
    past_video_urls = []
    if repost_protection:
        past_video_urls = list(get_past_video_urls(subreddit))
        print past_video_urls

    for entry in feed:
        title = unicode(entry.title.text, "utf-8")
        url = entry.media.player.url
        video_id = get_videoId_from_entry(entry)

        logging.debug("Video: %s (%s)" % (title, url))

        # Check if someone else already uploaded it
        for post_url in past_video_urls:
            if video_id in post_url:
                logging.debug("Video found in past video list.")
                break
        else:
            submit_content(subreddit, title, url, fake_post)

def load_settings():
    """Load settings from file."""
    try:
        settings_file = open("settings.json", "r")
    except IOError:
        logging.exception("Error opening settings.json.")
        exit_app()
    
    setting_str = settings_file.read()
    settings_file.close()

    try:
        settings = json.loads(setting_str)
    except ValueError:
        logging.exception("Error parsing settings.json.")
        exit_app()
    
    # Check integrity
    if len(settings["reddit_username"]) == 0:
        logging.critical("Reddit username not set.")
        exit_app()

    if len(settings["reddit_password"]) == 0:
        logging.critical("Reddit password not set.")
        exit_app()

    if len(settings["reddit_subreddit"]) == 0:
        logging.critical("Subreddit not set.")
        exit_app()

    if len(settings["reddit_ua"]) == 0:
        logging.critical("Reddit bot user agent not set.")
        exit_app()

    if len(settings["youtube_targets"]) == 0:
        logging.critical("YouTube targets not set.")
        exit_app()

    # Coerce list
    if isinstance(settings["youtube_targets"], dict):
        settings["youtube_targets"] = [settings["youtube_targets"]]

    # Enforce list
    if not isinstance(settings["youtube_targets"], list):
        logging.critical("YouTube targets not in correct format.")
        exit_app()

    settings["repost_protection"] = bool(settings["repost_protection"])

    # Get last upload position
    try:
        last_upload_file = open("lastupload.json", "r")
        last_upload_str = last_upload_file.read()
        last_upload_file.close()

        settings["youtube_lastupload"] = json.loads(last_upload_str)
        if not isinstance(settings["youtube_lastupload"], dict):
            settings["youtube_lastupload"] = {}

    except (IOError, ValueError):
        logging.info("No last uploaded video found.")
        settings["youtube_lastupload"] = {}

    return settings

def save_positions(settings):
    """Write most recent list of video IDs to file."""
    last_upload_file = open("lastupload.json", "w")
    last_upload_file.write(json.dumps(settings["youtube_lastupload"]))
    last_upload_file.close()

def exit_app():
    sys.exit(1)

def run_bot(args):
    """Start a run of the bot."""
    logging.info("Starting bot.")
    settings = load_settings()

    logging.info("Getting YouTube videos.")
    all_uploads = []

    # Download video list
    for target in settings["youtube_targets"]:
        channel = target["from"]
        subreddits = target["to"]
        if isinstance(subreddits, basestring):
            subreddits = [subreddits]

        # Create new lastupload format for channel if it doesn't exist
        if not channel in settings["youtube_lastupload"]:
            settings["youtube_lastupload"][channel] = {"recent": []}

        # Get uploads
        uploads = get_playlist_uploads(channel)
        if not uploads or not uploads.entry:
            # No items, probably due to etag
            logging.debug("Playlist %s returned no results", channel)
            continue

        uploads = uploads.entry

        recent_ids = map(get_videoId_from_entry, uploads)
        logging.info("Playlist %s got %d items" % (channel, len(uploads)))

        # Reverse from new to old, to old to new
        uploads.reverse()

        # Only get new uploads
        if len(settings["youtube_lastupload"][channel]["recent"]) > 0:
            uploads = [x for x in uploads if get_videoId_from_entry(x) not in settings["youtube_lastupload"][channel]["recent"]]

        # Update marker
        settings["youtube_lastupload"][channel]["recent"] = recent_ids

        logging.info("Adding %d uploads from channel %s" % (len(uploads), channel))
        if len(uploads) > 0:
            all_uploads.append((subreddits, uploads))

    if len(all_uploads) == 0:
        logging.info("No new uploads since last run.")
        return

    # Get reddit stuff
    logging.info("Logging into Reddit.")
    reddit = get_reddit(settings)
    all_subreddits = {}

    # Collect all subreddits
    for subreddits, uploads in all_uploads:
        for subreddit in subreddits:
            if subreddit not in all_subreddits:
                all_subreddits.update({subreddit: reddit.get_subreddit(subreddit)})

    # Submit entries
    logging.info("Submitting to Reddit.")
    for subreddits, uploads in all_uploads:
        for subreddit in subreddits:
            submit_feed_to_subreddit(all_subreddits[subreddit], uploads, settings["repost_protection"], args.fake)
    
    # Save newest position
    logging.info("Saving position.")
    save_positions(settings)
    
    logging.info("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post YouTube videos to Reddit.")
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Verbose output.")
    parser.add_argument("--fake", dest="fake", action="store_true", help="Don't actually submit to Reddit.")
    args = parser.parse_args()

    level = logging.WARNING
    if args.verbose:
        level = logging.DEBUG

    logging.basicConfig(level=level)

    try:
        run_bot(args)
    except SystemExit:
        logging.info("Exit called.")
    except:
        logging.exception("Uncaught exception.")

    logging.shutdown()
