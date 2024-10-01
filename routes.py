from flask import Blueprint, redirect, url_for
from controllers.auth import auth  
from controllers.admin import admin
from controllers.document import document
from controllers.user import user

main = Blueprint('main', __name__)



@main.route('/')
def index():
    return redirect(url_for('auth.login'))  

def register_routes(app):
    app.register_blueprint(auth, url_prefix='/auth')        
    app.register_blueprint(admin, url_prefix='/admin')      
    app.register_blueprint(document, url_prefix='/documents') 
    app.register_blueprint(user, url_prefix='/user')        
    app.register_blueprint(main)

