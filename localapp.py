print "Loading runserverlocal.py"

import os
os.environ['500DAYS_ENVIRONMENT'] = 'local'

from the500days import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
