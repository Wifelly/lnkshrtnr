from flask import Flask, request, Response, redirect, jsonify
from passlib.hash import pbkdf2_sha256
from hash import getHash
from db_wrapper import request_db
import os
import json
import sqlite3


app = Flask(__name__)
db = request_db('db.db')
link_types = ('public', 'general', 'private')


@app.route('/api/short', methods=['POST'])
def shorten_link():
    data = request.json
    # print(data)
    if ('url' not in data) or ('type' not in data):
        return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')
    if data['type'] not in link_types:
        # шо за хуйню ты тут прислал? у нас три типа всего: 'public', 'general', 'private'
        data['type'] = 'public'
    try:
        last_id = db.request_insert_two('Urls', 'url, type', data['url'], data['type'])
        hashed = getHash(last_id[0][0])
        db.request_update('Urls', 'short_url', hashed, 'id', last_id[0][0])
    except sqlite3.IntegrityError:
        print('oops')
        shorten_link = db.request_select('short_url', 'Urls', 'url', data['url'])
        hashed = shorten_link[0][0]
    # Переделать под возврат кор. ссылки в джcоне jsonify
    return Response('{"short_url": "'+ str(hashed) + '"}', status=200, mimetype='application/json')

@app.route('/api/short/<string:short_url>', methods=['GET'])
def get_link(short_url):
    reqv = db.request_select('url, type, times_opened', 'Urls', 'short_url', short_url)
    print(reqv)
    if reqv[0][1] == 'public':
        times_opened = reqv[0][2] + 1
        db.request_update('Urls', 'times_opened', times_opened, 'short_url', short_url)
        return redirect(reqv[0][0], code=302)
    elif reqv[0][1] == 'general':
        # просим логин
        pass
    elif reqv[0][1] == 'private':
        # просим логин и если логин != создателю - шлем нахуй
        pass
    else:
        # сумасшедший? что это вообще за ссылка?
        return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')


@app.route('/api/short/delete/<string:short_url>', methods=['GET'])
def delete_link(short_url):
    db.request_delete('Urls', 'short_url', short_url)
    return Response('{"status": "OK"}', status=200, mimetype='application/json')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if 'login' not in data or 'password' not in data:
        return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')
    try:
        print(data['login'])
        print(data['password'])
        hash = pbkdf2_sha256.hash(data['password'])
        print(hash)
        # помещаем лог и пароль в бд
        db.request_insert_two('Users', 'login, password', data['login'], hash)
    except sqlite3.IntegrityError:
        # если лог уже в бд - шлем нахуй
        return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')
    # ну и наверн возвращаем токен
    # Знать бы как его генерить бы ещё
    return Response('{"status": "OK", "token": "token"}', status=200, mimetype='application/json')

@app.route('/api/lk/<string:username>', methods=['POST'])
def lk():
    data = request.json
    if 'username' not in data:
        return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')
    # Делаем запрос в бд левым джоином на все линки, созданные username
    reqv = None
    return Response(reqv, status=200, mimetype='application/json')