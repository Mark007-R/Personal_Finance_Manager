from flask import Blueprint, render_template, request, session, redirect, url_for
import os
import subprocess
import re
from datetime import datetime
import pymysql

extract_bill_bp = Blueprint(
    'extract_bill_bp', __name__, template_folder='templates')

import os
DB_CONFIG = {
    'host': os.getenv('DB_SERVER'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'database': os.getenv('DB_NAME')
}


def get_db_connection():
    return pymysql.connect(**DB_CONFIG)


def extract_text_from_pdf(pdf_path):
    desktop_path = os.path.expanduser('~/Desktop')
    output_path = os.path.join(desktop_path, 'extracted_text.txt')
    # poppler_path = r'C:\\xampp\\htdocs\\website\\poppler-24.07.0\\Library\\bin\\pdftotext.exe'
    poppler_path = r'C:\poppler-24.07.0\Library\bin\pdftotext.exe'

    result = subprocess.run(
        [poppler_path, pdf_path, output_path], capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception('Error extracting text from PDF: ' + result.stderr)

    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise Exception('Extracted text file not found.')


def find_bill_details(text):
    amount_match = re.findall(r'\b\d+\.\d{2}\b', text)
    date_match = re.findall(r'\b(\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4})\b', text)

    amount = float(amount_match[0]) if amount_match else 0.0
    date_str = date_match[0] if date_match else None

    bill_date = 'Not found'
    if date_str:
        for fmt in ('%m/%d/%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'):
            try:
                bill_date = datetime.strptime(
                    date_str, fmt).strftime('%Y-%m-%d')
                break
            except ValueError:
                continue

    return -abs(amount), bill_date


@extract_bill_bp.route('/extract_bill', methods=['GET', 'POST'])
def extract_bill():
    if 'user_id' not in session:
        return redirect(url_for('login_bp.login'))

    bill_amount = ''
    bill_date = ''
    error_message = ''
    debug_text = ''

    if request.method == 'POST':
        if 'pdf' not in request.files:
            error_message = 'No file uploaded.'
        else:
            file = request.files['pdf']
            if file and file.filename.endswith('.pdf'):
                temp_path = os.path.join('temp', file.filename)
                os.makedirs('temp', exist_ok=True)
                file.save(temp_path)
                try:
                    text = extract_text_from_pdf(temp_path)
                    debug_text = text
                    amount, date = find_bill_details(text)

                    bill_amount = amount
                    bill_date = date

                    # Save to DB
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO transactions (description, amount, date) VALUES (%s, %s, %s)",
                            ('Bill', amount, date)
                        )
                        conn.commit()
                    conn.close()
                except Exception as e:
                    error_message = str(e)
                finally:
                    os.remove(temp_path)

    return render_template('extract_bill.html',
                           bill_amount=bill_amount,
                           bill_date=bill_date,
                           error_message=error_message,
                           debug_text=debug_text)
