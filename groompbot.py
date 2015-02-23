#!/usr/bin/env python
# Posts YouTube videos from a channel to a subreddit

# Imports
import sys
import logging
import json
import praw
import requests

# YouTube functions
def get_playlist_uploads(api_key, playlist, etag=None):
    """Get YouTube uploads by username."""
    uri = "https://www.googleapis.com/youtube/v3/playlistItems"
    payload = {"part": "snippet", "playlistId": playlist, "maxResults": 5, "key": api_key}

    # Use the etag
    if etag:
        headers = {"If-None-Match": etag}
    else:
        headers = None

    r = requests.get(uri, params=payload, headers=headers)
    if r.status_code == 304:
        # Nothing has changed since the last execution
        return None

    js = r.json()
    return js

def get_videoId_from_entry(entry):
    """Get video ID from a YouTube entry."""
    return entry["snippet"]["resourceId"]["videoId"]

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

def get_subreddit(settings, reddit):
    """Get the subreddit."""
    return reddit.get_subreddit(settings["reddit_subreddit"])

def submit_content(subreddit, title, link):
    """Submit a link to a subreddit."""
    logging.info("Submitting %s (%s)" % (title, link))
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
def submit_feed_to_subreddit(settings, subreddit, feed):
    """Iterate through each YouTube feed entry and submit to Reddit."""
    past_video_urls = []
    if settings["repost_protection"]:
        past_video_urls = list(get_past_video_urls(subreddit))
        print past_video_urls

    for entry in feed:
        title = entry["snippet"]["title"]
        video_id = get_videoId_from_entry(entry)
        url = "https://www.youtube.com/watch?v=%s" % video_id

        logging.debug("Video: %s (%s)" % (title, url))

        # Check if someone else already uploaded it
        for post_url in past_video_urls:
            if video_id in post_url:
                logging.debug("Video found in past video list.")
                break
        else:
            submit_content(subreddit, title, url)

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

    if len(settings["youtube_playlists"]) == 0:
        logging.critical("YouTube playlist not set.")
        exit_app()

    # Coerce single string to list
    if isinstance(settings["youtube_playlists"], basestring):
        settings["youtube_playlists"] = [settings["youtube_playlists"]]

    if len(settings["youtube_api_key"]) == 0:
        logging.critical("YouTube API key not set.")
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

def run_bot():
    """Start a run of the bot."""
    logging.info("Starting bot.")
    settings = load_settings()

    logging.info("Getting YouTube videos.")
    all_uploads = []

    # Download video list
    for playlist in settings["youtube_playlists"]:
        # Create new lastupload format for playlist if it doesn't exist
        if not playlist in settings["youtube_lastupload"]:
            settings["youtube_lastupload"][playlist] = {"recent": [], "etag": None}

        # Get ETag
        try:
            etag = settings["youtube_lastupload"][playlist]["etag"]
        except KeyError:
            etag = None

        # Get uploads
        items = get_playlist_uploads(settings["youtube_api_key"], playlist, etag)
        if not items:
            # No items, probably due to etag
            logging.debug("Playlist %s returned no results", playlist)
            continue

        etag = items["etag"]
        uploads = items["items"]
        recent_ids = map(get_videoId_from_entry, uploads)
        logging.info("Playlist %s got %d items" % (playlist, len(uploads)))

        # Reverse from new to old, to old to new
        uploads.reverse()

        # Only get new uploads
        if len(settings["youtube_lastupload"][playlist]["recent"]) > 0:
            uploads = [x for x in uploads if get_videoId_from_entry(x) not in settings["youtube_lastupload"][playlist]["recent"]]

        # Update marker
        settings["youtube_lastupload"][playlist]["recent"] = recent_ids
        settings["youtube_lastupload"][playlist]["etag"] = etag

        logging.info("Adding %d uploads from playlist %s" % (len(uploads), playlist))
        all_uploads.extend(uploads)

    if len(all_uploads) == 0:
        logging.info("No new uploads since last run.")
        exit_app()
        return

    # Get reddit stuff
    logging.info("Logging into Reddit.")
    reddit = get_reddit(settings)
    sr = get_subreddit(settings, reddit)
    
    # Submit entries
    logging.info("Submitting to Reddit.")
    submit_feed_to_subreddit(settings, sr, all_uploads)
    
    # Save newest position
    logging.info("Saving position.")
    save_positions(settings)
    
    logging.info("Done!")

if __name__ == "__main__":
    logging.basicConfig()

    try:
        run_bot()
    except SystemExit:
        logging.info("Exit called.")
    except:
        logging.exception("Uncaught exception.")

    logging.shutdown()
