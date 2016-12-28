print "Loading __init__.py ..."

import os
from flask import Flask
app = Flask(__name__)

# ------------------------------------------------------------------------------------------ Configuration 
if('500DAYS_ENVIRONMENT' in os.environ):
    if os.environ['500DAYS_ENVIRONMENT'] == 'heroku':
        print "-" * 50
        print "set os.environ from Heroku to app.config vars:"
        for key, value in os.environ.iteritems() :
            app.config[key] = value
            print key, value
        print "-" * 50
    elif os.environ['500DAYS_ENVIRONMENT'] == 'local':
        from the500days import settingslocal
    elif os.environ['500DAYS_ENVIRONMENT'] == 'pythonanywhere':
        from the500days import settingspa
# ------------------------------------------------------------------------------------------

import the500days.views