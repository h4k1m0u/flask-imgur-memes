#!/usr/bin/python

import sqlite3
import requests
import os
# import datetime
from flask import Flask, render_template, redirect, url_for, flash, g

# config
CLIENT_ID = 'imgur-app-clientid' 
SECRET_KEY = os.urandom(24)
DATABASE = 'memes.db'
PATH = 'static'

# create app
app = Flask(__name__)
app.config.from_object(__name__)

@app.before_request
def before_request():
    """ Connect to sqlite db before each http request
    """
    g.db = sqlite3.connect(app.config['DATABASE'])

@app.teardown_request
def teardown_request(exception):
    """ Disconnect from db when app is closed or exception
    """
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def top_memes():
    """ Home page to show first-page top memes 
        retreived from https://imgur.com/top
    """
    # get memes from imgur api
    r = requests.get('https://api.imgur.com/3/gallery/g/memes', headers={'Authorization':'Client-ID %s' % app.config['CLIENT_ID']})
    memes = r.json()['data'] if r.status_code == 200 else {}
    return render_template('memes.html', memes=memes)

@app.route('/save/<img_id>')
def save_meme(img_id):
    """ Save image by its imgur's id to disk & db
        Args:
            img_id(str): image id in imgur
    """
    # get image link from imgur api
    r = requests.get(
        'https://api.imgur.com/3/gallery/image/%s' % img_id,
        headers={'Authorization':'Client-ID %s' % app.config['CLIENT_ID']}
    )

    if r.status_code == 200:
        img = r.json()['data']

        # retreive img from link
        r = requests.get(img['link'])
        img_path = '%s/%s' % (app.config['PATH'], img['id'])

        #  save it on disk
        with open(img_path, 'w') as img_file:
            for chunk in r.iter_content(1024):
                img_file.write(chunk)

        # save it to sqlite db
        g.db.execute(
            'insert into memes (id, title, path) values (?, ?, ?)',
            [img['id'], img['title'], img_path]
        )
        g.db.commit()

        flash('Image has been saved to %s' % img_path)

    return redirect(url_for('saved_memes'))

@app.route('/favs')
def saved_memes():
    """ Get favourite memes saved on db & disk
        from folder /static
    """
    # get favorite memes from db
    cur = g.db.execute('select id, title from memes')
    fav_memes = [{'id':row[0], 'link':row[1]} for row in cur.fetchall()]

    return render_template('memes.html', memes=fav_memes)

# run app
if __name__ == '__main__':
    app.run(debug=True)
