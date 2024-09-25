from flask import request
from models.user import User
from extensions import db

def add_user_function():
    if request.method == "POST":
        name=request.form['name']
        email=request.form['email']
        password=request.form['password']
        user=User(
            name=name,
            email=email,
            password=password
        )
        
        user.save()
        data={
            'id':user.id,
            'name':user.name,
            'email':user.email,
            'password':user.password
        }
        return data
        
def edit_user_function(data):
    if request.method == "POST":
        data.name = request.form['name']
        data.email = request.form['email']
        data.password = request.form['password']
        
        db.session.commit()
        return data
    
def delete_user_function(user):
    db.session.delete(user)
    db.session.commit()
  
            