from app.main import main
from flask import request, jsonify, abort
import logging


@main.route('/login', methods=['POST'])
def login():
    pass


@main.route('/hello', methods=['POST'])
def hello():
    return "Hello!"