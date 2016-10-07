#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import datetime
import random
import requests
import requests.packages.urllib3
import json
import xmltodict, json
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify
from datetime import date,timedelta
from werkzeug.utils import secure_filename
requests.packages.urllib3.disable_warnings()
import sys
from the500days import app

# Required for correct utf8 encoding calls from heroku
reload(sys)
sys.setdefaultencoding("utf-8")

@app.route('/500days')
@app.route('/')
def show_entries():
    print '-'*50

    num_days_into_trip = days_into_trip()
    location = get_location_from_last_foursquare_checkin()
    gmaps_url = get_static_google_map(location)
    #instagram_data = get_insta_photos()

    #insta_images= instagram_data['images']
    #insta_locations= instagram_data['image_locations']
    insta_images = get_insta_photos()

    #print insta_locations
    
    return render_template('index2.html', num_days_into_trip=num_days_into_trip, location=location, gmaps_url=gmaps_url, images = insta_images)

def get_static_google_map(location):
    lat = location['latitude']
    long = location['longitude']
    api_key = 'AIzaSyDoemInMQhCNVqELI9R58ass8f7MnzvjPM' 
    gmaps_url = 'https://maps.googleapis.com/maps/api/staticmap?center=%s,%s&zoom=6&size=400x300&maptype=roadmap&markers=color:red%%7C%s,%s&key=%s' % (lat, long, lat, long, api_key)
    #print ("Problem getting map from gmaps api")
    return gmaps_url

# Returns the number of days we've been on the road


def days_into_trip():
    anchor_date = date(2015, 7, 6)
    now = date.today()
    current_date = date(now.year, now.month, now.day)
    time_delta = current_date - anchor_date
    return time_delta.days

if __name__ == '__main__':    
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port)


@app.route('/insta')
def get_insta_photos():

    access_token = '42490049.fc522f8.11667271a4984f93a7803ffdec6497cf'
    max_id = ''
    url = 'https://api.instagram.com/v1/users/42490049/media/recent/?access_token=%s&&max_id=%s' % (access_token, max_id)
    # https://api.instagram.com/v1/users/42490049/media/recent/?access_token=42490049.fc522f8.11667271a4984f93a7803ffdec6497cf

    print "\r\nGetting images from instagram api : \r\n", 
    print url

    try: 
        r = requests.get(url)
        r_json = r.json()

        images = []
        image_locations = []
        for media in r_json['data']:
            item = dict(
                low = media['images']['low_resolution']['url'],
                thumb = media['images']['thumbnail']['url'],
                thumb_width = media['images']['standard_resolution']['width'],
                thumb_height = media['images']['standard_resolution']['height'],
                standard = media['images']['standard_resolution']['url'],
                standard_width = media['images']['standard_resolution']['width'],
                standard_height = media['images']['standard_resolution']['height'],

                caption = media['caption']['text']#,

            )
            images.append(item) 

            #print item
            """
             if 'location' in media:
                if 'latitude' in media['location']:
                    item = dict(
                        location_name = media['location']['name'],
                        latitude = media['location']['latitude'],
                        longitude = media['location']['longitude']
                    )
                    image_locations.append(item)  
                    print item
            """
            #image_locations = None
        print "Found %s images from instagram api. Returning array" % (len(images))

    except Exception as e:
        print "-- Could not get data from instagram api: ", e.message, e.args
        images = []
        image_locations = []

    return images
    #return jsonify(images = images, image_locations = image_locations)



#http://maps.googleapis.com/maps/api/geocode/json?latlng=41.37835625181477,2.1654902381285197&sensor=true
@app.route('/fs')
def get_location_from_last_foursquare_checkin():

	#Get Last Checked-In Data
    try:
        foursquare_url = 'https://feeds.foursquare.com/history/6e67d1fa352b2bd8480c98adcf91d2a4.rss'
        print "Gettng data from foursquare api: \r\n", foursquare_url

        r = requests.get(foursquare_url)
        check_in_xml = r.text
        check_in_ordered_dict = xmltodict.parse(check_in_xml)
        check_in_json = json.dumps(check_in_ordered_dict['rss']['channel']['item'][0], indent=4)

        venue  = check_in_ordered_dict['rss']['channel']['item'][0]['title']
        lat_long  = check_in_ordered_dict['rss']['channel']['item'][0]['georss:point']
        lat_long_list = lat_long.split()
        latitude = lat_long_list[0]
        longitude = lat_long_list[1]

        print "--- From FS API latitude: ", latitude
        print "--- From FS API longitude: ", longitude
        print ""

        #Get City from Google Maps API
        googlemaps_url = "http://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&sensor=false" % (latitude, longitude)
        print "Getting location data from google maps api : \r\n", googlemaps_url

        try: 
            r = requests.get(googlemaps_url)
            g_json = r.json()

            for datums in g_json['results'][0]['address_components']:
                if datums['types'][0] == 'locality':
                    city = datums['long_name']
                    print "--- From Google Lat Long API, City: ", city
                if datums['types'][0] == 'country':
                    country = datums['long_name']
                    print "--- From Google Lat Long API, Country: ", country

        except Exception as e:
            print "--- Could not get data from google api: ", e.message, e.args
            print "Datum key threw exception: ", datums['types'][0]
            print "Datum value which threw exception: ",  datums['long_name']

            city = None
            country = None

    except Exception as e:
        print "--- Could not get data from foursquare api api: ", e.message, e.args
        city = None
        country = None
        latitude = None
        longitude = None
        venue = None

    location = {'city': city, 'country': country, 'latitude': latitude, 'longitude': longitude, 'venue': venue}
    return location
