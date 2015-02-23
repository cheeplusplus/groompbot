Groompbot
=========

[Groompbot](https://github.com/AndrewNeo/groompbot): A bot that posts new videos from YouTube to a subreddit

Built by [AndrewNeo](http://www.reddit.com/u/AndrewNeo) to post [Game Grumps](http://www.youtube.com/gamegrumps) videos to the [/r/gamegrumps](http://www.reddit.com/r/gamegrumps) subreddit. It should work fine for other YouTube channels and subreddits.

Usage
-----

It's set up to be run by a cronfile, probably every minute or so at most.

Configuration
-------------

Configuration for the bot is set up in the settings.json file. The configuration file (which should be copied from settings.json.default) should contain the reddit bot username, password, the subreddit to post to, an approperate useragent, and the YouTube API key and playlist ID(s) to read from.

Dependencies
------------

Groompbot depends on the following external libraries:

* [praw](https://github.com/praw-dev/praw/) - Reddit library

YouTube info
------------

Due to changes in the YouTube v3 API, reading the info we want is a little more of a pain to get started.

1. [Register your application with Google](https://console.developers.google.com/) so you can submit API requests. Create a server API access key, this is what will go into the settings file.
2. Fetch the playlist IDs you want to read from. You can follow [these general directions](http://stackoverflow.com/a/13504900/151495) with the YouTube [API Explorer](https://developers.google.com/youtube/v3/docs/search/list).

License
-------

Groompbot is free to use under the MIT License.
