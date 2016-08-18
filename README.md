---
# TheaterTrailers

This is a python script that automates, downloading of trailers from youtube using youtube-dl. Trailers are downloaded if their release date hasn't hit yet and are deleted when it does. Files and folders are named with the standard Plex and The Movie DB naming convention, a "Coming Soon" image is copied in as `poster.jpg` and two versions of the trailer are stored, one with `-trailer` in the name so Plex recognizes it as the trailer and the other is recognized as the movie.

---

# Screenshot

![Plex Web View](http://i.imgur.com/BaH7En3.png)

---

# Installation

*Please note, this module is currently only compatible with Python 2.7.x systems. Python 3.x has not been tested.*

1. Install Python 2.7.x. 
   * Python for Windows can be found [here](https://www.python.org/downloads/windows/)
   * For all other OS's, check out [this stack overflow](http://stackoverflow.com/questions/1093322/how-do-i-check-what-version-of-python-is-running-my-script) to check what version your system is using
2. Install PIP if it isn't already present
   * Check [this out](https://pip.pypa.io/en/stable/installing/) for help
3. Install [youtube_dl](https://rg3.github.io/youtube-dl/index.html)
   * `pip install --upgrade youtube_dl`
4. Install [tmdbsimple](https://pypi.python.org/pypi/tmdbsimple)
   * `pip install tmdbsimple`
5. Sign up at Movie DB for an account and [get a personal api key](https://www.themoviedb.org/documentation/api)
6. Clone this repository or download it where you want
7. Edit the ~~config file~~ to include your api key, as well as the path to wherever you cloned/downloaded the repository. Adjust other settings as necessary
    * *the config file is not currently working. For now, edit the script directly+*
8. Run manually like any other script.
    * *cron and windows task scheduler are currently untested but should work fine*

---

# Credit

Thank you to the [youtube-dl](https://github.com/rg3/youtube-dl) team

This product uses the TMDb API but is not endorsed or certified by TMDb
![Plex Web View](http://i.imgur.com/YR33JTt.png)
