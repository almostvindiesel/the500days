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



@app.route('/bars.json', methods=['GET'])
def bars_json():

    return render_template('bars.json')

def initialize_filter_values():
    filter_values = dict()
    filter_values['genders'] = list()
    filter_values['countries'] = list()
    filter_values['age_ranges'] = list()
    return filter_values

def initialize_filter_sql():
    filter_sql = dict()
    filter_sql['genders'] = ''
    filter_sql['countries'] = ''
    filter_sql['age_ranges'] = ''
    return filter_sql

def update_filter_values(filter_values, filter_sql): 
    filter_categories = ['genders','countries','age_ranges']

    print "prior   filter_values: ", filter_values

    for filter_category in filter_categories:
        if request.form.get(filter_category):
            filter_selections = json.loads(request.form.get(filter_category))
            for filter_selection in filter_selections:
                filter_values[filter_category].append(filter_selection)
    
    print "updated filter_values: ", filter_values

    return filter_values

def update_filter_sql(filter_values, filter_sql): 

    if len(filter_values['genders']) == 0:
        filter_sql['genders'] = ' and 1=1'
    else:
        filter_sql['genders'] =' and gender in (' + ','.join(map(apply_quotes, filter_values['genders'])) + ')'

    if len(filter_values['age_ranges']) == 0:
        filter_sql['age_ranges'] = ' and 1=1'
    else:
        filter_sql['age_ranges'] =' and age_range in (' + ','.join(map(apply_quotes, filter_values['age_ranges'])) + ')'

    if len(filter_values['countries']) == 0:
        filter_sql['countries'] = ' and 1=1'
    else:
        filter_sql['countries'] =' and country in (' + ','.join(map(apply_quotes, filter_values['countries'])) + ')'
    
    print "updated filter sql: ", filter_sql
    return filter_sql
    
def apply_quotes(x):
    return "'%s'" % text(x)


@app.route('/dau/update', methods=['GET','POST'])
def apply_filters():

    filter_values = initialize_filter_values()
    filter_sql = initialize_filter_sql()

    filter_values = update_filter_values(filter_values, filter_sql)
    filter_sql = update_filter_sql(filter_values, filter_sql)

    return jsonify(filter_values)


def get_countries(filter_values):
    sql =  "select distinct country from market_sizing"
    result = db.engine.execute(sql)
    countries  = []
    for row in result:
        datum =  {'country': row[0]}
        for item in filter_values['countries']:
            if item == row[0]:
                datum['selected'] = 'selected'
                break;
            else: 
                datum['selected'] = False
        countries.append(datum)
    return countries

def get_age_ranges(filter_values):
    sql =  "select distinct age_range from v_market_sizing"
    result = db.engine.execute(sql)
    age_ranges  = []
    for row in result:
        datum =  {'age_range': row[0]}
        for item in filter_values['age_ranges']:
            if item == row[0]:
                datum['selected'] = 'selected'
                break;
            else: 
                datum['selected'] = False
        age_ranges.append(datum)
    return age_ranges

def get_genders(filter_values):
    sql =  "select distinct gender from market_sizing"
    result = db.engine.execute(sql)
    genders  = []
    for row in result:
        datum =  {'gender': row[0]}
        for item in filter_values['genders']:
            if item == row[0]:
                datum['selected'] = 'selected'
                break;
            else: 
                datum['selected'] = False
        genders.append(datum)
    return genders


@app.route('/dau', methods=['GET'])
def dau():

    filter_values = initialize_filter_values()
    filter_sql = initialize_filter_sql()

    countries = get_countries(filter_values)
    genders = get_genders(filter_values)
    age_ranges = get_age_ranges(filter_values)

    return render_template('dau.html', countries=countries, age_ranges=age_ranges, genders=genders)

@app.route('/genderpct.json', methods=['GET','POST'])
def gender_pct():

    filter_values = initialize_filter_values()
    filter_sql    = initialize_filter_sql()

    filter_values = update_filter_values(filter_values, filter_sql)
    filter_sql    = update_filter_sql(filter_values, filter_sql)

    sql =  "select \
              num.gender, \
              cast(round(sum(case when num.measure = 'snapchat' then num.dau else 0 end) * 100 / \
                   max(case when den.measure = 'snapchat' then den.dau else 0 end),0) as signed) sc_pct, \
              cast(round(sum(case when num.measure = 'instagram' then num.dau else 0 end) * 100 / \
                   max(case when den.measure = 'instagram' then den.dau else 0 end),0) as signed) ig_pct \
            from ( \
                select \
                  measure, \
                  sum(dau) dau \
                from v_market_sizing \
                where measure in ('snapchat', 'instagram') \
                         %s \
                         %s \
                         %s \
                group by 1 \
            ) den inner join ( \
                select \
                  measure, \
                  gender, \
                  sum(dau) dau \
                from v_market_sizing \
                where measure in ('snapchat', 'instagram') \
                         %s \
                         %s \
                         %s \
                group by 1,2 \
            ) num on num.measure = den.measure \
            group by 1 \
            order by 1 asc"  % (filter_sql['genders'], filter_sql['age_ranges'], filter_sql['countries'], \
                                filter_sql['genders'], filter_sql['age_ranges'], filter_sql['countries'])

    result = db.engine.execute(sql)

    data = []
    datasets = []
    countries  = []
    snap_data  = []
    insta_data = []
    for row in result:
        countries.append(row[0])
        snap_data.append(row[1])
        insta_data.append(row[2])

    snap = dict (
        label = 'snapchat',
        data  = snap_data,
        backgroundColor = "#f6d93e"
    )
    insta = dict (
        label = 'instagram',
        data  = insta_data,
        backgroundColor = "#7102ff"
    )
    datasets.append(snap)
    datasets.append(insta)

    data = dict (
        labels    = countries,
        datasets  = datasets
    )

    return jsonify(data)

@app.route('/agepct.json', methods=['GET','POST'])
def age_pct():

    filter_values = initialize_filter_values()
    filter_sql    = initialize_filter_sql()

    filter_values = update_filter_values(filter_values, filter_sql)
    filter_sql    = update_filter_sql(filter_values, filter_sql)

    sql =  "select \
              num.age_range, \
              cast(round(sum(case when num.measure = 'snapchat' then num.dau else 0 end) * 100 / \
                   max(case when den.measure = 'snapchat' then den.dau else 0 end),0) as signed) sc_pct, \
              cast(round(sum(case when num.measure = 'instagram' then num.dau else 0 end) * 100 / \
                   max(case when den.measure = 'instagram' then den.dau else 0 end),0) as signed) ig_pct \
            from ( \
                select \
                  measure, \
                  sum(dau) dau \
                from v_market_sizing \
                where measure in ('snapchat', 'instagram') \
                         %s \
                         %s \
                         %s \
                group by 1 \
            ) den inner join ( \
                select \
                  measure, \
                  age_range, \
                  sum(dau) dau \
                from v_market_sizing \
                where measure in ('snapchat', 'instagram') \
                         %s \
                         %s \
                         %s \
                group by 1,2 \
            ) num on num.measure = den.measure \
            group by 1 \
            order by 1 asc" % (filter_sql['genders'], filter_sql['age_ranges'], filter_sql['countries'], \
                               filter_sql['genders'], filter_sql['age_ranges'], filter_sql['countries'])

    result = db.engine.execute(sql)

    data = []
    datasets = []
    countries  = []
    snap_data  = []
    insta_data = []
    for row in result:
        countries.append(row[0])
        snap_data.append(row[1])
        insta_data.append(row[2])

    snap = dict (
        label = 'snapchat',
        data  = snap_data,
        backgroundColor = "#f6d93e"
    )
    insta = dict (
        label = 'instagram',
        data  = insta_data,
        backgroundColor = "#7102ff"
    )
    datasets.append(snap)
    datasets.append(insta)

    data = dict (
        labels    = countries,
        datasets  = datasets
    )

    return jsonify(data)

@app.route('/countrypenetration.json', methods=['GET','POST'])
def country_penetration():

    filter_values = initialize_filter_values()
    filter_sql    = initialize_filter_sql()

    filter_values = update_filter_values(filter_values, filter_sql)
    filter_sql    = update_filter_sql(filter_values, filter_sql)

    sql =  "select \
              country, \
              cast( sum(case when measure = 'snapchat' then dau else 0 end) as signed) sc_dau, \
              cast( sum(case when measure = 'instagram' then dau else 0 end) as signed) ig_dau, \
              cast(round(sum(case when measure = 'snapchat' then dau else 0 end) * 100 / \
                   sum(case when measure = 'smartphones' then users else 0 end),0) as signed) sc_pen, \
              cast(round(sum(case when measure = 'instagram' then dau else 0 end) * 100 / \
                   sum(case when measure = 'smartphones' then users else 0 end),0) as signed) ig_pen, \
              cast( sum(case when measure = 'smartphones' then users else 0 end) as signed) smartphones \
            from v_market_sizing \
            where measure in ('snapchat', 'instagram', 'smartphones') \
             %s\
             %s\
             %s\
            group by 1 \
            order by 2 desc \
            limit 10" % (filter_sql['genders'], filter_sql['age_ranges'], filter_sql['countries'])

    print '-' * 50
    print sql
    print filter_sql
    print filter_values
    print '-' * 50

    result = db.engine.execute(sql)

    data = []
    datasets = []
    countries  = []
    snap_data  = []
    insta_data = []
    for row in result:
        countries.append(row[0])
        snap_data.append(row[3])
        insta_data.append(row[4])

    snap = dict (
        label = 'snapchat',
        data  = snap_data,
        backgroundColor = "#f6d93e"
    )
    insta = dict (
        label = 'instagram',
        data  = insta_data,
        backgroundColor = "#7102ff"
    )
    datasets.append(snap)
    datasets.append(insta)

    data = dict (
        labels    = countries,
        datasets  = datasets
    )

    return jsonify(data)

@app.route('/countrydau.json', methods=['GET','POST'])
def country_dau():

    filter_values = initialize_filter_values()
    filter_sql    = initialize_filter_sql()

    filter_values = update_filter_values(filter_values, filter_sql)
    filter_sql    = update_filter_sql(filter_values, filter_sql)

    sql =  "select \
              country, \
              cast( sum(case when measure = 'snapchat' then dau else 0 end) as signed) sc_dau, \
              cast( sum(case when measure = 'instagram' then dau else 0 end) as signed) ig_dau \
            from v_market_sizing \
            where measure in ('snapchat', 'instagram') \
             %s\
             %s\
             %s\
            group by 1 \
            order by 2 desc \
            limit 10" % (filter_sql['genders'], filter_sql['age_ranges'], filter_sql['countries'])

    result = db.engine.execute(sql)

    data = []
    datasets = []
    countries  = []
    snap_data  = []
    insta_data = []
    for row in result:
        countries.append(row[0])
        snap_data.append(row[1])
        insta_data.append(row[2])

    snap = dict (
        label = 'snapchat',
        data  = snap_data,
        backgroundColor = "#f6d93e"
    )
    insta = dict (
        label = 'instagram',
        data  = insta_data,
        backgroundColor = "#7102ff"
    )
    datasets.append(snap)
    datasets.append(insta)

    data = dict (
        labels    = countries,
        datasets  = datasets
    )

    return jsonify(data)

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

