from flask import Flask, request, Response, redirect, jsonify
from passlib.hash import pbkdf2_sha256
from hash import getHash
from db_wrapper import request_db
import os
import json
import sqlite3
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
from flask_httpauth import HTTPBasicAuth
from validators import url as validate_url

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = '2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b'
db = request_db('db.db')
link_types = ('public', 'general', 'private')
jwt = JWTManager(app)
auth_basic = HTTPBasicAuth()


@auth_basic.verify_password
def validate_user(login, password):
    '''Validate password'''
    hash_pass = db.request_select('password', 'Users', 'login', login)
    if hash_pass != []:
        return pbkdf2_sha256.verify(password, hash_pass[0][0])
    else:
        return False


def get_lk(login):
    '''return url list of user'''
    response = db.request_select('url, short_url, times_opened, custom_short_url', 'Urls', 'user_id', login)
    return json.dumps(response)


def add_link(url, url_type, login, custom_short_url = None):
    ''' adds link in database'''
    if url_type not in link_types:
        url_type = 'public'
    if url[:4] != 'http':
        url = 'http//' + url
    if not validate_url(url):
        return jsonify({"msg": "Bad url"}), 400
    try:
        last_id = db.request_insert_three('Urls', 'url, url_type, user_id', url, url_type, login)
        hashed = getHash(last_id[0][0])
        if custom_short_url is not None:
            db.request_update('Urls', 'custom_short_url', custom_short_url, 'id', last_id[0][0])
        db.request_update('Urls', 'short_url', hashed, 'id', last_id[0][0])
    except Exception as e:
        print(e)
    # except sqlite3.IntegrityError:
    #     print('oops')
    #     shorten_link = db.request_select('short_url', 'Urls', 'url', data['url'])
    #     hashed = shorten_link[0][0]
    # Переделать под возврат кор. ссылки в джcоне jsonify
    return Response('{"short_url": "'+ str(hashed) + '", "custom_short_urs": "' + str(custom_short_url) + '"}', status=200, mimetype='application/json')


def set_custom_short_url(custom_short_url, short_url):
    try:
        db.request_update('Urls', 'custom_short_url', custom_short_url, 'short_url', short_url)
    except Exception as e:
        print(e)
    return Response('{"status": "OK"}', status=200, mimetype='application/json')


def change_url_type(short_url, url_type):
    db.request_update('Urls', 'url_type', url_type, 'short_url', short_url)
    return Response('{"status": "OK"}', status=200, mimetype='application/json')


def delete_url(short_url):
    db.request_delete('Urls', 'short_url', short_url)
    return Response('{"status": "OK"}', status=200, mimetype='application/json')


def delete_custom_short_url(custom_short_url):
    db.request_update('Urls', 'custom_short_url', 'NULL', 'custom_short_url', custom_short_url)
    return Response('{"status": "OK"}', status=200, mimetype='application/json')


@app.route('/api/auth', methods=['POST'])
def authorise():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    data = request.json
    if 'login' not in data:
        return jsonify({"msg": "Missing login parameter"}), 400
    if 'password' not in data:
        return jsonify({"msg": "Missing password parameter"}), 400
    login = data['login']
    password = data['password']
    try:
        hash = pbkdf2_sha256.hash(password)
        db.request_insert_two('Users', 'login, password', login, hash)
    except sqlite3.IntegrityError:
        if not validate_user(login, password):
            return jsonify({"msg": "Bad login or password"}), 401
    access_token = create_access_token(identity=login)
    return jsonify(access_token=access_token), 200


@app.route('/<string:short_url>', methods=['GET'])
def get_link(short_url):
    reqv = db.request_select('url, url_type, times_opened, user_id', 'Urls', 'short_url', short_url)
    print(reqv)
    if reqv == []:
        reqv = db.request_select('url, url_type, times_opened, short_url, user_id', 'Urls', 'custom_short_url', short_url)
        short_url = reqv[0][3]
    if reqv[0][1] == 'public':
        times_opened = reqv[0][2] + 1
        db.request_update('Urls', 'times_opened', times_opened, 'short_url', short_url)
        return redirect(reqv[0][0], code=302)
    elif (reqv[0][1] == 'general') or (reqv[0][1] == 'private'):
        return redirect('/secure/' + short_url, code=302)
    else:
        # сумасшедший? что это вообще за ссылка?
        return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')



@app.route('/secure/<string:short_url>', methods=['GET'])
@auth_basic.login_required
def general(short_url):
    reqv = db.request_select('url, url_type, times_opened, user_id', 'Urls', 'short_url', short_url)
    print(reqv)
    if reqv == []:
        reqv = db.request_select('url, url_type, times_opened, short_url, user_id', 'Urls', 'custom_short_url', short_url)
        short_url = reqv[0][3]
    if (reqv[0][1] == 'general'):
        times_opened = reqv[0][2] + 1
        db.request_update('Urls', 'times_opened', times_opened, 'short_url', short_url)
        return redirect(reqv[0][0], code=302)
    elif (reqv[0][1] == 'private') and (auth_basic.username == reqv[0][4]):
        times_opened = reqv[0][2] + 1
        db.request_update('Urls', 'times_opened', times_opened, 'short_url', short_url)
        return redirect(reqv[0][0], code=302)



@app.route('/api/lk', methods=['GET', 'POST', 'PATCH', 'DELETE'])
@jwt_required
def lk():
    login = get_jwt_identity()
    # if not request.is_json:
    #     return jsonify({"msg": "Missing JSON in request"}), 400
    data = request.json
    if request.method == 'GET':
        # получение всех ссылок юзера
        response = get_lk(login)
    elif request.method == 'POST':
        # добавление ссылки
        if 'url' not in data or 'url_type' not in data:
            return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')
        url = data['url']
        url_type = data['url_type']
        if 'custom_short_url' not in data:
            response = add_link(url, url_type, login)
        else:
            custom_short_url = data['custom_short_url']
            response = add_link(url, url_type, login, custom_short_url)
    elif request.method == 'PATCH':
        if 'custom_short_url' in data: # изменение ссылки
            custom_short_url = data['custom_short_url']
            short_url = data['short_url']
            response = set_custom_short_url(custom_short_url, short_url)
        elif ('short_url' in data) and ('url_type' in data): # изменение типа ссылки
            url_type = data['url_type']
            short_url = data['short_url']
            response = change_url_type(short_url, url_type)
    elif request.method == 'DELETE':
        if 'short_url' in data: # удаление ссылки
            short_url = data['short_url']
            response = delete_url(short_url)
        elif 'custom_short_url' in data: # удаление кастом ссылки
            custom_short_url = data['custom_short_url']
            response = delete_custom_short_url(custom_short_url)
        else:
            return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')
    return response

