from flask import session, render_template, redirect, url_for, flash, request
from passlib.hash import sha256_crypt
from wtforms import Form, validators, StringField, SelectField, PasswordField
from functools import wraps
from dao import dao


class admin:

    @staticmethod
    def load_routes(app):

        @app.route('/admin_dashboard/', defaults ={'search_student': ''}, methods=['GET', 'POST'])
        @app.route('/admin_dashboard/<string:search_student>', methods=['GET', 'POST'])
        @admin_logged_in
        def admin_dashboard(search_student):
            # Get students

            if search_student == '':
                response, students = dao.execute(
                    "SELECT * FROM users WHERE role_id = 3",None, 'all')
            else:
                search_student = "'%%"+search_student+"%%'"
                sql = "SELECT * FROM users WHERE role_id = 3 AND (last_name Like "+search_student+" OR first_name Like "+search_student+" OR username Like  "+search_student+" )"
                response, students = dao.execute(sql, None, 'all')
            # Get teachers
            response, teachers = dao.execute("SELECT * FROM users WHERE role_id = 2", None, 'all')

            # Get admins
            response, admins = dao.execute("SELECT * FROM users WHERE role_id = 1", None, 'all')

            # Get course catalog
            response, course_details = dao.execute("SELECT * FROM course_details", None, 'all')

            # Get available courses
            response, courses = dao.execute("SELECT c.id, c.semester_name, cd.course_name, u.first_name, u.last_name "
                                            "FROM courses c "
                                            "INNER JOIN course_details cd on c.course_details_id = cd.id "
                                            "INNER JOIN users u on c.teacher_id = u.id", None, 'all')

            return render_template('admin_dashboard.html', students=students, teachers=teachers, admins=admins,
                                   course_details=course_details, courses=courses)

        @app.route('/user_registration', methods=['GET', 'POST'])
        @admin_logged_in
        def user_registration():
            form = UserRegisterForm(request.form)
            if request.method == 'POST' and form.validate():
                first_name = form.first_name.data
                last_name = form.last_name.data
                email = form.email.data
                username = form.username.data
                role = form.role.data
                password = sha256_crypt.encrypt(str('admin'))

                # Execute
                dao.execute(
                    "INSERT INTO users(first_name, last_name, email, username, password, role_id) VALUES(%s, %s, %s, %s, %s, %s);",
                    (first_name, last_name, email, username, password, role), 'commit')

                flash('User registered!', 'success')

                redirect(url_for('admin_dashboard'))

            return render_template('user_registration.html', form=form)

        # Edit user
        @app.route('/edit_user/<string:user_id>', methods=['GET', 'POST'])
        @admin_logged_in
        def edit_user(user_id):

            # Get user by id
            response, user = dao.execute("SELECT * FROM users WHERE id = %s", [user_id], 'one')

            # Get form
            form = UserRegisterForm(request.form)

            # populate user form fields
            form.first_name.data = user['first_name']
            form.last_name.data = user['last_name']
            form.email.data = user['email']
            form.username.data = user['username']
            # role_id is an int, the form requires a string
            form.role.data = str(user['role_id'])

            if request.method == 'POST' and form.validate():
                first_name = request.form['first_name']
                last_name = request.form['last_name']
                email = request.form['email']
                username = request.form['username']
                role = request.form['role']

                # Execute
                dao.execute(
                    "UPDATE users SET first_name=%s, last_name=%s, email=%s, username=%s, role_id=%s WHERE id=%s",
                    (first_name, last_name, email, username, role, user_id), 'commit')

                flash('User Updated', 'success')

                return redirect(url_for('admin_dashboard'))

            return render_template('edit_user.html', form=form)

        @app.route('/delete_user/<string:user_id>', methods=['POST'])
        @admin_logged_in
        def delete_user(user_id):

            response, user_to_delete = dao.execute("SELECT * FROM users WHERE id = %s", [user_id], 'one')
            if int(user_to_delete['role_id']) == 3:
                dao.execute("DELETE FROM course_registration WHERE student_id = %s", [user_to_delete['id']], 'commit')

            dao.execute("DELETE FROM users WHERE id = %s", [user_id], 'commit')

            flash('User Deleted', 'success')
            return redirect(url_for('admin_dashboard'))

        @app.route('/create_course', methods=['GET', 'POST'])
        @admin_logged_in
        def create_course():
            form = CourseCreationForm(request.form)
            if request.method == 'POST' and form.validate():
                course_name = form.course_name.data
                course_description = form.course_description.data

                # Execute
                dao.execute("INSERT INTO course_details(course_name, course_description) VALUES(%s, %s);",
                            (course_name, course_description), 'commit')

                flash('Course created!', 'success')

                return redirect(url_for('admin_dashboard'))

            return render_template('create_course.html', form=form)

        @app.route('/edit_course/<string:course_id>', methods=['GET', 'POST'])
        @admin_logged_in
        def edit_course(course_id):

            # Get course by id
            response, course = dao.execute("SELECT * FROM course_details WHERE id = %s", [course_id], 'one')

            form = CourseCreationForm(request.form)
            form.course_name.data = course['course_name']
            form.course_description.data = course['course_description']

            if request.method == 'POST' and form.validate():
                course_name = request.form['course_name']
                course_description = request.form['course_description']

                # Execute
                dao.execute("UPDATE course_details SET course_name=%s, course_description=%s WHERE id=%s;",
                            (course_name, course_description, course_id), 'commit')

                flash('Course updated!', 'success')

                return redirect(url_for('admin_dashboard'))

            return render_template('edit_course.html', form=form)

        @app.route('/delete_course/<string:course_id>', methods=['POST'])
        @admin_logged_in
        def delete_course(course_id):

            response, registrations = dao.execute("SELECT * FROM courses WHERE course_details_id = %s", [course_id], 'one')
            course_to_delete = registrations['id']
            # records are explicitly deleted
            dao.execute("DELETE FROM course_registration WHERE course_id = %s", [course_to_delete], 'commit')
            dao.execute("DELETE FROM courses WHERE course_details_id = %s", [course_id], 'commit')
            dao.execute("DELETE FROM course_details WHERE id = %s", [course_id], 'commit')

            flash('Course Deleted', 'success')
            return redirect(url_for('admin_dashboard'))

        @app.route('/course_registration', methods=['GET', 'POST'])
        @admin_logged_in
        def course_registration():
            form = CourseRegisterForm(request.form)
            if request.method == 'POST' and form.validate():
                course_details_id = form.course_details_id.data
                teacher_id = form.teacher_id.data
                semester_name = form.semester_name.data

                # Execute
                dao.execute("INSERT INTO courses(course_details_id, teacher_id, semester_name) VALUES(%s, %s, %s);",
                            (course_details_id, teacher_id, semester_name), 'commit')

                flash('Course registered!', 'success')

                return redirect(url_for('admin_dashboard'))

            return render_template('course_registration.html', form=form)

        @app.route('/student_course_registration', methods=['GET', 'POST'])
        @admin_logged_in
        def student_course_registration():
            form = StudentCourseRegisterForm(request.form)
            if request.method == 'POST' and form.validate():
                student_id = form.student_id.data
                course_id = form.course_id.data

                # validate student_id is a student and course_id is a course
                response, student = dao.execute("SELECT * FROM users WHERE id = %s AND role_id = 3", [student_id],
                                                'all')
                response, course = dao.execute("SELECT * FROM courses WHERE id = %s", [course_id], 'all')

                if len(student) > 0 and len(course) > 0:
                    # Execute
                    dao.execute("INSERT INTO course_registration(student_id, course_id) VALUES(%s, %s);",
                                (int(student_id), int(course_id)), 'commit')

                    flash('Student registered in the course!', 'success')

                    return redirect(url_for('admin_dashboard'))
                else:
                    error = "StudentID or CourseID does not exist"
                    return render_template('student_course_registration.html', form=form, error=error)

            return render_template('student_course_registration.html', form=form)

        @app.route('/change_password', methods=['GET', 'POST'])
        def change_password():
            form = ChangePasswordForm(request.form)
            if request.method == 'POST' and form.validate():
                password = sha256_crypt.encrypt(str(form.password.data))
                dao.execute("UPDATE users SET password = %s WHERE id = %s;", (password, session['user_id']), 'commit')
                flash('Password changed!', 'success')
                return redirect(url_for('index'))
            return render_template('change_password.html', form=form)


def admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('admin_login'))

    return wrap


# Register Form
class UserRegisterForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    role = SelectField('Role', choices=[('1', 'Admin'), ('2', 'Teacher'), ('3', 'Student')])
    # password = PasswordField('Password', [
    #     validators.DataRequired(),
    #     validators.EqualTo('confirm', message='Passwords do not match')
    # ])
    # confirm = PasswordField('Confirm Password')


# Register Form
class CourseCreationForm(Form):
    course_name = StringField('Course Name', [validators.Length(min=1, max=100)])
    course_description = StringField('Course Description', [validators.Length(min=4, max=255)])


# Register Form
class CourseRegisterForm(Form):
    course_details_id = StringField('Course Catalog ID', [validators.Length(min=1, max=100)])
    teacher_id = StringField('Teacher ID', [validators.Length(min=1, max=255)])
    semester_name = StringField('Semester', [validators.Length(min=1, max=255)])


# Register Form
class StudentCourseRegisterForm(Form):
    student_id = StringField('Student ID', [validators.Length(min=1, max=100)])
    course_id = StringField('Course ID', [validators.Length(min=1, max=255)])


# change password form
class ChangePasswordForm(Form):
    password = PasswordField('Password', [validators.DataRequired(),
                                          validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')