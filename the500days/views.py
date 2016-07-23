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

from the500days import app

@app.route('/500days')
@app.route('/')
def show_entries():
    num_days_into_trip = days_into_trip()
    location = get_location_from_last_foursquare_checkin()
    gmaps_url= get_static_google_map(location)
    print '-'*50
    print gmaps_url
    print '-'*50

    return render_template('index.html', num_days_into_trip=num_days_into_trip, location=location, gmaps_url=gmaps_url)

def get_static_google_map(location):
    lat = location['latitude']
    long = location['longitude']
    api_key = 'AIzaSyDoemInMQhCNVqELI9R58ass8f7MnzvjPM' 
    gmaps_url = 'https://maps.googleapis.com/maps/api/staticmap?center=%s,%s&zoom=4&size=200x100&maptype=roadmap&markers=color:red%%7Clabel:X%%7C%s,%s&key=%s' % (lat, long, lat, long, api_key)
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


#http://maps.googleapis.com/maps/api/geocode/json?latlng=41.37835625181477,2.1654902381285197&sensor=true
@app.route('/fs')
def get_location_from_last_foursquare_checkin():

	#Get Last Checked-In Data
    try:
        #raise Exception('spam', 'eggs')
        foursquare_url = 'https://feeds.foursquare.com/history/6e67d1fa352b2bd8480c98adcf91d2a4.rss'
        r = requests.get(foursquare_url)
        check_in_xml = r.text

        check_in_ordered_dict = xmltodict.parse(check_in_xml)
        check_in_json = json.dumps(check_in_ordered_dict['rss']['channel']['item'][0], indent=4)

        location  = check_in_ordered_dict['rss']['channel']['item'][0]['title']
        lat_long  = check_in_ordered_dict['rss']['channel']['item'][0]['georss:point']
        lat_long_list = lat_long.split()
        latitude = lat_long_list[0]
        longitude = lat_long_list[1]

        #Get City from Google Maps API
        googlemaps_url = "http://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(latitude) + 	"," + str(longitude) + "&sensor=true"
        rg = requests.get(googlemaps_url)
        geolocation_json = rg.json()
        city = geolocation_json['results'][0]['address_components'][3]['short_name']
        country = geolocation_json['results'][0]['address_components'][5]['long_name']

        location  = {'city': city, 'country': country, 'latitude': latitude, 'longitude': longitude}
    except:
        print("Problem getting location from foursquare api")
        location  = None

    return location
