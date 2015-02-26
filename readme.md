Groompbot
=========

[Groompbot](https://github.com/AndrewNeo/groompbot): A bot that posts new videos from YouTube to a subreddit

Built by [AndrewNeo](http://www.reddit.com/u/AndrewNeo) to post [Game Grumps](http://www.youtube.com/gamegrumps) videos to the [/r/gamegrumps](http://www.reddit.com/r/gamegrumps) subreddit. It should work fine for other YouTube channels and subreddits.

Usage
-----

It's set up to be run by a cronfile, probably every minute or so at most.

Configuration
-------------

Configuration for the bot is set up in the settings.json file. The configuration file (which should be copied from settings.json.default) should contain the reddit bot username, password, an approperate useragent, and the YouTube channels to pull from attached to the subreddits to post to.

The "youtube_targets" section should be a dictionary, or an array of dictionaries. Each dictionary should have a "from" key (the YouTube channel) and a "to" key, the latter of which can either be a string or an array of strings for which subreddits to post to.

For example,

    "youtube_targets": [
        {"from": "youtubechannel", to: "subreddit"},
        {"from": "anotherchannel", to: ["subredditA", "subredditB"]}
    ]

submits videos from `youtubechannel` to `subreddit`, and videos from `anotherchannel` to both `subredditA` and `subredditB`.

Dependencies
------------

Groompbot depends on the following external libraries:

* [praw](https://github.com/praw-dev/praw/) - Reddit library
* [gdata](http://code.google.com/p/gdata-python-client/) - Google Data API

License
-------

Groompbot is free to use under the MIT License.
