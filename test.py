from flask import Flask, request, Response, redirect, jsonify
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)

app = Flask(__name__)
jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = 'super-secret'
@app.route('/auth', methods=['POST'])
def token():
    data = request.json
    login = data['login']
    access_token = create_access_token(identity=login)
    return jsonify(access_token=access_token), 200
@app.route('/tk', methods=['GET'])
@jwt_required
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    print(current_user)
    return jsonify(logged_in_as=current_user), 200

if __name__ == '__main__':
    app.run()