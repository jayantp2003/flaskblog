from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app,db,bcrypt,mail
from flaskblog.form import RegistrationForm, LoginForm, UpdateForm, PostCreationForm, RequestResetForm,ResetPassword
from flaskblog.models import User,Post
import secrets,os
from flask_login import login_user,current_user,logout_user,login_required
from PIL import Image
from flask_mail import Message

@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page',1,type=int)
    sort_by = request.args.get('sort_by','desc',type=str)
    if(sort_by=='asc'):
        posts= Post.query.order_by(Post.date_posted).paginate(page = page, per_page=2)
    else:
        posts= Post.query.order_by(Post.date_posted.desc()).paginate(page = page, per_page=2) 
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    # if current_user.is_authenticated:
    #     return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed= bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data , email = form.email.data, password = hashed )
        db.session.add(user)
        db.session.commit()
        flash('Your account is successfully created you can now login')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    # if current_user.is_authenticated:
    #     return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            flash('You have been logged in!', 'success')
            login_user(user,remember = form.remember.data)
            nextpage = request.args.get('next')
            return redirect(nextpage) if nextpage else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out!', 'success')
    return redirect(url_for('home'))

def save_pic(form_pic):
    rand = secrets.token_hex(8)
    _,file_ext = os.path.splitext(form_pic.filename)
    picfn = rand+file_ext
    picpath = os.path.join(app.root_path,'static/profile_pics',picfn)
    outputs=(125,125)
    i = Image.open(form_pic)
    i.thumbnail(outputs)
    i.save(picpath)
    return picfn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateForm()
    if form.validate_on_submit():
        if form.imgfile.data:
            pic_file = save_pic(form.imgfile.data)
            current_user.image_file = pic_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account details has been updated",'success')
        return redirect(url_for('account'))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    imgfile = url_for('static',filename = 'profile_pics/'+current_user.image_file)
    return render_template('account.html', title='Account',image_file = imgfile,form =form)


@app.route("/create", methods=['GET', 'POST'])
@login_required
def create():
    form = PostCreationForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,content=form.content.data,author = current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your Content has been posted!!",'success')
        return redirect(url_for('home'))
    return render_template('create.html',title = "Post Creation",form=form, legend = "New Post")

@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
# @login_required
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post.html",title = post.title,post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update(post_id):
    post = Post.query.get_or_404(post_id)
    if(post.author!=current_user):
        abort(403)
    form = PostCreationForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Your Content has been updated!!",'success')
        return redirect(url_for('home'))
    elif request.method == "GET":
        form.title.data = post.title
        form.content.data =post.content
    return render_template('create.html',title = "Update post",form=form, legend = "Update Post")

@app.route("/post/<int:post_id>/delete", methods=['GET', 'POST'])
@login_required
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    if(post.author!=current_user):
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted ",'success')
    return redirect(url_for('home'))

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                    sender='noreply@demo.com',
                    recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
    {url_for('reset', token=token, _external=True)}
    If you did not make this request then simply ignore this email and no changes will be made.
    '''
    mail.send(msg)


@app.route("/request_reset", methods=['GET', 'POST'])
def request_reset():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An Email has been sent to you with instructions to reset the password','info')
        return redirect(url_for('login'))
    return render_template('req_res.html',title='Request Reset Password',form=form)


@app.route("/reset/<token>", methods=['GET', 'POST'])
def reset(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token','warning')
        return redirect(url_for('request_reset'))
    else:
        form = ResetPassword()
        if form.validate_on_submit():
            hashed= bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user.password = hashed 
            db.session.commit()
            flash('Your password has been successfully reset, you can now login','success')
            return redirect(url_for('login'))
    
        return render_template('reset.html',title='Reset Password',form=form) 
