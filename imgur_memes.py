#!/usr/bin/python

import sqlite3
import requests
import os
import time
# import datetime
from flask import Flask, render_template, redirect, url_for, flash, g, jsonify

# config
CLIENT_ID = '636ac93d409f0d2'
SECRET_KEY = os.urandom(24)
DATABASE = 'memes.db'
PATH = 'static'

# create app
app = Flask(__name__)
app.config.from_object(__name__)


def download_imgur_image(img_link, is_thumb=False):
    """ Save on disk image downloaded from imgur or its thumbnail
        Args:
            img_link (str): link of the image to be downloaded
            img_id (bool): whether to get the original image or its thumbnail
        Returns:
            img_path (str): path to the image downloaded
    """
    # get filename with extension from link
    file_name = img_link[img_link.rfind('/') + 1:]

    # retreive img thumbnail from link
    if is_thumb:
        img_link = img_link[::-1].replace('.', '.b', 1)[::-1]
        file_name = file_name.replace('.', 'b.')

    # retreive img from link
    r = requests.get(img_link)
    img_path = '%s/%s' % (app.config['PATH'], file_name)

    # save img on disk
    with open(img_path, 'w') as img_file:
        for chunk in r.iter_content(1024):
            img_file.write(chunk)

    return img_path


@app.before_request
def before_request():
    """ Connect to sqlite db before each http request
    """
    g.db = sqlite3.connect(app.config['DATABASE'])

    # profiling execution time
    g.start = time.time()


@app.teardown_request
def teardown_request(exception):
    """ Disconnect from db when app is closed or exception
    """
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

    # profiling execution time
    diff = time.time() - g.start
    print 'Execution time %s' % diff


@app.route('/')
def top_memes():
    """ Home page
        Memes are retreived with ajax in get_memes()
    """
    return render_template('layout.html')


@app.route('/<page>')
def get_memes(page):
    """ Get ajax loaded json memes in given page
        Args:
            page (int): page to be retreived
    """
    # get memes from imgur api
    r = requests.get(
        'https://api.imgur.com/3/g/memes/top/%s' % page,
        headers={'Authorization': 'Client-ID %s' % app.config['CLIENT_ID']}
    )
    memes = r.json()['data'] if r.status_code == 200 else {}

    # send json data to sub-template
    content = render_template('memes.html', **{
        'memes': memes
    })

    # return ajax response
    return jsonify(
        content=content,
        nextPage=int(page) + 1
    )


@app.route('/save/<img_id>')
def save_meme(img_id):
    """ Save image by its imgur's id to disk & db
        Args:
            img_id(str): image id in imgur
    """
    # get image link from imgur api
    r = requests.get(
        'https://api.imgur.com/3/gallery/image/%s' % img_id,
        headers={'Authorization': 'Client-ID %s' % app.config['CLIENT_ID']}
    )

    if r.status_code == 200:
        img = r.json()['data']

        # save img & thumb to disk
        thumb_path = download_imgur_image(img['link'], True)
        img_path = download_imgur_image(img['link'])

        # save it to sqlite db
        g.db.execute(
            'insert into memes (id, title, path, thumb) values (?, ?, ?, ?)',
            [img['id'], img['title'], img_path, thumb_path]
        )
        g.db.commit()

        # show a flash msg
        flash('Image has been saved to %s' % img_path)

    return redirect(url_for('saved_memes'))


@app.route('/delete/<img_id>')
def delete_meme(img_id):
    # get image path & thumb from sqlite db
    cur = g.db.execute(
        'select id, title, path, thumb from memes where id = ?',
        [img_id]
    )
    img_id, img_title, img_path, img_thumb = cur.fetchone()

    # delete from disk
    os.remove(img_path)
    os.remove(img_thumb)

    # delete from sqlite db
    g.db.execute('delete from memes where id = ?', [img_id])
    g.db.commit()

    # show a flash msg
    flash('Image has been deleted')

    return redirect(url_for('saved_memes'))


@app.route('/favs')
def saved_memes():
    """ Get favourite memes saved on db & disk
        from folder /static
    """
    # get favorite memes from db
    cur = g.db.execute('select id, title, path, thumb from memes')
    fav_memes = [
        {'id': row[0], 'title': row[1], 'path': row[2], 'thumb': row[3]}
        for row in cur.fetchall()
    ]

    return render_template('memes.html', memes=fav_memes)


# run app
if __name__ == '__main__':
    app.run(debug=True)
