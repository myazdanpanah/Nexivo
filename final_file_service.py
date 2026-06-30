# final_file_service.py - نسخه نهایی با استفاده از سرویس ReportBro برای تولید PDF
import os
import sys
import json
import io
import re
import traceback
import logging
import subprocess
import requests  # اضافه شد برای ارتباط با سرویس ReportBro
from datetime import datetime
from flask import Flask, request, send_file, jsonify, render_template_string
import pyodbc
import jdatetime
import pandas as pd
from docxtpl import DocxTemplate
from jinja2 import Environment, Template

# ==================== راه‌اندازی ====================
logging.basicConfig(level=logging.DEBUG, filename='service_errors.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)

# ==================== مسیرها و تنظیمات ====================
REPORTBRO_SERVICE_URL = "http://127.0.0.1:5001"  # آدرس سرویس ReportBro (اجرا روی پورت 5001)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

FINAL_STORAGE = r"C:\Users\myazd\Downloads\Invoice-Bills"
os.makedirs(FINAL_STORAGE, exist_ok=True)

def get_db_connection():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(".")
    local_config = os.path.join(base_dir, "db_config.json")
    if os.path.exists(local_config):
        config_path = local_config
    else:
        config_path = resource_path("db_config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['server']};DATABASE={config['database']};UID={config['username']};PWD={config['password']}"
    return pyodbc.connect(conn_str)

# ==================== توابع کمکی ====================
def to_persian_digits(text):
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    trans_table = str.maketrans(english_digits, persian_digits)
    return text.translate(trans_table)

def persian_to_english_number_strict(value, field_name="مقدار"):
    if pd.isna(value):
        raise ValueError(f"{field_name}: مقدار None یا NaN است")
    value = str(value).strip()
    if value == "":
        raise ValueError(f"{field_name}: رشته خالی است")
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    for p, e in zip(persian_digits, english_digits):
        value = value.replace(p, e)
    value = re.sub(r"[^\d\-]", "", value)
    if value == "" or value == "-":
        raise ValueError(f"{field_name}: عدد معتبر یافت نشد ('{value}')")
    return int(value)

def safe_str_strict(value, field_name="فیلد"):
    if pd.isna(value):
        raise ValueError(f"{field_name}: مقدار None یا NaN است")
    s = str(value).strip()
    if s == "":
        raise ValueError(f"{field_name}: رشته خالی است")
    return s

def safe_filename(text):
    text = str(text).strip()
    if not text:
        text = "بدون_نام"
    text = re.sub(r'[\\/*?:"<>|]', '-', text)
    text = text.replace('/', '-').replace('\\', '-')
    return text

def get_company_settings_from_db(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM company_settings WHERE id=1")
    row = cursor.fetchone()
    if row:
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row))
    return {}

# ==================== توابع شماره‌گذاری اتمیک ====================
def get_next_letter_number(conn, payer_code, year):
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(number) FROM available_letter_numbers WHERE payer_code = ? AND year = ?", (payer_code, year))
    row = cursor.fetchone()
    if row and row[0] is not None:
        return row[0]
    cursor.execute("SELECT last_number FROM letter_sequences WHERE payer_code = ? AND year = ?", (payer_code, year))
    row = cursor.fetchone()
    return row[0] + 1 if row else 1

def update_letter_sequence(conn, payer_code, year, last_number):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM available_letter_numbers WHERE payer_code = ? AND year = ? AND number = ?", (payer_code, year, last_number))
    if cursor.fetchone():
        cursor.execute("DELETE FROM available_letter_numbers WHERE payer_code = ? AND year = ? AND number = ?", (payer_code, year, last_number))
    else:
        cursor.execute("""
            MERGE INTO letter_sequences AS target
            USING (VALUES (?, ?, ?)) AS source (payer_code, year, last_number)
            ON target.payer_code = source.payer_code AND target.year = source.year
            WHEN MATCHED THEN UPDATE SET last_number = source.last_number
            WHEN NOT MATCHED THEN INSERT (payer_code, year, last_number) VALUES (source.payer_code, source.year, source.last_number);
        """, (payer_code, year, last_number))
    conn.commit()

def get_or_create_final_letter_number(conn, req_id, payer_code):
    cursor = conn.cursor()
    cursor.execute("SELECT final_letter_number FROM approval_requests WHERE id = ?", (req_id,))
    row = cursor.fetchone()
    if row and row[0]:
        return row[0]
    year_two_digit = str(jdatetime.date.today().year)[-2:]
    next_num = get_next_letter_number(conn, payer_code, year_two_digit)
    update_letter_sequence(conn, payer_code, year_two_digit, next_num)
    format_str = "YYYY/CODE/NNNNN"
    today = jdatetime.date.today()
    final_number = format_str.replace("YYYY", str(today.year)).replace("YY", year_two_digit).replace("CODE", payer_code).replace("CCC", payer_code.zfill(3)).replace("NUM", str(next_num)).replace("NNNNN", str(next_num).zfill(5))
    cursor.execute("UPDATE approval_requests SET final_letter_number = ? WHERE id = ?", (final_number, req_id))
    conn.commit()
    return final_number

# ==================== تولید PDF از طریق سرویس ReportBro ====================
def render_pdf_via_reportbro(template_id, data):
    """
    ارسال درخواست به سرویس reportbro برای تولید PDF
    template_id: شناسه قالب ذخیره شده (مثلاً 'invoice_template')
    data: دیکشنری داده‌های فاکتور (مطابق با ساختار مورد انتظار قالب)
    """
    # 1. دریافت قالب از سرویس reportbro
    load_url = f"{REPORTBRO_SERVICE_URL}/load-template/{template_id}"
    try:
        response = requests.get(load_url, timeout=10)
        if response.status_code != 200:
            raise Exception(f"قالب {template_id} یافت نشد در سرویس reportbro (status {response.status_code})")
        template_json = response.json()
    except Exception as e:
        logging.error(f"خطا در دریافت قالب از ReportBro: {str(e)}")
        raise Exception(f"خطا در ارتباط با سرویس طراحی قالب: {str(e)}")

    # 2. درخواست رندر PDF
    render_url = f"{REPORTBRO_SERVICE_URL}/render"
    payload = {
        "template": template_json,
        "data": data
    }
    try:
        resp = requests.post(render_url, json=payload, timeout=60)
        if resp.status_code != 200:
            raise Exception(f"خطا در تولید PDF: {resp.text}")
        return resp.content  # bytes PDF
    except Exception as e:
        logging.error(f"خطا در رندر PDF: {str(e)}")
        raise Exception(f"خطا در تولید PDF توسط سرویس ReportBro: {str(e)}")

# ==================== توابع اصلی تولید فایل برای یک درخواست ====================
def generate_files_for_request(req_dict, storage_dir):
    import json
    service_data = json.loads(req_dict.get('service_data_json', '[]'))
    flight_data = json.loads(req_dict.get('flight_data_json', '[]'))
    hotel_data = json.loads(req_dict.get('hotel_data_json', '[]'))

    payer_code = req_dict.get('payer_code')
    payer_name = req_dict.get('payer_name')
    letter_date = req_dict.get('letter_date')
    period_range = req_dict.get('period_range')
    req_id = req_dict.get('id')

    if not payer_code or not payer_name:
        raise ValueError("payer_code یا payer_name خالی است")

    conn = get_db_connection()
    try:
        final_letter_base = get_or_create_final_letter_number(conn, req_id, payer_code)
    except Exception as e:
        conn.close()
        raise ValueError(f"خطا در تخصیص شماره نامه: {str(e)}")

    today_shamsi = jdatetime.date.today()
    date_folder = today_shamsi.strftime("%Y-%m-%d")
    safe_payer = safe_filename(payer_name)
    final_dir = os.path.join(storage_dir, date_folder, safe_payer)
    os.makedirs(final_dir, exist_ok=True)

    company_settings = get_company_settings_from_db(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT national_id, economic_code, address, postal_code, phone FROM payers WHERE code=?", (payer_code,))
    payer_row = cursor.fetchone()
    if not payer_row:
        conn.close()
        raise ValueError(f"طرف حساب با کد {payer_code} یافت نشد")
    buyer_info = {
        'name': payer_name,
        'national_id': payer_row[0] or '',
        'economic_code': payer_row[1] or '',
        'address': payer_row[2] or '',
        'postal_code': payer_row[3] or '',
        'phone': payer_row[4] or ''
    }

    service_packages = []

    # پردازش پروازها
    if flight_data:
        flight_rows = []
        flight_total = 0
        for idx, flt in enumerate(flight_data):
            try:
                debt = persian_to_english_number_strict(flt.get('debt'), f"بدهکار پرواز ردیف {idx+1}")
                credit = persian_to_english_number_strict(flt.get('credit'), f"بستانکار پرواز ردیف {idx+1}")
                balance = debt - credit
                contract = safe_str_strict(flt.get('contract', ''), f"شماره قرارداد پرواز ردیف {idx+1}")
                passenger = safe_str_strict(flt.get('passenger', ''), f"نام مسافر پرواز ردیف {idx+1}")
                route = safe_str_strict(flt.get('route', ''), f"مسیر پرواز ردیف {idx+1}")
                date_val = flt.get('date', '')
                if pd.isna(date_val):
                    date_val = ''
                notes = flt.get('notes', '')
                if pd.isna(notes):
                    notes = ''
                flight_rows.append({
                    'contract': contract,
                    'passenger': passenger,
                    'description': route,
                    'date': str(date_val),
                    'notes': str(notes),
                    'debt': debt,
                    'credit': credit,
                    'balance': balance
                })
                flight_total += balance
            except Exception as e:
                conn.close()
                raise ValueError(f"خطا در رکورد پرواز شماره {idx+1}: {str(e)}")
        if flight_rows:
            service_packages.append({'type': 'پرواز', 'total_balance': flight_total, 'rows': flight_rows})

    # پردازش هتل‌ها
    if hotel_data:
        hotel_rows = []
        hotel_total = 0
        for idx, htl in enumerate(hotel_data):
            try:
                debt = persian_to_english_number_strict(htl.get('debt'), f"بدهکار هتل ردیف {idx+1}")
                credit = persian_to_english_number_strict(htl.get('credit'), f"بستانکار هتل ردیف {idx+1}")
                balance = debt - credit
                contract = safe_str_strict(htl.get('contract', ''), f"شماره قرارداد هتل ردیف {idx+1}")
                passenger = safe_str_strict(htl.get('passenger', ''), f"نام مسافر هتل ردیف {idx+1}")
                hotel_name = safe_str_strict(htl.get('hotel', ''), f"نام هتل ردیف {idx+1}")
                room_type = safe_str_strict(htl.get('room', ''), f"نوع اتاق هتل ردیف {idx+1}")
                description = f"{hotel_name} - {room_type}"
                pax_val = htl.get('pax', 1)
                try:
                    pax = int(persian_to_english_number_strict(pax_val, f"تعداد نفرات هتل ردیف {idx+1}"))
                    if pax < 1:
                        pax = 1
                except:
                    pax = 1
                date_raw = htl.get('date', '')
                if pd.isna(date_raw):
                    date_raw = ''
                notes = htl.get('notes', '')
                if pd.isna(notes):
                    notes = ''
                if not notes and pax > 1:
                    notes = f"تعداد نفرات: {pax}"
                hotel_rows.append({
                    'contract': contract,
                    'passenger': passenger,
                    'description': description,
                    'date': str(date_raw),
                    'notes': str(notes),
                    'debt': debt,
                    'credit': credit,
                    'balance': balance
                })
                hotel_total += balance
            except Exception as e:
                conn.close()
                raise ValueError(f"خطا در رکورد هتل شماره {idx+1}: {str(e)}")
        if hotel_rows:
            service_packages.append({'type': 'هتل', 'total_balance': hotel_total, 'rows': hotel_rows})

    # پردازش سایر خدمات
    if service_data:
        service_rows = []
        service_total = 0
        for idx, svc in enumerate(service_data):
            try:
                debt = persian_to_english_number_strict(svc.get('debt'), f"بدهکار خدمات ردیف {idx+1}")
                credit = persian_to_english_number_strict(svc.get('credit'), f"بستانکار خدمات ردیف {idx+1}")
                balance = debt - credit
                contract = safe_str_strict(svc.get('contract', ''), f"شماره قرارداد خدمات ردیف {idx+1}")
                passenger = safe_str_strict(svc.get('passenger', ''), f"نام مسافر خدمات ردیف {idx+1}")
                svc_type = safe_str_strict(svc.get('type', 'سایر'), f"نوع خدمات ردیف {idx+1}")
                date_val = svc.get('date', '')
                if pd.isna(date_val):
                    date_val = ''
                notes = svc.get('notes', '')
                if pd.isna(notes):
                    notes = ''
                service_rows.append({
                    'contract': contract,
                    'passenger': passenger,
                    'description': svc_type,
                    'date': str(date_val),
                    'notes': str(notes),
                    'debt': debt,
                    'credit': credit,
                    'balance': balance
                })
                service_total += balance
            except Exception as e:
                conn.close()
                raise ValueError(f"خطا در رکورد خدمات شماره {idx+1}: {str(e)}")
        if service_rows:
            service_packages.append({'type': 'سایر خدمات', 'total_balance': service_total, 'rows': service_rows})

    if not service_packages:
        conn.close()
        raise ValueError("هیچ داده معتبری (پرواز، هتل، خدمات) برای تولید وجود ندارد")

    result_files = []
    try:
        for idx, package in enumerate(service_packages):
            current_letter = final_letter_base if idx == 0 else f"{final_letter_base}-{idx+1}"
            safe_letter = safe_filename(current_letter)
            total_balance = package['total_balance']
            is_creditor = total_balance < 0
            template_path = resource_path("template_creditor.docx" if is_creditor else "template.docx")

            # تولید اکسل
            df_excel = pd.DataFrame(package['rows'])
            column_mapping = {
                'contract': 'شماره قرارداد',
                'passenger': 'نام مسافر',
                'description': 'شرح خدمات',
                'date': 'تاریخ',
                'notes': 'توضیحات',
                'debt': 'بدهکار',
                'credit': 'بستانکار',
                'balance': 'مانده'
            }
            df_excel = df_excel.rename(columns=column_mapping)
            df_excel.insert(0, 'ردیف', range(1, len(df_excel)+1))
            excel_path = os.path.join(final_dir, f"صورت حساب {package['type']} {safe_payer} {safe_letter}.xlsx")
            df_excel.to_excel(excel_path, index=False)

            # تولید Word
            if os.path.exists(template_path):
                word_output = os.path.join(final_dir, f"اعلامیه {package['type']} {safe_payer} {safe_letter}.docx")
                doc = DocxTemplate(template_path)
                context_word = {
                    'letter_date': '/'.join(reversed(letter_date.split('/'))) if '/' in letter_date else letter_date,
                    'letter_number': '/'.join(reversed(current_letter.split('/'))) if '/' in current_letter else current_letter,
                    'payer': buyer_info['name'],
                    'subsidiary': payer_name,
                    'service_type': package['type'],
                    'period_range': period_range,
                    'total_debt': f"{abs(total_balance):,}" if not is_creditor else "",
                    'total_credit': f"{abs(total_balance):,}" if is_creditor else "",
                    'bank_name1': company_settings.get('bank_name1', ''),
                    'account_number1': company_settings.get('account_number1', ''),
                    'shaba_number1': company_settings.get('shaba_number1', ''),
                    'bank_name2': company_settings.get('bank_name2', ''),
                    'account_number2': company_settings.get('account_number2', ''),
                    'shaba_number2': company_settings.get('shaba_number2', ''),
                    'company_name': company_settings.get('company_name', ''),
                    'manager_name': company_settings.get('manager_name', ''),
                    'manager_position': company_settings.get('manager_position', '')
                }
                doc.render(context_word)
                doc.save(word_output)

            # تولید PDF با استفاده از سرویس ReportBro
            # ساختار داده برای ReportBro باید با قالب طراحی شده هماهنگ باشد
            pdf_context = {
                'seller': {
                    'company_name': company_settings.get('company_name', ''),
                    'national_id': company_settings.get('national_id', ''),
                    'economic_code': company_settings.get('economic_code', ''),
                    'address': company_settings.get('address', ''),
                    'postal_code': company_settings.get('postal_code', ''),
                    'phone': company_settings.get('phone', ''),
                    'manager_name': company_settings.get('manager_name', ''),
                    'manager_position': company_settings.get('manager_position', ''),
                    'signature_path': company_settings.get('signature_path', ''),
                    'stamp_path': company_settings.get('stamp_path', '')
                },
                'buyer': buyer_info,
                'invoice_number': current_letter,
                'invoice_date': letter_date,
                'service_type': package['type'],
                'rows': package['rows'],
                'total_debt': abs(total_balance) if not is_creditor else 0,
                'total_credit': abs(total_balance) if is_creditor else 0,
                'total_balance': total_balance,
                'period_range': period_range
            }

            # استفاده از سرویس ReportBro با یک شناسه قالب ثابت (مثلاً 'invoice_template')
            # می‌توانید این شناسه را از تنظیمات شرکت یا کاربر فعلی نیز دریافت کنید
            template_id = "invoice_template"
            try:
                pdf_bytes = render_pdf_via_reportbro(template_id, pdf_context)
            except Exception as e:
                logging.error(f"خطا در تولید PDF با ReportBro: {str(e)}")
                raise Exception(f"تولید PDF با سرویس طراحی قالب ممکن نیست: {str(e)}")

            pdf_path = os.path.join(final_dir, f"فاکتور {package['type']} {safe_payer} {safe_letter}.pdf")
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)

            result_files.append({
                'letter_number': current_letter,
                'service_type': package['type'],
                'file_name': f"فاکتور {package['type']} {safe_payer} {safe_letter}.pdf",
                'file_data': pdf_bytes,
                'disk_path': pdf_path
            })
        conn.close()
        return result_files
    except Exception as e:
        conn.close()
        raise e

# ==================== ENDPOINT های Flask ====================
@app.route('/generate', methods=['POST'])
def generate_final():
    data = request.get_json()
    req_id = data.get('request_id')
    if not req_id:
        return jsonify({'error': 'request_id required'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM approval_requests WHERE id = ? AND status = 'pending'", (req_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'Request not found or not pending'}), 404
    columns = [desc[0] for desc in cursor.description]
    req_dict = dict(zip(columns, row))
    try:
        files_info = generate_files_for_request(req_dict, FINAL_STORAGE)
        for f in files_info:
            cursor.execute("""
                INSERT INTO final_files (request_id, letter_number, service_type, file_name, file_path, file_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (req_id, f['letter_number'], f['service_type'], f['file_name'], f['disk_path'], pyodbc.Binary(f['file_data'])))
        cursor.execute("UPDATE approval_requests SET status = 'approved', approved_at = GETDATE() WHERE id = ?", (req_id,))
        conn.commit()
        return jsonify({'status': 'success', 'files_count': len(files_info)})
    except Exception as e:
        conn.rollback()
        error_msg = str(e)
        logging.error(f"خطا در generate برای request_id {req_id}: {traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500
    finally:
        conn.close()

@app.route('/download/<int:file_id>')
def download_file(file_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, file_data, file_name FROM final_files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'File not found'}), 404
    disk_path, blob_data, file_name = row
    if disk_path and os.path.exists(disk_path):
        try:
            return send_file(disk_path, as_attachment=True, download_name=file_name)
        except:
            pass
    if blob_data:
        return send_file(io.BytesIO(blob_data), as_attachment=True, download_name=file_name, mimetype='application/pdf')
    return jsonify({'error': 'No data available'}), 404

@app.route('/health')
def health():
    return jsonify({'status': 'alive'})

@app.route('/stats')
def stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM final_files")
        total_files = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM approval_requests WHERE status='approved'")
        total_approved = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM final_files WHERE last_accessed IS NOT NULL")
        total_downloads = cursor.fetchone()[0]
        return jsonify({'status':'running','total_files':total_files,'total_approved_requests':total_approved,'total_downloads':total_downloads})
    except Exception as e:
        return jsonify({'error':str(e)}),500
    finally:
        conn.close()

@app.route('/regenerate', methods=['POST'])
def regenerate():
    data = request.get_json()
    letter_number = data.get('letter_number')
    if not letter_number:
        return jsonify({'error': 'letter_number required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, payer_code, payer_name, service_data_json, flight_data_json, hotel_data_json, letter_date, period_range FROM approval_requests WHERE final_letter_number = ?", (letter_number,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'درخواست با این شماره نامه یافت نشد'}), 404

    req_id, payer_code, payer_name, service_json, flight_json, hotel_json, letter_date, period_range = row
    req_dict = {
        'id': req_id,
        'payer_code': payer_code,
        'payer_name': payer_name,
        'letter_number': letter_number,
        'letter_date': letter_date,
        'period_range': period_range,
        'service_data_json': service_json,
        'flight_data_json': flight_json,
        'hotel_data_json': hotel_json
    }
    try:
        files_info = generate_files_for_request(req_dict, FINAL_STORAGE)
        cursor.execute("DELETE FROM final_files WHERE letter_number = ?", (letter_number,))
        for f in files_info:
            cursor.execute("""
                INSERT INTO final_files (request_id, letter_number, service_type, file_name, file_path, file_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (req_id, f['letter_number'], f['service_type'], f['file_name'], f['disk_path'], pyodbc.Binary(f['file_data'])))
        conn.commit()
        cursor.execute("SELECT TOP 1 id FROM final_files WHERE letter_number = ?", (letter_number,))
        file_id = cursor.fetchone()[0]
        return jsonify({'status': 'success', 'file_id': file_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/reserve-letter', methods=['POST'])
def reserve_letter():
    data = request.get_json()
    payer_code = data.get('payer_code')
    if not payer_code:
        return jsonify({'error': 'payer_code required'}), 400

    conn = get_db_connection()
    try:
        year_two_digit = str(jdatetime.date.today().year)[-2:]
        next_num = get_next_letter_number(conn, payer_code, year_two_digit)
        update_letter_sequence(conn, payer_code, year_two_digit, next_num)
        format_str = "YYYY/CODE/NNNNN"
        today = jdatetime.date.today()
        letter_number = format_str.replace("YYYY", str(today.year)).replace("YY", year_two_digit).replace("CODE", payer_code).replace("CCC", payer_code.zfill(3)).replace("NUM", str(next_num)).replace("NNNNN", str(next_num).zfill(5))
        return jsonify({'status': 'success', 'letter_number': letter_number})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/release-letter', methods=['POST'])
def release_letter():
    data = request.get_json()
    letter_number = data.get('letter_number')
    if not letter_number:
        return jsonify({'error': 'letter_number required'}), 400

    match = re.search(r'(\d+)$', letter_number)
    if not match:
        return jsonify({'error': 'Invalid letter number format'}), 400
    num = int(match.group(1))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT payer_code FROM approval_requests WHERE letter_number = ? AND status IN ('pending', 'rejected')", (letter_number,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'No pending request found for this letter number'}), 404
    payer_code = row[0]
    year_two_digit = str(jdatetime.date.today().year)[-2:]

    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM available_letter_numbers WHERE payer_code = ? AND year = ? AND number = ?)
        INSERT INTO available_letter_numbers (payer_code, year, number) VALUES (?, ?, ?)
    """, (payer_code, year_two_digit, num, payer_code, year_two_digit, num))
    conn.commit()
    conn.close()
    return jsonify({'status': 'released', 'letter_number': letter_number})

# ==================== راه‌اندازی سرویس ====================
if __name__ == '__main__':
    # اطمینان از وجود پوشه‌های مورد نیاز
    os.makedirs(FINAL_STORAGE, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)