#!/usr/bin/env python
# -*- coding: utf-8 -*-

print "Loading charts.py ..."

import os
import datetime
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
from models import db, InstaMediaAsset

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text
from flaskext.mysql import MySQL
import MySQLdb


@app.route('/spendlocationday', methods=['GET','POST'])
def spend_per_day_per_country():

    # Set filters for variables
    """
    if request.args.get('parent_category'):
        session['parent_category'] = request.args.get('parent_category')
        print "--- Changed parent_category filter to: ", session['parent_category']
    if  not ('parent_category' in session) or session['parent_category'] == 'reset' or session['parent_category'] == '':
        session['parent_category'] = ''
    """

    if 'location' in session:
        location = session['location']
    else:
        location = 'country'

    if 'category' in session:
        if session['category'] == 'reset' or session['category'] == '':
            category_filter = ''
            session['category'] = ''
            category = ''
        else: 
            category = session['category']
            category_filter = " and category ='%s'" % (category)
    else:
        category = ''
        category_filter = ''


    print "Location: ", location
    print "Category: ", category
    print "Category SQL: ", category_filter


    sql =  "select tdd.%s, cast(round(sum(amount_usd) / min(cd.days)) as signed) 'spend_per_day' \
            from trip_expenses te \
              left join travel_destination_day tdd on te.date = tdd.date \
              left join ( \
                select %s, count(*) days \
                from travel_destination_day \
                where date between '2015-10-04' and '2016-11-03' \
                group by 1 \
              ) cd on cd.%s = tdd.%s \
            where te.date between '2015-10-04' and '2016-11-03' \
             %s\
            group by 1 \
            order by 2 desc" % (location, location, location, location, category_filter)
    print "SQL: \r\n", sql



    result = db.engine.execute(sql)
    data = []
    for row in result:
        datum = dict (
            location  = row[0],
            value = row[1]
        )
        data.append(datum)

    return jsonify(data)


@app.route('/maxlikespermonth')
def max_likes():
    sql = text("select date_format(created_date,'%Y-%m') month, max(likes) max_likes from insta_media_asset group by 1 order by 1 asc")
    result = db.engine.execute(sql)
    data = []
    for row in result:
        datum = dict (
            date  = row[0],
            value = row[1]
        )
        data.append(datum)

    return jsonify(data)

@app.route('/avglikespermonth')
def avg_likes():
    sql = text("select date_format(created_date,'%Y-%m') month, cast(sum(likes)/count(*) as SIGNED) ratio from insta_media_asset group by 1 order by 1 asc")
    result = db.engine.execute(sql)
    data = []
    for row in result:
        datum = dict (
            date  = row[0],
            value = row[1]
        )
        data.append(datum)

    return jsonify(data)

@app.route('/json')
def simple_json():
    dates = ['2013-01','2013-02','2013-03']
    values = [53,165,269]

    data = []

    item = dict(
        date = '2013-01',
        value = 53
    )
    data.append(item)
    
    item = dict(
        date = '2013-02',
        value = 57
    )
    data.append(item)

    item = dict(
        date = '2013-03',
        value = 100
    )
    data.append(item)


    return jsonify(data)

