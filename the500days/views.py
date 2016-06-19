import requests
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify

from the500days import app
#from executionmeal import models

@app.route('/500days')
@app.route('/')
def show_entries():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
