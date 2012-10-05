#!/usr/bin/env python
# Posts YouTube videos from a channel to a subreddit

# Imports
import sys
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
    r.login(settings["reddit_username"], settings["reddit_password"])
    return r

def getSubreddit(settings, reddit):
    """Get the subreddit."""
    return reddit.get_subreddit(settings["reddit_subreddit"])

def submitContent(subreddit, title, link):
    """Submit a link to a subreddit."""
    try:
        subreddit.submit(title, url=link)
    except praw.errors.APIException, e:
        print "Error on submit: %s" % e

def getPastVideos(subreddit):
    """Get all YouTube videos posted in the past hour."""
    hour = subreddit.get_new_by_date()
    for video in hour:
        if ("youtube" in video.url):
            yield video.url

# Main functions
def takeAndSubmit(settings, subreddit, feed):
    """Iterate through each YouTube feed entry and submit to Reddit."""
    pastVideos = list(getPastVideos(subreddit))

    for entry in feed:
        title = unicode(entry.title.text, "utf-8")
        url = entry.media.player.url
        videoid = getVideoIdFromEntry(entry)

        # Check if someone else already uploaded it
        escape = False
        for post in pastVideos:
            if (videoid in post):
                escape = True
                break

        if escape:
            continue

        # Submit
        print "Submitting %s" % title
        submitContent(subreddit, title, url)

def loadSettings():
    """Load settings from file."""
    try:
        settingsFile = open("settings.json", "r")
    except IOError, e:
        print "Error opening settings.json! Exiting. (%s)" % e
        sys.exit(1)
    
    settingStr = settingsFile.read()
    settingsFile.close()

    try:
        settings = json.loads(settingStr)
    except ValueError, e:
        print "Error parsing settings.json! Exiting. (%s)" % e
        sys.exit(1)
    
    # Check integrity
    if (len(settings["reddit_username"]) == 0):
        print "Reddit username not set. Exiting."
        sys.exit(1)

    if (len(settings["reddit_password"]) == 0):
        print "Reddit password not set. Exiting."
        sys.exit(1)

    if (len(settings["reddit_subreddit"]) == 0):
        print "Subreddit not set. Exiting."
        sys.exit(1)

    if (len(settings["youtube_account"]) == 0):
        print "YouTube account not set. Exiting."
        sys.exit(1)

    # Get last upload position
    try:
        lastUploadFile = open("lastupload.txt", "r")
        lastUpload = lastUploadFile.read()
        lastUploadFile.close()

        settings["youtube_lastupload"] = lastUpload
    except IOError:
        settings["youtube_lastupload"] = None

    return settings

def savePosition(position):
    """Write last position to file."""
    lastUploadFile = open("lastupload.txt", "w")
    lastUploadFile.write(position)
    lastUploadFile.close()

def runBot():
    """Start a run of the bot."""
    print "Starting bot."
    settings = loadSettings()

    print "Getting YouTube videos..."

    # Download video list
    uploads = getUserUploads(settings["youtube_account"]).entry
    
    # Hold first entry (newest)
    newestUpload = uploads[0]
    if (getVideoIdFromEntry(newestUpload) == settings["youtube_lastupload"]):
        print "No new uploaded videos. Exiting."
        sys.exit(1)
    
    # Reverse from old to new
    uploads.reverse()
    
    print "Logging into Reddit..."
    reddit = getReddit(settings)
    sr = getSubreddit(settings, reddit)
    
    print "Submitting to Reddit..."
    takeAndSubmit(settings, sr, uploads)
    
    print "Saving position..."
    videoid = getVideoIdFromEntry(newestUpload)
    savePosition(videoid)
    
    print "Done!"

if __name__ == "__main__":
    runBot()
