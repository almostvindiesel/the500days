import requests
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify

from the500days import app

@app.route('/500days')
@app.route('/')
def show_entries():
    return render_template('index.html')

if __name__ == '__main__':
    
	# !!! uncomment for running locally
    # app.run(debug=True)

    # heroku
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port)
