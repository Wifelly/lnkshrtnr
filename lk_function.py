import json
import sqlite3

from flask import Flask, request, Response, redirect, jsonify
from validators import url as validate_url

from db_wrapper import request_db
from hash import getHash
from validate import validate_access

db = request_db('db.db')
url_types = ('public', 'general', 'private')


def get_lk(login):
    '''return url list of user'''
    reqv = db.request_select('id ,url, short_url, times_opened, custom_short_url, url_type', 'Urls', 'user_id', login)
    response = []
    for item in reqv:
        response.append(
            {
                'id': reqv[len(response)-1][0],
                'url': reqv[len(response)-1][1],
                'short_url': reqv[len(response)-1][2],
                'times_opened': reqv[len(response)-1][3],
                'custom_short_url': reqv[len(response)-1][4],
                'url_type': reqv[len(response)-1][5]
            }
        )
    return jsonify(response), 200


def add_link(url, url_type, login, custom_short_url=None):
    ''' adds link in database'''
    if url_type not in url_types:
        url_type = 'public'
    if url[:4] != 'http':
        url = 'http://' + url
    if not validate_url(url):
        return jsonify({"msg": "Bad url"}), 400
    try:
        last_id = db.request_insert_three('Urls', 'url, url_type, user_id', url, url_type, login)
        hashed = getHash(last_id[0][0])
        db.request_update('Urls', 'short_url', hashed, 'id', last_id[0][0])
        if custom_short_url is not None:
            db.request_update('Urls', 'custom_short_url', custom_short_url, 'id', last_id[0][0])
    except sqlite3.IntegrityError:
        custom_short_url = None
    # Переделать под возврат кор. ссылки в джcоне jsonify
    return jsonify(short_url=hashed, custom_short_url=custom_short_url), 200


def set_custom_short_url(custom_short_url, short_url, login):
    if not validate_access(login, 'short_url', short_url):
        return jsonify({"msg": "Acces denied"}), 403
    try:
        db.request_update('Urls', 'custom_short_url', custom_short_url, 'short_url', short_url)
    except sqlite3.IntegrityError:
        return jsonify({"msg": "Bad request"}), 400
    return jsonify({"status": "OK"}), 200


def change_url_type(short_url, url_type, login):
    if not validate_access(login, 'short_url', short_url):
        return jsonify({"msg": "Acces denied"}), 403
    if url_type not in url_types:
        return jsonify({"msg": "Bad request"}), 400
    db.request_update('Urls', 'url_type', url_type, 'short_url', short_url)
    return jsonify({"status": "OK"}), 200


def delete_url(short_url, login):
    if not validate_access(login, 'short_url', short_url):
        return jsonify({"msg": "Acces denied"}), v
    db.request_delete('Urls', 'short_url', short_url)
    return jsonify({"status": "OK"}), 200


def delete_custom_short_url(custom_short_url, login):
    if not validate_access(login, 'custom_short_url', custom_short_url):
        return jsonify({"msg": "Acces denied"}), 403
    db.request_update('Urls', 'custom_short_url', 'NULL', 'custom_short_url', custom_short_url)
    return jsonify({"status": "OK"}), 200
