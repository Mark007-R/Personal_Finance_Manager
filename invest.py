from flask import Blueprint, render_template
import mysql.connector

# Define Blueprint
invest_bp = Blueprint('invest_bp', __name__)


@invest_bp.route('/invest', methods=['GET', 'POST'], endpoint='invest')
def invest():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='pass123',
        database='finase'
    )
    cursor = conn.cursor(dictionary=True)

    # Get total balance
    cursor.execute("SELECT amount FROM transactions")
    transactions = cursor.fetchall()
    total_balance = sum(t['amount'] for t in transactions)

    options = []

    # Recurring Deposits
    cursor.execute(
        "SELECT * FROM RecurringDeposits WHERE min_investment <= %s", (total_balance,))
    for row in cursor.fetchall():
        row['type'] = 'Recurring Deposit'
        options.append(row)

    # Bonds with bank name
    cursor.execute("""
        SELECT b.*, bank.bank_name 
        FROM Bonds b 
        JOIN Banks bank ON b.bank_id = bank.bank_id 
        WHERE b.minimum_investment <= %s
    """, (total_balance,))
    for row in cursor.fetchall():
        row['type'] = 'Bond'
        options.append(row)

    # Bank Stocks
    cursor.execute(
        "SELECT * FROM BankStockData WHERE CurrentPrice <= %s", (total_balance,))
    for row in cursor.fetchall():
        row['type'] = 'Bank Stock'
        options.append(row)

    # Life Insurance
    cursor.execute(
        "SELECT * FROM BankLifeInsurance WHERE premium_range <= %s", (total_balance,))
    for row in cursor.fetchall():
        row['type'] = 'Life Insurance'
        options.append(row)

    cursor.close()
    conn.close()

    return render_template('invest.html', options=options, total_balance=total_balance)
