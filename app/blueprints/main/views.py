from app.blueprints.main import main
from flask import request, jsonify, abort
import logging


@main.route('/login', methods=['POST'])
def login():
    pass


@main.route('/hello', methods=['GET'])
def hello():
    return "Hello!"