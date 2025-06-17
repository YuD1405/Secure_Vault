from flask import Blueprint, render_template, session, redirect

main_routes = Blueprint("main", __name__)


@main_routes.route("/")
def home():
    return "Welcome to Secure Vault"
