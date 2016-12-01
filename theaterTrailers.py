#!/usr/bin/python

from __future__ import unicode_literals
from datetime import datetime
import youtube_dl
import tmdbsimple as tmdb
import logging
import json
import shutil
import re
import os
import time
import requests

#Local Modules
from ConfigMapper.configMapper import ConfigSectionMap


# Global items
MovieDict = {}
MovieList = []
DirsDict = {}
ResultsDict = {}
search = tmdb.Search()

# Config Variables
tmdb.API_KEY = ConfigSectionMap("Main")['tmdb_api_key']
TheaterTrailersHome = ConfigSectionMap("Main")['theatertrailershome']
playlistEndVar = int(ConfigSectionMap("Main")['playlistendvar'])
youtubePlaylist = ConfigSectionMap("Main")['youtubeplaylist']
runCleanup = ConfigSectionMap("Main")['runcleanup']
trailerLocation = ConfigSectionMap("Main")['trailerlocation']
redBand = ConfigSectionMap("Main")['redband']
plexHost = ConfigSectionMap("Main")['plexhost']
plexPort = ConfigSectionMap("Main")['plexport']
plexToken = ConfigSectionMap("Main")['plextoken']
cacheRefresh = int(ConfigSectionMap("Main")['cacherefresh'])
cacheDir = os.path.join(TheaterTrailersHome, "Cache")
if not os.path.exists(cacheDir):
  os.makedirs(cacheDir)

# Pause in seconds. TMDB has a rate limit of 40 requests per 10 seconds
pauseRate = .25

# Logging options
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh = logging.FileHandler(os.path.join(TheaterTrailersHome, 'theaterTrailers.log'))
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

# Sets the Current Date in ISO format
currentDate = time.strftime('%Y-%m-%d')


# Main detirmines the flow of the module
def main():

  if runCleanup == 'True':
    cleanup()

  checkCashe()

  infoDownloader(youtubePlaylist)
  
  # Querries tmdb and updates the release date in the dictionary
  for item in MovieList:
    try:
      if MovieDict['item']['Release Date'] in MovieDict:
        continue
    except KeyError as ke1:
      with open(os.path.join(cacheDir, 'theaterTrailersCache.json'), 'a+') as fp:
        try:
          DB_Dict = json.load(fp)
          MovieDict[item]['Release Date'] = DB_Dict[item]['Release Date']

        except (KeyError, ValueError) as e:
          tmdbInfo(item)
          tempList = search.results
          tempList.reverse()
          for s in tempList:
            releaseDate = s['release_date']
            releaseDateList = releaseDate.split('-')
            try:
              if (int(releaseDateList[0]) - 1) <= int(MovieDict[item]['Trailer Release']) <= (int(releaseDateList[0]) + 1):
                MovieDict[item]['Release Date'] = releaseDate
            except ValueError:
              pass

        except AttributeError as ae1:
          logger.error("{0}, AttributeError".format(item))
          continue

    # Adds the movies to the cache
    title = item.strip()
    try:
      yearVar = MovieDict[item]['Release Date'].split('-')
      trailerYear = yearVar[0].strip()
      updateCache(MovieDict[item]['url'], title, trailerYear)
    except KeyError as error:
      print error
      logger.debug("{0} is missing its release date".format(item))
    

    

def checkCashe():
    if os.path.exists(cacheDir):
      if os.path.isfile(os.path.join(cacheDir, 'theaterTrailersCache.json')):
        with open(os.path.join(cacheDir, 'theaterTrailersCache.json')) as fp:
          try:
            cacheDict = json.load(fp)
            creationDate = datetime.strptime(cacheDict['Creation Date'] , '%Y-%m-%d').date()
            Current_Date = datetime.strptime(currentDate, '%Y-%m-%d').date()
            age = Current_Date - creationDate
            age = age.days
            logger.info('The cache is {0} days old'.format(age))
            if(age==cacheRefresh):
              os.remove(os.path.join(cacheDir, 'theaterTrailersCache.json'))

          except ValueError as e:
            logger.debug("Cache file empty")

    else:
      logger.info("making cache dir")
      os.makedirs(cacheDir)


def checkDownloadDate(passedTitle):
  try:
    if currentDate < MovieDict[passedTitle]['Release Date']:
      return True
  except KeyError as ke2:
    logger.error(MovieDict[passedTitle] + " has no release date")


def updateCache(string, passedTitle, yearVar):
  with open(os.path.join(cacheDir, 'theaterTrailersCache.json'), 'a+') as fp:
    try:
      jsonDict = json.load(fp)
      try:
        if jsonDict[passedTitle]['url'] == string:
          if jsonDict[passedTitle]['status'] == 'Downloaded':
            if checkFiles(passedTitle, yearVar):
              logger.debug('{0} from {1} is already downloaded'.format(passedTitle, string))
              return
            else:
              logger.debug('{0} from {1} was in the cache but did not exist'.format(passedTitle, string))
              if yearVar == MovieDict[passedTitle]['Trailer Year']:
                videoDownloader(string,passedTitle,yearVar)
              else:
                with open(os.path.join(cacheDir, 'theaterTrailersTempCache.json'), 'a+') as temp1:
                  jsonDict[passedTitle]['Trailer Year'] = MovieDict[passedTitle]['Trailer Year']
                  videoDownloader(string,passedTitle,MovieDict[passedTitle]['Trailer Year'])
                  json.dump(jsonDict, temp1, indent=4)
          elif jsonDict[passedTitle]['status'] == 'Released':
            logger.debug('{0} from {1} has been released'.format(passedTitle, string))
            return
          else:
            logger.error('error with {0} from {1}'.format(passedTitle, string))
        else:
          logger.debug('New trailer for ' + passedTitle)
          with open(os.path.join(cacheDir, 'theaterTrailersTempCache.json'), 'a+') as temp1:
            jsonDict[passedTitle]['url'] = string
            if checkDownloadDate(passedTitle):
              shutil.rmtree(os.path.join(trailerLocation, '{0} ({1})'.format(passedTitle, yearVar)))
              videoDownloader(string,passedTitle,yearVar)
              jsonDict[passedTitle]['status'] = 'Downloaded'
            else:
              jsonDict[passedTitle]['status'] = 'Released'
            json.dump(jsonDict, temp1, indent=4)

      except KeyError as e:
        logger.debug('Creating New Entry')
        with open(os.path.join(cacheDir, 'theaterTrailersTempCache.json'), 'a+') as temp2:
          jsonDict[passedTitle] = MovieDict[passedTitle]
          if checkDownloadDate(passedTitle):
            videoDownloader(string,passedTitle,yearVar)
            jsonDict[passedTitle]['status'] = 'Downloaded'
          else:
            jsonDict[passedTitle]['status'] = 'Released'
          json.dump(jsonDict, temp2, indent=4)

    except ValueError as e:
      logger.debug('Creating Cache')
      jsonDict = {}
      jsonDict['Creation Date'] = currentDate
      jsonDict[passedTitle] = MovieDict[passedTitle]
      if checkDownloadDate(passedTitle):
        videoDownloader(string,passedTitle,yearVar)
        jsonDict[passedTitle]['status'] = 'Downloaded'
      else:
        jsonDict[passedTitle]['status'] = 'Released'
        json.dump(jsonDict, fp, indent=4)

  if os.path.isfile(os.path.join(cacheDir, 'theaterTrailersTempCache.json')):
    shutil.move(os.path.join(cacheDir, 'theaterTrailersTempCache.json'), os.path.join(cacheDir, 'theaterTrailersCache.json'))


# Downloads the video, names it and copies the resources to the folder
def videoDownloader(string, passedTitle, yearVar):
  # Options for the video downloader
  ydl1_opts = {
    'outtmpl': os.path.join(TheaterTrailersHome, 'Trailers', '{0} ({1})'.format(passedTitle, yearVar), '{0} ({1}).mp4'.format(passedTitle, yearVar)),
    'ignoreerrors': True,
    'format': 'mp4',
  }
  with youtube_dl.YoutubeDL(ydl1_opts) as ydl:
    logger.info("downloading {0} from {1}".format(passedTitle, string))
    ydl.download([string])
    shutil.copy2(
        os.path.join(trailerLocation, '{0} ({1})'.format(passedTitle, yearVar), '{0} ({1}).mp4'.format(passedTitle, yearVar)),
        os.path.join(trailerLocation, '{0} ({1})'.format(passedTitle, yearVar), '{0} ({1})-trailer.mp4'.format(passedTitle, yearVar))
      )
    shutil.copy2(
        os.path.join(TheaterTrailersHome, 'res', 'poster.jpg'), 
        os.path.join(trailerLocation, '{0} ({1})'.format(passedTitle, yearVar))
      )
    updatePlex()


# Downloads info for the videos from the playlist
def infoDownloader(playlist):
  # Options for the info downloader
  ydl_opts = {
    'skip_download': True,
    'ignoreerrors': True,
    'playlistreverse': True,
    'playliststart': 1,
    'playlistend': playlistEndVar,
    'quiet': False,
    'matchtitle': '.*\\btrailer\\b.*', 
    'extract_flat': True,
  }
  with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(playlist)
  
  for x in info['entries']:
    MovieVar = x['title'].encode('ascii',errors='ignore')
    MovieVar = MovieVar.replace(':', '')
    if 'Official' in MovieVar:
      regexedTitle = re.search('^.*(?=(Official))', MovieVar)
    elif [e for e in MovieList if e in MovieVar]:
      regexedTitle = re.search('.*?(?=Trailer)', MovieVar)
    elif redBand == True:
      if 'Red Band' in MovieVar:
        regexedTitle = re.search('.*?(?=Red)', MovieVar)
    else:
      # Throws out edge cases
      continue
    trailerYear = re.search('(?<=\().*(?=\))', MovieVar)
    TempDict = { 'url' : info['entries'][info['entries'].index(x)]['url']}
    movieTitle = regexedTitle.group(0).strip()
    MovieDict[movieTitle] = TempDict
    MovieDict[movieTitle]['Trailer Release'] = trailerYear.group(0)
    MovieDict[movieTitle]['Movie Title'] = movieTitle
    MovieList.append(movieTitle)


def updatePlex():
  r = requests.get('http://{0}:{1}/library/sections/1/refresh?X-Plex-Token={2}'.format(plexHost, plexPort, plexToken))
  if r.status_code != 200:
    logger.warning("The plex server at {0}:{1} did not respond correctly to the request".format(plexHost, plexPort))

# Returns results from tmdb
def tmdbInfo(item):
  response = search.movie(query=item)
  logger.info("querying the movie db for {0}".format(item))
  time.sleep(pauseRate)
  return search.results
  

def checkFiles(title, year):
  if os.path.isfile(os.path.join(trailerLocation, '{0} ({1})'.format(title, year), '{0} ({1}).mp4'.format(title, year))):
    if not os.path.isfile(os.path.join(trailerLocation, '{0} ({1})'.format(title, year), '{0} ({1})-trailer.mp4'.format(title, year))):
      shutil.copy2(
        os.path.join(trailerLocation, '{0} ({1})'.format(title, year), '{0} ({1}).mp4'.format(title, year)),
        os.path.join(trailerLocation, '{0} ({1})'.format(title, year), '{0} ({1})-trailer.mp4'.format(title, year))
      )
      updatePlex()
    if not os.path.isfile(os.path.join(trailerLocation, '{0} ({1})'.format(title, year), 'poster.jpg')):
      shutil.copy2(
        os.path.join(TheaterTrailersHome, 'res', 'poster.jpg'), 
        os.path.join(trailerLocation, '{0} ({1})'.format(title, year))
      )
      updatePlex()
    return True
  if os.path.isfile(os.path.join(trailerLocation, '{0} ({1})'.format(title, year), '{0} ({1})-trailer.mp4'.format(title, year))):
    if not os.path.isfile(os.path.join(trailerLocation, '{0} ({1})'.format(title, year), '{0} ({1}).mp4'.format(title, year))):
      shutil.copy2(
        os.path.join(trailerLocation, '{0} ({1})'.format(title, year), '{0} ({1})-trailer.mp4'.format(title, year)),
        os.path.join(trailerLocation, '{0} ({1})'.format(title, year), '{0} ({1}).mp4'.format(title, year))
      )
      updatePlex()
    if not os.path.isfile(os.path.join(trailerLocation, '{0} ({1})'.format(title, year), 'poster.jpg')):
      shutil.copy2(
        os.path.join(TheaterTrailersHome, 'res', 'poster.jpg'), 
        os.path.join(trailerLocation, '{0} ({1})'.format(title, year))
      )
      updatePlex()
    return True
  else:
    return False


# Gets a list of the movies in the directory and removes old movies
def cleanup():
  if not os.path.isdir(os.path.join(TheaterTrailersHome, 'Trailers')):
    return
  else:
    dirsList = os.listdir(os.path.join(TheaterTrailersHome, 'Trailers'))
    for item in dirsList:
      dirsTitle = re.search('^.*(?=(\())', item)
      dirsTitle = dirsTitle.group(0).strip()
      dirsYear = re.search('(?<=\().*(?=\))', item)
      dirsYear = dirsYear.group(0).strip()
      filePath = os.path.join(cacheDir, 'theaterTrailersCache.json')
      if (os.path.isfile(filePath)):
        with open(filePath, 'r') as fp:
          try:
            data = json.load(fp)
            releaseDate = data[dirsTitle]['Release Date']
            if releaseDate <= currentDate:
              logger.debug("Removing " + dirsTitle)
              shutil.rmtree(os.path.join(TheaterTrailersHome, 'Trailers', '{0} ({1})'.format(dirsTitle, dirsYear)))
              updatePlex()
          except KeyError as ex:
            logger.debug("Removing " + dirsTitle)
            shutil.rmtree(os.path.join(TheaterTrailersHome, 'Trailers', '{0} ({1})'.format(dirsTitle, dirsYear)))
            updatePlex()
          except ValueError as Ve:
            noCacheCleanup(dirsTitle, dirsYear)      

    
def noCacheCleanup(dirsTitle, dirsYear):
  s = tmdbInfo(dirsTitle)
  for s in search.results:
    releaseDate = s['release_date']
    releaseDateList = releaseDate.split('-')
    if dirsYear == releaseDateList[0]:
      if releaseDate <= currentDate:
        logger.debug("Removing " + dirsTitle)
        shutil.rmtree(os.path.join(TheaterTrailersHome, 'Trailers', '{0} ({1})'.format(dirsTitle, dirsYear)))
        updatePlex()
    
    break    


if __name__ == "__main__":
  main()
