from xml.dom import minidom
import urllib

GEOCODER="http://ws.geonames.org/search?q=%s"

from math import * 

def haversine(co1, co2):
  lon1, lat1 = co1
  lon2, lat2 = co2
  # convert to radians
  lon1 = lon1 * pi / 180
  lon2 = lon2 * pi / 180
  lat1 = lat1 * pi / 180
  lat2 = lat2 * pi / 180
  # haversine formula
  dlon = lon2 - lon1
  dlat = lat2 - lat1
  a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
  c = 2 * atan2(sqrt(a), sqrt(1-a))
  km = 6367 * c
  miles = km * 0.621
  return miles

def get_geocode(place):
  url = GEOCODER % place
  fp = urllib.urlopen(url)
  data = fp.read()
  dom = minidom.parseString(data)
  geonames = dom.getElementsByTagName("geoname")
  if len(geonames) == 0:
    return (None, None)
  name = geonames[0].getElementsByTagName("name")[0].firstChild.nodeValue
  country = geonames[0].getElementsByTagName("countryCode")[0].firstChild.nodeValue
  lat = float(geonames[0].getElementsByTagName("lat")[0].firstChild.nodeValue)
  lng = float(geonames[0].getElementsByTagName("lng")[0].firstChild.nodeValue)
  return ("%s, %s" % (name, country), (lat, lng))

def cmd_distance_from(ensoapi, places):
  "Show the distance between two places"
  if places.find(" to ") != -1:
    place1, place2 = places.split(" to ", 1)
  else:
    place1, place2 = places.split(None, 1)
  show_distance(ensoapi, place1, place2)

def cmd_distance_to(ensoapi, place):
  "Show the distance from Stourbridge to the place"
  show_distance(ensoapi, "Stourbridge", place)

def show_distance(ensoapi, place1, place2):
  place1name, place1loc = get_geocode(place1)
  if not place1name:
    ensoapi.display_message("Couldn't identify '%s' as a place" % place1)
    return
  place2name, place2loc = get_geocode(place2)
  if not place2name:
    ensoapi.display_message("Couldn't identify '%s' as a place" % place2)
    return
  distance = haversine(place1loc, place2loc)
  ensoapi.display_message("Distance between %s and %s: %s miles" % (
    place1name, place2name, round(distance, 1)
  ))

