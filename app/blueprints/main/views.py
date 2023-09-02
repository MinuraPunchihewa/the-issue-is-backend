from app.blueprints.main import main
from flask import request, jsonify, abort
import logging


@main.route('/login', methods=['POST'])
def login():
    pass


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