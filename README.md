# ############################################################ INSTALLATION
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
python runserver.py


# For Heroku
virtualenv venv
source venv/bin/activate
pip install flask (no sudo needed)
pip install gunicorn
pip freeze > requirements.txt
-> Add psycopg2 to the end of requirements.txt
heroku create
git push heroku master -f
heroku ps:scale web=1
heroku open