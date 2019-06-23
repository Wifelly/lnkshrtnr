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

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret'
db = request_db('db.db')
link_types = ('public', 'general', 'private')
jwt = JWTManager(app)
auth_basic = HTTPBasicAuth()

@auth_basic.verify_password
def validate_user(login, password):
    hash_pass = db.request_select('password', 'Users', 'login', login)
    if hash_pass != []:
        return pbkdf2_sha256.verify(password, hash_pass[0][0])
    else:
        return False


def get_lk(data):
    if 'login' not in data:
        return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')
    login = data['login']
    # Делаем запрос в бд левым джоином на все линки, созданные username
    response = db.request_select('url, short_url, times_opened', 'Urls', 'user_id', login)
    print(json.dumps(response))
    return json.dumps(response)


def add_link(data):
    if ('url' not in data) or ('url_type' not in data) or ('login' not in data):
        return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')
    url = data['url']
    url_type = data['url_type']
    login = data['login']
    if data['url_type'] not in link_types:
        # шо за хуйню ты тут прислал? у нас три типа всего: 'public', 'general', 'private'
        url_type = 'public'
    try:
        last_id = db.request_insert_three('Urls', 'url, url_type, user_id', url, url_type, login)
        hashed = getHash(last_id[0][0])
        db.request_update('Urls', 'short_url', hashed, 'id', last_id[0][0])
    except Exception as e:
        print(e)
    # except sqlite3.IntegrityError:
    #     print('oops')
    #     shorten_link = db.request_select('short_url', 'Urls', 'url', data['url'])
    #     hashed = shorten_link[0][0]
    # Переделать под возврат кор. ссылки в джcоне jsonify
    return Response('{"short_url": "'+ str(hashed) + '"}', status=200, mimetype='application/json')


def set_custom_short_url(data):
    if 'custom_short_url' not in data or 'short_url' not in data:
        return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')
    custom_short_url = data['custom_short_url']
    short_url = data['short_url']
    try:
        db.request_update('Urls', 'custom_short_url', custom_short_url, 'short_url', short_url)
    except Exception as e:
        print(e)
    return Response('{"status": "OK"}', status=200, mimetype='application/json')


def change_url_type(data):
    short_url = data['short_url']
    url_type = data['url_type']
    db.request_update('Urls', 'url_type', url_type, 'short_url', short_url)
    return Response('{"status": "OK"}', status=200, mimetype='application/json')


def delete_url(data):
    short_url = data['short_url']
    db.request_delete('Urls', 'short_url', short_url)
    return Response('{"status": "OK"}', status=200, mimetype='application/json')


def delete_custom_short_url(data):
    custom_short_url = data['custom_short_url']
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
        # помещаем лог и пароль в бд
        db.request_insert_two('Users', 'login, password', login, hash)
    except sqlite3.IntegrityError:
        print("ujdkfjdlfjd")
        # если лог уже в бд - значит юзер уже зареган 
        # чекаем пароль на валидность и даем токен
        

        if not validate_user(login, password):
            return jsonify({"msg": "Bad login or password"}), 401

        # Identity can be any data that is json serializable
    access_token = create_access_token(identity=login)
    return jsonify(access_token=access_token), 200
    # ну и наверн возвращаем токен
    # Знать бы как его генерить бы ещё


@app.route('/short/<string:short_url>', methods=['GET'])
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
    elif reqv[0][1] == 'general':
        return redirect('/general/' + short_url, code=302)
    elif reqv[0][1] == 'private':
        return redirect('/private/' + short_url, code=302)
    else:
        # сумасшедший? что это вообще за ссылка?
        return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')



@app.route('/general/<string:short_url>', methods=['GET'])
@auth_basic.login_required
def general(short_url):
    return "Hello"


@app.route('/private/<string:short_url>', methods=['GET'])
@auth_basic.login_required
def private(short_url):
    return "Hello"



@app.route('/api/lk', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def lk():
    if request.method == 'GET':
        # получение всех ссылок юзера
        response = get_lk(request.json)
        return response
    elif request.method == 'POST':
        # добавление ссылки
        response = add_link(request.json)
        return response
    elif request.method == 'PATCH':
        data = request.json
        if 'custom_short_url' in data: # изменение ссылки
            response = set_custom_short_url(data)
        elif ('short_url' in data) and ('url_type' in data):
            response = change_url_type(data)
        return response
    elif request.method == 'DELETE':
        data = request.json
        if 'url' in data: # удаление ссылки
            response = delete_url(data)
        elif 'custom_short_url' in data: # удаление кастом ссылки
            response = delete_custom_short_url(data)
        else:
            return Response('{"status": "error", "error": "Bad request"}', status=400, mimetype='application/json')
        return response
if __name__ == '__main__':
    app.run()


