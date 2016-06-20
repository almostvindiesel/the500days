# ############################################################ INSTALLATION
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
python app.py


# For Heroku
virtualenv venv
source venv/bin/activate
pip install flask (no sudo needed)
pip install gunicorn
pip freeze > requirements.txt
echo 'psycopg2' >> requirements.txt
echo 'requests' >> requirements.txt
heroku create
git push heroku master -f
heroku ps:scale web=1
heroku open

heroku local web