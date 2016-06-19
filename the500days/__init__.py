from flask import Flask
app = Flask(__name__)

#app.config.from_envvar('THE500DAYS_SETTINGS', silent=True)

import the500days.views