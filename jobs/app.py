from flask import Flask, render_template, request, redirect, url_for, g
import datetime
import sqlite3

PATH = "db/jobs.sqlite"

app = Flask(__name__)


def open_connection():
    connection = getattr(g, '_connection', None)

    if connection is None:
        connection = g._connection = sqlite3.connect(PATH)

    connection.row_factory = sqlite3.Row
    return connection


def execute_sql(sql, values=(), commit=False, single=False):
    connection = open_connection()
    cursor = connection.execute(sql, values)

    if commit is True:
        results = connection.commit()
    else:
        results = cursor.fetchone() if single else cursor.fetchall()

    cursor.close()
    return results


@app.teardown_appcontext
def close_connection(exception):
    connection = getattr(g, '_connection', None)

    if connection is not None:
        connection.close()


@app.route("/")
@app.route("/jobs")
def jobs():
    sql = '''SELECT job.id, job.title, job.description, job.salary, employer.id 
                as employer_id, employer.name as employer_name FROM job JOIN 
                employer ON employer.id = job.employer_id'''

    jobs_list = execute_sql(sql)
    return render_template('index.html', jobs=jobs_list)


@app.route("/job/<job_id>")
def job(job_id):
    sql = '''SELECT job.id, job.title, job.description, job.salary, 
                employer.id as employer_id, employer.name as employer_name
                FROM job JOIN employer ON employer.id = job.employer_id 
                WHERE job.id = ?'''

    job_obj = execute_sql(sql, [job_id], single=True)
    return render_template('job.html', job=job_obj)


@app.route("/employer/<employer_id>")
def employer(employer_id):
    employer_sql = 'SELECT * FROM employer WHERE id=?'
    jobs_sql = '''SELECT job.id, job.title, job.description, job.salary
                    FROM job JOIN employer ON employer.id = job.employer_id
                    WHERE employer.id = ?'''
    reviews_sql = '''SELECT review, rating, title, date, status FROM review
                        JOIN employer ON employer.id = review.employer_id
                        WHERE employer.id = ?'''

    employer_obj = execute_sql(employer_sql, [employer_id], single=True)
    jobs_list = execute_sql(jobs_sql, [employer_id])
    reviews_list = execute_sql(reviews_sql, [employer_id])
    return render_template(
        "employer.html", employer=employer_obj, jobs=jobs_list,
        reviews=reviews_list
        )


@app.route("/employer/<employer_id>/review", methods=['GET', 'POST'])
def review(employer_id):
    if request.method == "POST":
        review = request.form['review']
        rating = request.form['rating']
        title = request.form['title']
        status = request.form['status']
        date = datetime.datetime.now().strftime("%m/%d/%Y")
        sql = '''INSERT INTO review 
                    (review, rating, title, date, status, employer_id) 
                    VALUES (?, ?, ?, ?, ?, ?)'''

        execute_sql(
            'INSERT INTO review (review, rating, title, date, status, '
            'employer_id) VALUES (?, ?, ?, ?, ?, ?)',
            (review, rating, title, date, status, employer_id), commit=True
            )

        return redirect(url_for('employer', employer_id=employer_id))
    else:
        return render_template('review.html', employer_id=employer_id)
