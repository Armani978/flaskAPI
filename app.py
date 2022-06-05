from flask import Flask, make_response, request, g, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_httpauth import HttpBasicAuth, HTTPTokenAuth
from flask_cors import CORS
import os
import secrets
from werkzeug.security import generate_password_hash, check_password_hash



class Config():
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
basic_auth = HttpBasicAuth()
token_auth = HttpTokenAuth()
cors = CORS(app)

@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return False
    g.current_user = user
    return True

def verify_token(token):
    user = User.query.filter_by(token=token).first()
    if not user:
        return False
    g.current_user = user
    return True

class User(db.Model):
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)
    user_id = db.Column(db.Integer)
    token= db.Colummn(db.String)
    
    def get_token(self):
        self.token = secrets.token_urlsafe(16)
        self.save()
        return self.token
    
    @staticmethod
    def checkToken(token):
        user = User.query.filter_by(token=token).first()
        if user:
            return user
        if not user:
            return None
        
    def hash_password(self , og_password):
        self.password = generate_password_hash(og_password)
        return self.password

    def check_password_hash(self, login_password):
        return check_password_hash(self.password, login_password)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f'<{self.user_id}|{self.email}>'

    def from_db(self, data):
        for field in ["email", "password", "first_name", "last_name"]:
            if field in data and field == "password":
                setattr(self, field, data.get(field))

    def register(self, data):
        self.email = data['email']
        self.password = self.hash_password(data['password'])
        self.first_name = data['first_name']
        self.last_name = data['last_name']

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "email": self.email,
            "first_name":self.first_name,
            "last_name":self.last_name,
            "token":self.token
            }

class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    author = db.Column(db.String)
    genre = db.Column(db.String)
    img = db.Column(db.String)
    year = db.Column(db.Integer)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f'<{self.book_id}|{self.title}>'

    def from_db(self, data):
        for field in ["title", "author", "genre", "img", "year"]:
            if field in data:
                setattr(self, field, data.get(field))

    def to_db(self):
        return{

            'title' : self.title,
            'author' : self.author,
            'genre' : self.genre,
            'img': self.img,
            'year' : self.year

        }

@app.get('/login')
@basic_auth.login_required()
def login():
    g.current_user.get_token()
    return make_response(g.current_user.to_dict(), 200)


@app.post('/user')
def post_user():
    data = request.get_json
    user = User()
    user.register(data)
    user.save()
    return make_response(user.to_dict(), 200)

@app.put('/user')
@token_auth.login_required
def putUSer():
    data = request.get_json()
    user = g.current_user
    user.from_db(data)
    user.save()
    return make_response(user.to_dict(), 200)


@app.delete('/user')
@token_auth.login_required
def deleteUser():
    user = g.current_user
    user.delete()
    return make_response(user.to_dict(), 200)


@app.get('/book')
def get_books():
    books = Book.query.all()
    return make_response([book.to_dict() for book in books], 200)

@app.get('/book')
def get_book(book_id):
    book = Book.query.filter_by(book_id=book_id).first()
    if not book:
        return make_response({"message": "Book not found"}, 404)
    return make_response(book.to_dict(), 200)

@app.post('/book')
@token_auth.login_required
def post_book():
    data = request.get_json()
    book = Book()
    book.from_db(data)
    book.save()
    return make_response(book.to_dict(), 200)

@app.post('/book')
@token_auth.login_required
def put_book():
    data = request.get_json()
    book = g.current_book
    book.from_db(data)
    book.save()
    return make_response(book.to_dict(), 200)

@app.delete('/book')
@token_auth.login_required
def delete_book():
    book = g.current_book
    book.delete()
    return make_response(book.to_dict(), 200)


if __name__=="__main__":
    app.run(debug=True) 