from flask import session, render_template, redirect, url_for,flash,request
from wtforms import Form, validators, DecimalField
from functools import wraps
from .dao import dao


class teacher:

    @staticmethod
    def load_routes(app):

        @app.route('/teacher_dashboard', methods=['GET', 'POST'])
        @teacher_logged_in
        def teacher_dashboard():
            # Get available courses
            response, data = dao.execute("SELECT c.id, c.semester_name, cd.course_name FROM courses c " +
                                         "INNER JOIN course_details cd on c.course_details_id = cd.id " +
                                         "WHERE teacher_id = %s;", (session['user_id'],), 'all')

            return render_template('teacher_dashboard.html', courses=data)


        @app.route('/gradebook/<string:course_id>', methods=['GET', 'POST'])
        @teacher_logged_in
        def gradebook(course_id):
            response, data = dao.execute(
                "SELECT cd.course_name, u.first_name, u.last_name, cr.id, cr.course_gpa, cr.exam_1, cr.exam_2, cr.final"
                " FROM course_registration cr "
                "INNER JOIN users u on cr.student_id = u.id "
                "INNER JOIN courses c on cr.course_id = c.id "
                "INNER JOIN course_details cd on c.course_details_id = cd.id "
                "WHERE course_id = %s;", [course_id], 'all')
            return render_template('gradebook.html', course=data)


        @app.route('/gradebook/'
                   'update_grades/<string:course_registration_id>/', methods=['GET', 'POST'])
        @teacher_logged_in
        def update_grades(course_registration_id):
            response, data = dao.execute("SELECT * FROM course_registration WHERE id = %s;", [course_registration_id],
                                         'one')

            # Get form
            form = UpdateGradesForm(request.form)

            # populate form fields
            form.exam_1.data = data['exam_1']
            form.exam_2.data = data['exam_2']
            form.final.data = data['final']

            if request.method == 'POST' and form.validate():
                exam_1 = request.form['exam_1']
                exam_2 = request.form['exam_2']
                final = request.form['final']
                gpa = 0.0

                if exam_1 != "" and exam_2 != "" and final != "":
                    # calculate GPA
                    average = (float(exam_1) + float(exam_2) + float(final)) / 3
                    if average > 89.5:
                        gpa = 4.0
                    elif average > 79.5:
                        gpa = 3.0
                    elif average > 69.5:
                        gpa = 2.0
                    elif average > 59.5:
                        gpa = 1.0
                    else:
                        gpa = 0.0
                # Execute Commit
                dao.execute("UPDATE course_registration SET course_gpa=%s, exam_1=%s, exam_2=%s, final=%s WHERE id=%s",
                            (gpa, exam_1, exam_2, final, course_registration_id), 'commit')
                flash('Grades Updated', 'success')
                return redirect(url_for('teacher_dashboard'))

            return render_template('update_grades.html', form=form)


class UpdateGradesForm(Form):
    exam_1 = DecimalField('Exam 1',  [validators.optional()])
    exam_2 = DecimalField('Exam 2', [validators.optional()])
    final = DecimalField('Final', [validators.optional()])


def teacher_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'teacher_logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('teacher_login'))
    return wrap
