#!/usr/bin/python

import requests
import os
# import datetime
from flask import Flask, render_template, redirect, url_for, flash

# config
CLIENT_ID = '636ac93d409f0d2' 
SECRET_KEY = os.urandom(24)

# create app
app = Flask(__name__)
app.config.from_object(__name__)

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
    """ Save image by its imgur's id
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

        # retreive img from link & save it on disk
        r = requests.get(img['link'])
        with open('memes/%s' % img['id'], 'w') as img_file:
            for chunk in r.iter_content(1024):
                img_file.write(chunk)
        flash('Image has been saved to memes/%s' % img['id'])

    return redirect(url_for('saved_memes'))

@app.route('/favs')
def saved_memes():
    """ Get favourite memes saved on disk
        from folder /memes
    """
    favs_memes = ''
    # get meme image
    # r = requests.get()

    return render_template('memes.html', memes=favs_memes)

# run app
if __name__ == '__main__':
    app.run(debug=True)
