# Running locally 
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
python localapp.py


# Running on Heroku 
virtualenv venv
source venv/bin/activate
pip install flask (no sudo needed)
pip install gunicorn
pip freeze > requirements.txt
heroku create
git push heroku master -f
heroku ps:scale web=1
heroku open
heroku local web


# Refreshing Instagram Access Token 
Visit this link to get the access token:
https://api.instagram.com/oauth/authorize/?client_id=fc522f8ae493478c9b83009bac960755&redirect_uri=http%3A%2F%2Fjoanneandjohn.com%2F500days&response_type=token 


curl \-F 'client_id=CLIENT-ID' \
    -F 'client_secret=CLIENT-SECRET' \
    -F 'grant_type=authorization_code' \
    -F 'redirect_uri=YOUR-REDIRECT-URI' \
    -F 'code=CODE' \
    https://api.instagram.com/oauth/access_token


# Mac OS Notes
If you get the following exception, you may need to finish mysql configuration by entering in this command:
  Command "python setup.py egg_info" failed with error code 1 in /private/var/folders/nd/s5whpw7s439fd1jdfs06k05m0000gn/T/pip-build-Vm_m1z/mysql-python/
  
export PATH=$PATH:/usr/local/mysql/bin

