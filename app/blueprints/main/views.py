import logging
import mindsdb_sdk
from urllib.error import HTTPError
from app.blueprints.main import main
from flask import request, jsonify, abort


@main.route('/login', methods=['POST'])
def login():
    # if request is json, get data from json
    if request.is_json:
        request_data = request.get_json()
        login = request_data.get('login')
        password = request_data.get('password')

    # else get data from form
    else:
        login = request.form.get('login')
        password = request.form.get('password')

    # if login and password are not empty, try to connect
    if login and password:
        try:
            server = mindsdb_sdk.connect(login=login, password=password)
            return jsonify({'message': 'Login successful'}), 200
        except HTTPError as e:
            logging.error(e)
            return jsonify({'message': 'Login unsuccessful'}), 401

    # else return error
    else:
        return jsonify({'message': 'Either the login or password has not been provided'}), 400


@main.route('/databases', methods=['PUT'])
def create_database():
    pass


@main.route('/databases', methods=['GET'])
def get_databases():
    pass


@main.route('/models', methods=['PUT'])
def create_model():
    pass


@main.route('/issues', methods=['PUT'])
def create_issue():
    pass

@main.route('/issues/description', methods=['PUT'])
def generate_issue_description():
    pass