from flask import Flask , jsonify , request , session ,redirect
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
import os
import json
import datetime
from flask_http_middleware import BaseHTTPMiddleware
from flask_bcrypt import Bcrypt
import re 
import jwt
from flask_login import LoginManager, login_required, logout_user, login_user

#initiliaze app

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
login_manager = LoginManager()
bcrypt = Bcrypt(app)


# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'counterCount'
# Initialize db
db = SQLAlchemy(app)

# Initialize ma
ma = Marshmallow(app)

"""Categorey"""

#Categorey Model
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100) , unique = True)
    books = db.relationship('Book', backref='category', lazy=True)
    def __init__(self,name):
        self.name = name

# Category Schema
class CategorySchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'books')

# Init schema
category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)

"""USER"""
#User Model

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100) , unique = True)
    email = db.Column(db.String(100) , unique = True)
    password = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_on = db.Column(db.DateTime, nullable=False, default= datetime.datetime.now)
    orders = db.relationship('Order', backref='user', lazy=True)    
    def __init__(self, name , email, password, is_admin = False ):
        self.name= name
        self.email = email
        self.password = password
        self.is_admin  = is_admin


# User Schema
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'email' , 'password' , 'is_admin', 'created_on' )

# Init USer schema
user_schema = UserSchema()
users_schema = UserSchema(many=True)


# Association Table for Many-to-Many Relationship
cart_book_association = db.Table('cart_book_association',
                                    db.Column('cart_id', db.Integer, db.ForeignKey('cart.id'), primary_key=True),
                                    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True)
                                    )



"""BOOKS"""

#Book Model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100),  nullable = False , unique = True)
    year = db.Column(db.Integer )
    no_pages = db.Column(db.Integer )
    ISBN = db.Column(db.String(100) , nullable = False , unique = True)
    language = db.Column(db.String(100) ,nullable = False )
    created_on = db.Column('Created On', db.DateTime, default= datetime.datetime.now)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    price = db.Column(db.Integer )
    quantity = db.Column(db.Integer )
    def __init__(self, title, year, no_pages , ISBN ,language, price,quantity,category_id):
        self.title = title
        self.year = year
        self.no_pages = no_pages
        self.ISBN = ISBN
        self.language = language
        self.price= price
        self.quantity = quantity
        self.category_id = category_id

# Book Schema
class BookSchema(ma.Schema):
    class Meta:
        fields = ('id', 'title', 'year' , 'no_pages' , 'ISBN', 'language','price','quantity','category_id' )

# Init Book schema
book_schema = BookSchema()
books_schema = BookSchema(many=True)


"""CART"""
#Cart Model
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_price = db.Column(db.Integer, default=0)
    total_quantity = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref=db.backref("user", uselist=False))
    items = db.relationship('Book', secondary=cart_book_association,
                            backref=db.backref('carts', lazy='dynamic'))
    created_on = db.Column('Created On', db.DateTime, default= datetime.datetime.now)
    def __init__(self,user_id, total_price ,total_quantity):
        self.user_id=user_id
        self.total_price = total_price
        self.total_quantity = total_quantity
        self.items=[]


# Cart Schema
class CartSchema(ma.Schema):
    class Meta:
        fields = ('id', 'total_price', 'total_quantity' , 'user_id' , 'created_on' )

# Init Cart schema
cart_schema = CartSchema()
carts_schema = CartSchema(many=True)

"""Order Model"""
class Order(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cart_id  = db.relationship(Cart, backref=db.backref('order', uselist=False))
    final_price=db.Column(db.Integer,nullable = False)
    status = db.Column(db.String(100), nullable = False ,default = "In Progress")
    created_on = db.Column('Created On', db.DateTime, default= datetime.datetime.now)
    def __init__(self,user_id, cart_id  ):
        self.user_id=user_id
        self.cart_id = cart_id

# Cart Schema
class OrderSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user_id', 'cart_id' ,'final_price', 'status' , 'created_on' )

# Init Cart schema
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

with app.app_context():
    db.create_all()

'''HOME PAGE'''
@app.route("/")
def home():
    return jsonify({"welcome": "Welcome To Our Book Shop"})


'''USER ROUTING!'''
#registaretion for a user

@app.route("/register", methods = ['POST'])
def register():
    name = request.json['name']
    email= request.json['email']
    password = request.json['password']
    confirm_password = request.json['confirm_password']
    #validate email address
    if  not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        message = {
            "msg":"Invalid email address !"
        }
        return jsonify(message)

    #validate passowrds
    if password != confirm_password :
        message = {
            "msg":"Passwords Does not match"
        }
        return jsonify(message)
    else:
        #hashed_password  = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        hashed_password  = bcrypt.generate_password_hash(password)
        try:
            user = User(name, email, hashed_password )
            db.session.add(user)
            db.session.commit()
            session['logged_User'] = True
            session['logged_User_id'] = user.id
            print(session.get['logged_User_id'])
            return user_schema.jsonify(user)
        except:
            message = {
            "msg":"Failed to add user"
        }
        return jsonify(message)

#register admin
@app.route("/registeradmin", methods = ['POST'])
def register_admin():
    name = request.json['name']
    email= request.json['email']
    password = request.json['password']
    confirm_password = request.json['confirm_password']
    admin_confrim = request.json['admin_confrim']
    if admin_confrim == "0000":
        admin = True
        #validate email address
        if  not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = {
                "msg":"Invalid email address !"
            }
            return jsonify(message)
        #validate passowrds
        if password != confirm_password :
            message = {
                "msg":"Passwords Does not match"
            }
            return jsonify(message)
        else:
            #hashed_password  = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            hashed_password  = bcrypt.generate_password_hash(password)
            user = User(name, email, hashed_password , is_admin=admin)
            db.session.add(user)
            db.session.commit()
            session['logged_User'] = True
            session['logged_User_id'] = user.id
            return user_schema.jsonify(user)

#Login user 
@app.route("/login" , methods = ['POST'])
def login():
    email= request.json['email']
    password = request.json['password']
    if not email or not password:
        return jsonify({"msg:" "Invalid Email or Password !"})
    user = User.query.filter_by(email = email).first()
    if user and bcrypt.check_password_hash(user.password , password):
        session['logged_User_id'] = user.id
        if user.is_admin == True :
            session['logged_Admin'] = True
        else:
            session['logged_User'] = True
            session['logged_Admin'] = False
        return user_schema.jsonify(user)
    else:
        return jsonify({"msg:" "Invalid Email or Password !"})
    
#logout
@app.route("/logout" , methods = ["Get"])
def logout():
    if session.get('logged_User') is True or session.get('logged_Admin'):
        session['logged_User'] = False
        session['logged_Admin'] = False
    if session.get('logged_User_id'):
        session.pop("'logged_User_id'")
    return redirect("/")


"""BOOKS ROUTES"""

# Create a Book
@app.route('/book', methods=['POST'])
def add_book():
    if session.get('logged_Admin') is not False :
        title = request.json['title']
        year = request.json['year']
        no_pages = request.json['no_pages']
        category_id = request.json['category_id']
        ISBN = request.json['ISBN']
        language = request.json['language']
        price= request.json['price']
        quantity= request.json['quantity']
        new_book = Book(title, year, no_pages, ISBN , language ,price, quantity, category_id)
        db.session.add(new_book)
        db.session.commit()
        return book_schema.jsonify(new_book)
    else:
        return jsonify({"msg:" :"You Are Not Allowed To Add / Delete Or Update any Book!"})

#Get all books
@app.route('/book' , methods = ['GET'])
def get_book():
    all_books = Book.query.all()
    return jsonify(books_schema.dump(all_books))

#Delete a Book

@app.route('/book/delete/<id>', methods=['POST'])
def delete_book(id):
    if session.get('logged_Admin') is True :
        book = Book.query.filter_by(id = id).first()
        db.session.delete(book)
        return jsonify({"msg": "Book Deleted succesfully "})
    else:
        return jsonify({"msg" : "Something went wrong please try again!"})

#update a Book

@app.route("/book/<id>", methods = ["PUT"])
def update_book(id):
    if session.get('logged_Admin') is True :
        book = Book.query.filter_by(id = id).first()
        book.title = request.json('title')
        book.price = request.json('price')
        book.quantity = request.json('quantity')
        db.session.commit()
        return book_schema.jsonify(book) 
    else:
        return jsonify({"msg:" :"You Are Not Allowed To Add / Delete Or Update any Book!"})
        

'''Categorey Routes'''
# Create a Categorey
@app.route('/categorey', methods=['POST'])
def add_categorey():
    if session.get('logged_Admin') is True :
        name = request.json['name']
        print(name)
        new_categorey = Category(name)
        db.session.add(new_categorey)
        db.session.commit()
        return category_schema.jsonify(new_categorey)
    else:
        return jsonify({"msg": "something went wrong try again"})

#Get all Categories
@app.route('/categorey' , methods = ['GET'])
def get_categories():
    all_categories = Category.query.all()
    return jsonify(categories_schema.dump(all_categories))

#get all books in categorey id
@app.route('/books/categorey/<id>', methods=['GET'])
def get_books_in_categorey(id):
    books_by_category = Book.query.filter_by(category_id = id ).all()
    return(jsonify(books_schema.dump(books_by_category)))

#delete categorey
@app.route('/categorey/<id>', methods=['POST'])
def delete_categorey(id):
    if session.get('logged_Admin') is True :
        cat = Category.query.filter_by(id = id).first()
        db.session.delete(cat)
        return jsonify({"msg": "Categorey Deleted succesfully "})

'''Cart Routes'''
@app.route('/cart', methods=['POST'])
def new_cart():
    if session.get('logged_User') is True :
        book_id = request.json['book_id']
        quantity = request.json['quantity']
        user_id = session.get('logged_User_id')
        book = Book.query.filter_by(id = book_id ).first()
        user = User.query.filter_by(id = user_id).first()
        total_price = book.price * quantity
        new_cart = Cart( user.id  , total_price, quantity)
        db.session.add(new_cart)
        db.session.commit()
        session['cart_id'] =  new_cart.id
        new_cart.items.append(book)
        db.session.commit()
        return cart_schema.jsonify(new_cart.items)
    
#update Cart
@app.route('/cart/add', methods=['POST'])
def update_cart():
    if session.get('logged_User') is True and session.get('cart_id') :
        book_id = request.json['book_id']
        quantity = request.json['quantity']
        book = Book.query.filter_by(id = book_id ).first()
        price = book.price * quantity
        updated_cart = Cart.query.filter_by(id = session.get('cart_id')).first()
        update_quantity =  updated_cart.total_quantity + quantity
        updated_price = updated_cart.total_price + price
        updated_cart.total_price = updated_price
        updated_cart.total_quantity = update_quantity
        updated_cart.items.append(book)
        db.session.commit()
        return cart_schema.jsonify(updated_cart)
    
#get all books in the cart
@app.route('/cart/<id>', methods=['GET'])
def books_in_cart(id):
    if session.get('logged_User') is True :
        cart = Cart.query.filter_by(id = id).first()
        cart_items=[]
        for book in cart.items:
            cart_items.append({"Book": book.title, "price" : book.price})
        return jsonify({"yourCart items": cart_items})

#Cancel cart
@app.route('/cart/<id>', methods=['POST'])
def cancel_cart(id):
    if session.get('logged_User') is True :
        cart = Cart.query.filter_by(id = id).first()
        db.session.delete(cart)
        return jsonify({"msg": "Cart Cnaceled succesfully "})

#Submit Order
@app.route('/order', methods=['POST'])
def submit_order():
    if session.get('logged_User') is True and session.get('cart_id'):
        cart = Cart.query.filter_by(id = session.get('cart_id')).first()
        user = User.query.filter_by(id =session.get('logged_User_id') ).first()
        cart_id = cart.id
        user_id = user.id
        final_price = cart.total_price
        order= Order(user_id=user_id, cart_id=cart_id ,final_price = final_price )
        db.session.add(order)
        db.session.commit()
        return order_schema.jsonify(order)
    

#update status
@app.route('/update/order/<id>', methods=['POST'])
def status_update():
    if session.get('logged_Admin') is True :
        status = request.json(['status'])
        order = Order.query.filter_by(id = session.get('cart_id')).first()
        order.status= status
        db.session.commit()
        return order_schema.jsonify(order)
    else:
        return jsonify({"msg": "something went wrong try again"})
    