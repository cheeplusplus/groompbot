Groompbot
=========

[Groompbot](https://github.com/AndrewNeo/groompbot): A bot that posts new videos from YouTube to a subreddit

Built by [AndrewNeo](http://www.reddit.com/u/AndrewNeo) to post [Game Grumps](http://www.youtube.com/gamegrumps) videos to the [/r/gamegrumps](http://www.reddit.com/r/gamegrumps) subreddit. It should work fine for other YouTube channels and subreddits.

Usage
-----

It's set up to be run by a cronfile, probably every minute or so at most.

Configuration
-------------

Configuration for the bot is set up in the settings.json file. The configuration file (which should be copied from settings.json.default) should contain the reddit bot username, password, the subreddit to post to, an approperate useragent, and the YouTube account to read from.

Dependencies
------------

Groombot depends on the following external libraries:

* [praw](https://github.com/praw-dev/praw/) - Reddit library
* [gdata](http://code.google.com/p/gdata-python-client/) - Google Data API