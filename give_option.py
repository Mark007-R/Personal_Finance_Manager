from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
import os

# Blueprint setup
# give_option_bp = Blueprint('give_option', __name__)
app = Flask(__name__)

# Database config
DB_HOST = os.getenv('DB_SERVER', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASS', 'pass123')
DB_NAME = os.getenv('DB_NAME', 'finase')

@app.route('/')
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if request.method == 'POST':
            description = request.form.get('description')
            amount = request.form.get('amount')
            date = request.form.get('date')

            if description and amount and date:
                cursor.execute(
                    "INSERT INTO transactions (description, amount, date) VALUES (%s, %s, %s)",
                    (description, float(amount), date)
                )
                conn.commit()
                flash("Transaction added successfully!", "success")
            else:
                flash("Please fill out all fields.", "warning")

        delete_id = request.args.get('delete')
        if delete_id:
            cursor.execute(
                "DELETE FROM transactions WHERE id = %s", (int(delete_id),))
            conn.commit()
            flash("Transaction deleted successfully!", "success")
            return redirect(url_for('give_option.dashboard'))

        cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
        transactions = cursor.fetchall()

    except Exception as e:
        conn.rollback()
        flash(f"Database error: {e}", "danger")
        transactions = []

    finally:
        cursor.close()
        conn.close()

    return render_template('give_option.html', transactions=transactions)
