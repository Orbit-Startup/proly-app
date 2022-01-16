from flask import Flask, render_template, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_manager, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from predict import *




app = Flask(__name__)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

#Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Database
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

#Form Register
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)],
            render_kw={"placeholder":"username"})

    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)],
            render_kw={"placeholder":"password"})

    #submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()

        if existing_user_username:
            raise ValidationError(
                "Nama telah di gunakan.")

#Form Login
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)],
            render_kw={"placeholder":"username"})

    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)],
            render_kw={"placeholder":"password"})

    # submit = SubmitField("") #tulisan login "login.html"

#landing Page
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')
    
#Belum
@app.route('/belum', methods=['GET', 'POST'])
def belum():
    return render_template('belum.html')

#Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                #index di ganti jadi analisis
                return redirect(url_for('anggota'))
        
    return render_template('login.html', form=form)

#Register
@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

#Logout
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

#Analisis Login yang form input
@app.route('/anggota', methods=['GET', 'POST'])
@login_required
def anggota():
    return render_template('anggota.html')



#Analysis Login (Member) output
#Ada recomended
@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    #return render_template('analysis.html')

    url, category, ecommerce = [x for x in request.form.values()]

    if category == 'elektronik':
        path = 'data/train/electronic_data.csv'
    if category == 'makanan':
        path = 'data/train/food_data.csv'
    if category == 'pakaian':
        path = 'data/train/fashion_data.csv'
    
    if ecommerce == 'shopee':
        df = shopeeScraper(url)
    if ecommerce == 'tokopedia':
        df = tokopediaScraper(url)
        pass

    label_pos, label_neg, recommend = runApp(path, df)
    total_label = label_pos + label_neg 
    percent_pos = label_pos/total_label*100
    percent_neg = label_neg/total_label*100

    return render_template('member.html', url=url, category=category, ecommerce=ecommerce, percent_pos=percent_pos, percent_neg=percent_neg, recommend=recommend)
    

#Analysis Gak ada Recomended
@app.route('/member', methods=['GET', 'POST'])
def member():
    url, category, ecommerce = [x for x in request.form.values()]

    if category == 'elektronik':
        path = 'data/train/electronic_data.csv'
    if category == 'makanan':
        path = 'data/train/food_data.csv'
    if category == 'pakaian':
        path = 'data/train/fashion_data.csv'
    
    if ecommerce == 'shopee':
        df = shopeeScraper(url)
    if ecommerce == 'tokopedia':
        df = tokopediaScraper(url)
        pass

    label_pos, label_neg, recommend = runApp(path, df)
    total_label = label_pos + label_neg 
    percent_pos = label_pos/total_label*100
    percent_neg = label_neg/total_label*100

    return render_template('analysis.html', url=url, category=category, ecommerce=ecommerce, percent_pos=percent_pos, percent_neg=percent_neg)
    
if __name__ == "__main__":
    app.run(debug=True)

