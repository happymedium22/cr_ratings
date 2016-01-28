#!/usr/bin/env python

import requests
import HTMLParser
import re

class AnimeInfo(object):

    def __init__(self, title, description):
        self.title = title
        self.description = description
        self.averageRating = 0
        self.numFiveStarRating = 0
        self.numFourStarRating = 0
        self.numThreeStarRating = 0
        self.numTwoStarRating = 0
        self.numOneStarRating = 0

    def __str__(self):
        string = "Title: " + self.title
        string = string + "\nDescription: " + self.description
        string = string + "\n Average Rating: " + str(self.averageRating)
        string = string + "\n Number of Five Star Rating: " + \
                                        str(self.numFiveStarRating)
        string = string + "\n Number of Four Star Rating: " + \
                                        str(self.numFourStarRating)
        string = string + "\n Number of Three Star Rating: " + \
                                        str(self.numThreeStarRating)
        string = string + "\n Number of Two Star Rating: " + \
                                        str(self.numTwoStarRating)
        string = string + "\n Number of One Star Rating: " + \
                                        str(self.numOneStarRating)
        return string

    def getCsv(self):
        # csv
        return ",".join([self.title, 
                            str(self.averageRating),
                            str(self.numFiveStarRating),
                            str(self.numFourStarRating),
                            str(self.numThreeStarRating),
                            str(self.numTwoStarRating),
                            str(self.numOneStarRating)]) + "\n"

class CrunchyrollRatingHtmlParser(HTMLParser.HTMLParser):

    def __init__(self):
        # needs old style super
        HTMLParser.HTMLParser.__init__(self)
        self.inH3Tag = False
        self.inRatingsSection = False

        self.ratingCountRegexp = re.compile("\((?P<count>\d+)\)")

        self.inRatingLi = False

        self.averageRating = 0
        self.ratings = []

    def handle_starttag(self, tag, attrs):
        if tag == "h3":
            self.inH3Tag = True

        if self.inRatingsSection:
            if tag == "span":
                for attr in attrs:
                    if attr[0] == "content":
                        self.averageRating = float(attr[1])

            if tag == "li":
                if (len(attrs) > 0 and len(attrs[0]) > 0 and 
                        attrs[0][0] == "class" and 
                            (
                            attrs[0][1] == "5-star cf" or
                            attrs[0][1] == "4-star cf" or
                            attrs[0][1] == "3-star cf" or
                            attrs[0][1] == "2-star cf" or
                            attrs[0][1] == "1-star cf"
                            )):
                    self.inRatingLi = True

    def handle_endtag(self, tag):
        if tag == "h3":
            self.inH3Tag = False

        # assumes that ratings section is followed by a
        # javascript tag...crappy logic =[
        if self.inRatingsSection and tag == "script":
            self.inRatingsSection = False

            if tag == "li" and self.inRatingLi:
                self.inRatingLi = False
                print "exiting rating li"

    def __getCount(self, data):
        m = re.search(self.ratingCountRegexp, data)

        # return tuple of (foundData, count)
        if m is not None:
            return (True, m.group("count"))
        else:
            return (False, 0)

    def handle_data(self, data):
        if self.inH3Tag and data == "User Ratings":
            self.inRatingsSection = True

        if self.inRatingsSection:
            
            if self.inRatingLi:
                countTuple = self.__getCount(data)
                if countTuple[0]:
                    self.ratings.append(int(countTuple[1]))

class CrunchyrollratingHtmlParser(HTMLParser.HTMLParser):

    def __init__(self):
        # needs old style super
        HTMLParser.HTMLParser.__init__(self)

        self.__inScript = False
        self.allAnimeTitlesAndDescriptionString = ""

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.__inScript = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.__inScript = False

    def handle_data(self, data):
        if self.__inScript:
            # Expect long data only for
            # the anime title & description
            # javascript block
            if len(data) > 100000:
                self.allAnimeTitlesAndDescriptionString = data

def createBasicAnimeInfoList(animeTitleAndDescStr):
    titleAndDescList = [ x.strip()
                            for x in animeTitleAndDescStr.split("\n") ]
    
    basicAnimeInfoList = []

    for titleAndDesc in titleAndDescList:
        if titleAndDesc != "":
            m = re.search("\"name\":\"(?P<title>.+)\", \
                       \"description\":\"(?P<description>.+)\",",
                        titleAndDesc,
                        re.VERBOSE)

            if m is not None:
                # TODO: The description could be sanitized, but I'll just cope.
                basicAnimeInfoList.append(AnimeInfo(m.group("title"), 
                m.group("description")))

    return basicAnimeInfoList


def getAllBasicAnimeInfo():
    animeUrl = "http://www.crunchyroll.com/videos/anime/alpha?group=all"
    response = requests.get(animeUrl)

    encoding = response.encoding

    allAnimeHtml = response.text
    
    parser = CrunchyrollratingHtmlParser()
    parser.feed(allAnimeHtml)
    
    return createBasicAnimeInfoList(
        parser.allAnimeTitlesAndDescriptionString)


   
def updateInfoWithRatings(animeInfo):
    print "Getting ratings for", animeInfo.title

    cleanedTitle = animeInfo.title
    # properly encode the URL
    cleanedTitle = cleanedTitle.decode('unicode-escape').encode('utf-8')

    cleanedTitle = re.sub("[^A-Za-z0-9\s-]", "", cleanedTitle)

    cleanedTitle = cleanedTitle.replace(" ", "-")

    # replace multiple dashes with a single dash
    cleanedTitle = re.sub("[-]+", "-", cleanedTitle)


    titleUrl = "http://www.crunchyroll.com/" + cleanedTitle

    response = requests.get(titleUrl)

    if response.status_code != 200:
        print "\n\n======================================================\n\n"
        print "Could not get html for ", titleUrl
        print "Original title was: ", animeInfo.title
        print "Cleaned title was: ", cleanedTitle
        print "\n\n======================================================\n\n"
        return

    encoding = response.encoding
    ratingHtml = response.text

    parser = CrunchyrollRatingHtmlParser()

    parser.feed(ratingHtml)

    animeInfo.averageRating = parser.averageRating

    if (len(parser.ratings) > 0):
    
        orderedRatings = list(reversed(parser.ratings))
        animeInfo.numOneStarRating = orderedRatings[0]
        animeInfo.numTwoStarRating = orderedRatings[1]
        animeInfo.numThreeStarRating = orderedRatings[2]
        animeInfo.numFourStarRating = orderedRatings[3]
        animeInfo.numFiveStarRating = orderedRatings[4]
    else:
        print "No rating info for", animeInfo.title

    return 

def main():
    
    # Get all anime basic info
    
    allAnimeInfo = getAllBasicAnimeInfo()

    # Get ratings for each anime
    for animeInfo in allAnimeInfo:
        updateInfoWithRatings(animeInfo)
        with open("ratings.csv", "a") as f:
            f.write(animeInfo.getCsv())
            # terrible code that 
            f.close()

if __name__ == "__main__":
    main()
