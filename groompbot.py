#!/usr/bin/env python
# Posts YouTube videos from a channel to a subreddit

# Imports
import sys
import logging
import json
import praw
import gdata.youtube.service

# YouTube functions
def getUserUploads(username):
    """Get YouTube uploads by username."""
    yt_service = gdata.youtube.service.YouTubeService()
    uri = "http://gdata.youtube.com/feeds/api/users/%s/uploads" % username
    return yt_service.GetYouTubeVideoFeed(uri)

def getVideoIdFromEntry(entry):
    """Get video ID from a YouTube entry."""
    return entry.id.text.split("/")[-1]

# Reddit functions
def getReddit(settings):
    """Get a reference to Reddit."""
    r = praw.Reddit(user_agent=settings["reddit_ua"])
    try:
        r.login(settings["reddit_username"], settings["reddit_password"])
    except:
        logging.exception("Error logging into Reddit.")
        exitApp()
    return r

def getSubreddit(settings, reddit):
    """Get the subreddit."""
    return reddit.get_subreddit(settings["reddit_subreddit"])

def submitContent(subreddit, title, link):
    """Submit a link to a subreddit."""
    logging.info("Submitting %s (%s)", (title, link))
    try:
        subreddit.submit(title, url=link)
    except praw.errors.APIException:
        logging.exception("Error on link submission.")

def getPastVideos(subreddit):
    """Get all YouTube videos posted in the past hour."""
    hour = subreddit.get_new_by_date()
    for video in hour:
        if ("youtube" in video.url):
            yield video.url

# Main functions
def takeAndSubmit(settings, subreddit, feed):
    """Iterate through each YouTube feed entry and submit to Reddit."""
    pastVideos = []
    if (settings["repost_protection"]):
        pastVideos = list(getPastVideos(subreddit))

    for entry in feed:
        title = unicode(entry.title.text, "utf-8")
        url = entry.media.player.url
        videoid = getVideoIdFromEntry(entry)
        logging.debug("Video: %s (%s)", (title, url))

        # Check if someone else already uploaded it
        for post in pastVideos:
            if (videoid in post):
                logging.debug("Video found in past video list.")
                break
        else:
            submitContent(subreddit, title, url)

def loadSettings():
    """Load settings from file."""
    try:
        settingsFile = open("settings.json", "r")
    except IOError:
        logging.exception("Error opening settings.json.")
        exitApp()
    
    settingStr = settingsFile.read()
    settingsFile.close()

    try:
        settings = json.loads(settingStr)
    except ValueError:
        logging.exception("Error parsing settings.json.")
        exitApp()
    
    # Check integrity
    if (len(settings["reddit_username"]) == 0):
        logging.critical("Reddit username not set.")
        exitApp()

    if (len(settings["reddit_password"]) == 0):
        logging.critical("Reddit password not set.")
        exitApp()

    if (len(settings["reddit_subreddit"]) == 0):
        logging.critical("Subreddit not set.")
        exitApp()

    if (len(settings["reddit_ua"]) == 0):
        logging.critical("Reddit bot user agent not set.")
        exitApp()

    if (len(settings["youtube_account"]) == 0):
        logging.critical("YouTube account not set.")
        exitApp()

    settings["repost_protection"] = bool(settings["repost_protection"])

    # Get last upload position
    try:
        lastUploadFile = open("lastupload.txt", "r")
        lastUpload = lastUploadFile.read()
        lastUploadFile.close()

        settings["youtube_lastupload"] = lastUpload
    except IOError:
        logging.info("No last uploaded video found.")
        settings["youtube_lastupload"] = None

    return settings

def savePosition(position):
    """Write last position to file."""
    lastUploadFile = open("lastupload.txt", "w")
    lastUploadFile.write(position)
    lastUploadFile.close()

def exitApp():
    sys.exit(1)

def runBot():
    """Start a run of the bot."""
    logging.info("Starting bot.")
    settings = loadSettings()

    logging.info("Getting YouTube videos.")

    # Download video list
    uploads = getUserUploads(settings["youtube_account"]).entry
    newestUpload = uploads[0]

    # Reverse from new to old, to old to new
    uploads.reverse()
    
    # Only get new uploads
    try:
        videoIdList = map(getVideoIdFromEntry, uploads)
        indexOfLastUpload = videoIdList.index(settings["youtube_lastupload"])
        uploads = uploads[indexOfLastUpload + 1:]
        if (len(uploads) == 0):
            logging.info("No new uploads since last run.")
            exitApp()
    except ValueError:
        # Ignore a failure if lastupload value isn't in list
        pass

    # Get reddit stuff
    logging.info("Logging into Reddit.")
    reddit = getReddit(settings)
    sr = getSubreddit(settings, reddit)
    
    # Submit entries
    logging.info("Submitting to Reddit.")
    takeAndSubmit(settings, sr, uploads)
    
    # Save newest position
    logging.info("Saving position.")
    videoid = getVideoIdFromEntry(newestUpload)
    savePosition(videoid)
    
    logging.info("Done!")

if __name__ == "__main__":
    logging.basicConfig()

    try:
        runBot()
    except SystemExit:
        logging.info("Exit called.")
    except:
        logging.exception("Uncaught exception.")

    logging.shutdown()
