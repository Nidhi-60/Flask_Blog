from flask import Flask, render_template, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from wtforms import Form, StringField, PasswordField, validators, TextAreaField, SelectField, FileField

app = Flask(__name__)
app.config['IMAGE_UPLOADS'] = 'static/image/uploaded/'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = 'ThisIsComputerWorld'

db = SQLAlchemy(app)


# table for user
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(80))
    blogs = db.relationship('Blog', backref='writer')
    comments = db.relationship('BlogComment', backref='comment_writer')
    category = db.relationship('Category', backref='category_writer')


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), unique=True, nullable=False)
    body = db.Column(db.String(50))
    image = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=datetime.now())
    writer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    comment_blog = db.relationship('BlogComment', backref='comment_blog')


class BlogComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(200))
    writer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))


# category
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20))
    writer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    blog = db.relationship('Blog', backref='category')


# home page
@app.route('/')
def home():
    blog = Blog.query.all()
    if not blog:
        if session:
            return redirect('/add_blog/')
        else:
            return redirect('/Login/')
    else:
        return render_template('pages/displayblog.html', blog=blog)


# Register
# Registration Form
class RegisterForm(Form):
    username = StringField(label="Enter User Name ", validators=[validators.input_required("Please Fill the Field."),
                                                                 validators.length(min=3, max=20,
                                                                                   message="User Name "
                                                                                           "Must between 3 to 20")])
    email = StringField(label="Enter Email ", validators=[validators.input_required("Please fill the field")])
    password = PasswordField(label="Password ", validators=[validators.input_required(),
                                                            validators.equal_to('confirm', 'Password Not match')])
    confirm = PasswordField(label="Confirm Password ", validators=[validators.input_required()])


# User Registration
@app.route('/Registration/', methods=['GET', 'POST'])
def registration():
    registration_form = RegisterForm(request.form)
    if request.method == 'POST' and registration_form.validate():
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Successfully Registered..", 'info')
        return redirect('/Login/')
    else:
        return render_template('pages/registration.html', form=registration_form)


# Login
# login form
class LoginUser(Form):
    username = StringField(label="UserName", validators=[validators.input_required("Please Fill the Field."),
                                                         validators.length(min=3, max=20,
                                                                           message="User Name Mus between 3 to 20")])
    password = PasswordField(label="Password", validators=[validators.input_required()])


# User Login
@app.route('/Login/', methods=['GET', 'POST'])
def login():
    form = LoginUser(request.form)
    if request.method == 'POST' and form.validate():
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = user.username
            session['userid'] = user.id
            flash("successfully login", "info")
            return redirect('/')
        else:
            flash("please check User name or password", "danger")
            return redirect('/Login/')
    else:
        return render_template('pages/login.html', form=form)


# logout
@app.route('/Logout/')
def logout():
    session.clear()
    flash('Successfully logout', "info")
    return redirect('/')


# Category Add Form
class AddCategory(Form):
    category = StringField(label="Category_name: ", validators=[validators.input_required()])


# add Category
@app.route('/add_category/', methods=['GET', 'POST'])
def add_category():
    form = AddCategory(request.form)
    if request.method == 'POST' and form.validate():
        if not session['username']:
            return redirect('/Login/')
        else:
            category_name = request.form['category']
            category = Category(category=category_name, writer_id=session['userid'])
            db.session.add(category)
            db.session.commit()
            return redirect('/category/')
    else:
        return render_template('pages/addcategory.html', form=form)


# display Category
@app.route('/category/')
def display_category():
    category = Category.query.all()
    if category:
        return render_template('pages/displaycategory.html', category=category)
    else:
        return redirect('/add_category/')


# Blog Add
class AddBlog(Form):
    category = Category.query.all()
    title = StringField(label="Title: ", validators=[validators.input_required("Please Fill The field")])
    body = TextAreaField(label="Body: ", validators=[validators.input_required("Please Fill The Field")])
    image = FileField(label='blog_image')
    category = SelectField(label="Category : ", choices=[(int(i.id), i.category) for i in category])


# add blog
@app.route('/add_blog/', methods=['GET', 'POST'])
def add_blog():
    form = AddBlog(request.form)
    if request.method == 'POST' and request.files:
        if not session['userid']:
            return redirect('/Login/')
        else:
            image_file = request.files['image']
            image_file.save(f"{app.config['IMAGE_UPLOADS']}{image_file.filename}")
            title = request.form['title']
            body = request.form['body']
            category = int(request.form['category'])
            blog = Blog(title=title, body=body, image=image_file.filename, writer_id=session['userid'], category_id=category)
            db.session.add(blog)
            db.session.commit()
            flash("blog added", 'success')
            return redirect('/view_blog/')
    else:
        return render_template('pages/addblog.html', form=form)


# display blog
@app.route('/view_blog/')
def view_blog():
    blog = Blog.query.all()
    if not blog:
        return redirect('/add_blog/')
    else:
        return render_template('pages/displayblog.html', blog=blog)


# delete category
@app.route('/delete_category/<int:id>/')
def delete_category(id):
    category = Category.query.get(id)
    db.session.delete(category)
    db.session.commit()
    flash("Category Deleted..", 'info')
    return redirect('/category/')


# detail blog
@app.route('/detail_blog/<int:id>/', methods=['GET', 'POST'])
def detail_blog(id):
    blog = Blog.query.get(id)
    comment = BlogComment.query.filter_by(blog_id=id).all()
    if request.method == 'POST':
        if session:
            coment = request.form['txtcomment']
            blog_comment = BlogComment(comment=coment, writer_id=session['userid'], blog_id=id)
            db.session.add(blog_comment)
            db.session.commit()
            return redirect(f'/detail_blog/{blog.id}/')
        else:
            return redirect('/Login/')
    else:
        return render_template('pages/detailblog.html', blog=blog, comment=comment)


# Edit blog
@app.route('/edit_blog/<int:id>/', methods=['GET', 'POST'])
def edit_blog(id):
    blog = Blog.query.get(id)
    if request.method == 'POST':
        blog.title = request.form['txttitle']
        blog.body = request.form['txtbody']
        db.session.add(blog)
        db.session.commit()
        return redirect(f'/detail_blog/{blog.id}/')
    else:
        return render_template('pages/Editform.html', blog=blog)


# delete blog
@app.route('/delete_blog/<int:id>/')
def delete_blog(id):
    blog = Blog.query.get(id)
    db.session.delete(blog)
    db.session.commit()
    flash('successfully deleted..', 'success')
    return redirect('/view_blog/')


# display blog category wise
@app.route('/category_blog/<int:id>/')
def category_blog(id):
    blog = Blog.query.filter_by(category_id=id).all()
    return render_template('pages/BlogByCategory.html', blog=blog)


# delete comment
@app.route('/delete_comment/<int:id>/')
def delete_comment(id):
    comment = BlogComment.query.get(id)
    db.session.delete(comment)
    db.session.commit()
    flash("blog deleted..", 'success')
    return redirect(f'/detail_blog/{comment.blog_id}/')


if __name__ == '__main__':
    app.run(debug=True)