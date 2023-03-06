from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:0G8dv0W85glXRCRujzvy@containers-us-west-117.railway.app:6142/railway'
db = SQLAlchemy(app)
x = app.app_context()
x.push()
bcrypt = Bcrypt(app)
loginmanager=LoginManager(app)
loginmanager.login_view = 'login'
loginmanager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jayantparakh694@gmail.com'
app.config['MAIL_PASSWORD'] = 'rare2304'
mail = Mail(app)

from flaskblog import routes
# x.pop()
