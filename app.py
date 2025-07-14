from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
import os

# Import Blueprints
from login import login_bp
from signup import signup_bp
from invest import invest_bp
from extract_bill import extract_bill_bp


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

# Register Blueprints
app.register_blueprint(login_bp)
app.register_blueprint(signup_bp)
app.register_blueprint(invest_bp)
app.register_blueprint(extract_bill_bp)

# Database configuration
DB_HOST = os.getenv('DB_SERVER', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASS', 'pass123')
DB_NAME = os.getenv('DB_NAME', 'finase')


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route('/invest')
def invest():
    return render_template('invest.html')


@app.route('/extract_bill')
def extract_bill():
    return render_template('extract_bill.html')


@app.route('/logout')
def logout():
    session.clear()
    # 'login' matches the endpoint in login_bp
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_bp.login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Add new transaction
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

        # Handle deletion
        delete_id = request.args.get('delete')
        if delete_id:
            cursor.execute(
                "DELETE FROM transactions WHERE id = %s", (int(delete_id),))
            conn.commit()
            flash("Transaction deleted successfully!", "success")
            return redirect(url_for('dashboard'))

        # Fetch transactions
        cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
        transactions = cursor.fetchall()

    except Exception as e:
        conn.rollback()
        flash(f"Database error: {e}", "danger")
        transactions = []

    finally:
        cursor.close()
        conn.close()

    return render_template('main.html', transactions=transactions)


if __name__ == '__main__':
    app.run(debug=True)
