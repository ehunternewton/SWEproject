from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)


# Config MySQL
aws db
app.config['MYSQL_HOST'] = 'xavier.c4dthivni7sx.us-east-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345678'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# local db
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = '123456'
# app.config['MYSQL_DB'] = 'xmendb'
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MySQL
mysql = MySQL(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('home.html')


@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur. execute("SELECT * FROM users WHERE username = %s and role_id = 3", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['student_logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('student_dashboard'))
            else:
                error = 'Invalid login'
                return render_template('student_login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('student_login.html', error=error)
    return render_template('student_login.html')


def student_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'student_logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('student_login'))
    return wrap


@app.route('/student_dashboard', methods=['GET', 'POST'])
@student_logged_in
def student_dashboard():
    return render_template('student_dashboard.html')


@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur. execute("SELECT * FROM users WHERE username = %s and role_id = 2", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['teacher_logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('teacher_dashboard'))
            else:
                error = 'Invalid login'
                return render_template('teacher_login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('student_login.html', error=error)
    return render_template('teacher_login.html')


def teacher_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'teacher_logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('teacher_login'))
    return wrap


@app.route('/teacher_dashboard', methods=['GET', 'POST'])
@teacher_logged_in
def teacher_dashboard():
    return render_template('teacher_dashboard.html')


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur. execute("SELECT * FROM users WHERE username = %s and role_id = 1", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['admin_logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                error = 'Invalid login'
                return render_template('admin_login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('admin_login.html', error=error)

    return render_template('admin_login.html')


def admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('admin_login'))
    return wrap


@app.route('/admin_dashboard', methods=['GET', 'POST'])
@admin_logged_in
def admin_dashboard():
    return render_template('admin_dashboard.html')


# Logout
@app.route('/logout')
#  @is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))


# Register Form
class UserRegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    role = SelectField('Role', choices=[('1', 'Admin'), ('2', 'Teacher'), ('3', 'Student')])
    # password = PasswordField('Password', [
    #     validators.DataRequired(),
    #     validators.EqualTo('confirm', message='Passwords do not match')
    # ])
    # confirm = PasswordField('Confirm Password')


@app.route('/user_registration', methods=['GET', 'POST'])
@admin_logged_in
def user_registration():
    form = UserRegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        # last_name = form.last_name.data
        email = form.email.data
        username = form.username.data
        role = form.role.data
        password = sha256_crypt.encrypt(str('admin'))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO users(name, email, username, password, role_id) VALUES(%s, %s, %s, %s, %s);",
                    (name, email, username, password, role))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('User registered!', 'success')

        redirect(url_for('admin_dashboard'))

    return render_template('user_registration.html', form=form)


# Register Form
class CourseCreationForm(Form):
    course_name = StringField('Name', [validators.Length(min=1, max=100)])
    course_description = StringField('Username', [validators.Length(min=4, max=255)])


@app.route('/create_course', methods=['GET', 'POST'])
@admin_logged_in
def create_course():
    form = CourseCreationForm(request.form)
    if request.method == 'POST' and form.validate():
        course_name = form.course_name.data
        course_description = form.course_description.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO courses(course_name, course_description) VALUES(%s, %s);",
                    (course_name, course_description))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Course created!', 'success')

        redirect(url_for('admin_dashboard'))

    return render_template('create_course.html', form=form)


app.secret_key = 'secret123'
if __name__ == '__main__':
    app.run()
