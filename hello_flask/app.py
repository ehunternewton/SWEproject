from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
# from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators,SelectField
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'xavier.c4dthivni7sx.us-east-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345678'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MySQL
mysql = MySQL(app)

# Articles = Articles()


# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')


# Articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)

    # Close connection
    cur.close()
    return render_template('articles.html', articles=Articles)


# Single Article
@app.route('/article/<string:id>')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", id)
    article = cur.fetchone()

    return render_template('article.html', article=article)


# Easter egg game
@app.route('/flap')
def flap():
    return render_template('flap.html')


# Register Form
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')
    roles = SelectField(u'Role', choices=[('1', 'Admin'), ('2', 'Teacher'), ('3', 'Student')])


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        roles = form.roles.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO users(name, email, username, password,role_id) VALUES(%s, %s, %s, %s,%s);", (name, email, username, password,roles))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in!', 'success')

        redirect(url_for('index'))
    return render_template('register.html', form=form)


# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur. execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
            is_admin = data['role_id'] == 1;
            is_teacher = data['role_id'] == 2;
            is_student = data['role_id'] == 3;

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                session['is_admin'] = is_admin;
                session['is_teacher'] = is_teacher;
                session['is_student'] = is_student;

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('login'))
    return wrap


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles = articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)

    # Close connection
    cur.close()


# Article Form
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])


# Add article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# Edit article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    cur.close()

    # Get form
    form = ArticleForm(request.form)

    # populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM articles WHERE id = %s", id)

    mysql.connection.commit()
    cur.close()

    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))


app.secret_key = 'secret123'
if __name__ == '__main__':
    app.run()
