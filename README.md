# ############################################################ INSTALLATION
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
python runserver.py


# For Heroku
Run virtualenv venv
Run source venv/bin/activate
Run pip install flask (no sudo needed)
Run pip install gunicorn
Run pip install flask-sqlalchemy
Run pip freeze > requirements.txt
Add psycopg2 to the end of requirements.txt
Run heroku addons:add shared-database
Run git push heroku master
heroku create
git push heroku master
heroku ps:scale web=1
heroku open