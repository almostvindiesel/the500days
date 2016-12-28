#!/usr/bin/env python
# -*- coding: utf-8 -*-

print "Loading snapinstadash.py ..."

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

# --------------------------------------------------------------------------------
# Dashboard Home

@app.route('/snapvsinstadau', methods=['GET'])
def dau():

    filter_values = initialize_filter_values()
    filter_sql = initialize_filter_sql()

    countries = get_dashboard_filters(filter_values, 'country')
    genders = get_dashboard_filters(filter_values, 'gender')
    age_ranges = get_dashboard_filters(filter_values, 'age_range')

    return render_template('snapinstadash.html', countries=countries, age_ranges=age_ranges, genders=genders)


# --------------------------------------------------------------------------------
# API Helpfer Functions

def initialize_filter_values():
    filter_values = dict()
    filter_values['measure'] = '';
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


def update_filter_values(filter_values): 
    filter_categories = ['genders','countries','age_ranges']

    print "prior filter_values: ", filter_values

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

def get_dashboard_filters(filter_values, filter_name):
    if filter_name == 'country':
        sql =  "select distinct country from market_sizing"
    elif filter_name == 'age_range':
        sql =  "select distinct age_range from v_market_sizing"
    elif filter_name == 'gender':
        sql =  "select distinct gender from market_sizing"

    result = db.engine.execute(sql)
    datums  = []
    for row in result:
        datum =  {filter_name: row[0]}
        for item in filter_values['countries']:
            if item == row[0]:
                datum['selected'] = 'selected'
                break;
            else: 
                datum['selected'] = False
        datums.append(datum)
    return datums


# --------------------------------------------------------------------------------
# API: Endpoints which return data results or filtering selections


@app.route('/daudash/api/genderpct.json', methods=['GET','POST'])
def gender_pct():

    filter_values = initialize_filter_values()
    filter_sql    = initialize_filter_sql()

    filter_values = update_filter_values(filter_values)
    filter_sql    = update_filter_sql(filter_values, filter_sql)

    measure = request.form.get('measure') #snapchat or instagram

    sql =  "select \
              num.gender, \
              cast(round(sum(case when num.measure = '%s' then num.dau else 0 end) * 100 / \
                   max(case when den.measure = '%s' then den.dau else 0 end),0) as signed) measure_pct \
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
            order by 1 asc"  % (measure, measure, \
                                filter_sql['genders'], filter_sql['age_ranges'], filter_sql['countries'], \
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

    backgroundColor = ['#ce3535','#2219ef']
    snap = dict (
        label = measure,
        data  = snap_data,
        backgroundColor = backgroundColor
    )

    datasets.append(snap)
    data = dict (
        labels    = countries,
        datasets  = datasets
    )

    return jsonify(data)


@app.route('/daudash/api/agepct.json', methods=['GET','POST'])
def age_pct():

    filter_values = initialize_filter_values()
    filter_sql    = initialize_filter_sql()

    filter_values = update_filter_values(filter_values)
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
        backgroundColor = "#3366fc"
    )
    datasets.append(snap)
    datasets.append(insta)

    data = dict (
        labels    = countries,
        datasets  = datasets
    )

    return jsonify(data)


@app.route('/daudash/api/countrypenetration.json', methods=['GET','POST'])
def country_penetration():

    filter_values = initialize_filter_values()
    filter_sql    = initialize_filter_sql()

    filter_values = update_filter_values(filter_values)
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
        backgroundColor = "#3366fc"
    )
    datasets.append(snap)
    datasets.append(insta)

    data = dict (
        labels    = countries,
        datasets  = datasets
    )

    return jsonify(data)


@app.route('/daudash/api/countrydau.json', methods=['GET','POST'])
def country_dau():

    filter_values = initialize_filter_values()
    filter_sql    = initialize_filter_sql()

    filter_values = update_filter_values(filter_values)
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
        backgroundColor = "#3366fc"
    )
    datasets.append(snap)
    datasets.append(insta)

    data = dict (
        labels    = countries,
        datasets  = datasets
    )

    return jsonify(data)

