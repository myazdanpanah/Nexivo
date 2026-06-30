import os
import sys
import json
import io
from flask import Flask, request, send_file, jsonify, render_template_string
from werkzeug.utils import secure_filename
from reportbro import Report, ReportBroError
import logging

# -----------------------------
# 1. پیکربندی اولیه (Config)
# -----------------------------
# تعیین مسیر پایه، هم برای اجرای مستقیم و هم برای حالت exe
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_STORAGE = os.path.join(BASE_DIR, 'templates') # پوشه برای ذخیره فایل‌های قالب (.rpt)
ALLOWED_EXTENSIONS = {'rpt'}

# -----------------------------
# 2. راه‌اندازی Flask اپلیکیشن
# -----------------------------
app = Flask(__name__)

# پیکربندی آپلود فایل
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # حداکثر حجم 16 مگابایت
app.config['TEMPLATE_STORAGE'] = TEMPLATE_STORAGE
app.config['UPLOAD_FOLDER'] = TEMPLATE_STORAGE

os.makedirs(TEMPLATE_STORAGE, exist_ok=True)

# -----------------------------
# 3. هندلر صفحه اصلی (Static File Server)
# -----------------------------
# برای سرویس دهی فایل‌های reportbro.js و reportbro.css
# فرض می‌کنیم فایل‌ها در پوشه static/reportbro/ قرار دارند.
@app.route('/reportbro/<path:filename>')
def serve_reportbro_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static', 'reportbro'), filename)

# -----------------------------
# 4. صفحه دیزاینر (Designer Interface)
# -----------------------------
@app.route('/designer')
def designer():
    """
    صفحه اصلی ویرایشگر. فایل‌های HTML، CSS و JS مورد نیاز را لود می‌کند.
    برای عملکرد آفلاین، تمام فایل‌ها محلی (Local) هستند.
    """
    designer_html = """
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <title>طراح قالب حرفه‌ای فاکتور (ReportBro)</title>
        <link rel="stylesheet" href="/reportbro/reportbro.css">
        <style>
            body, html { margin: 0; padding: 0; height: 100%; direction: rtl; background: #f4f7f6; font-family: 'B Nazanin', Tahoma, sans-serif; }
            #toolbar {
                background: #fff;
                padding: 10px 20px;
                border-bottom: 1px solid #ddd;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .btn {
                background-color: #529e98;
                border: none;
                color: white;
                padding: 6px 14px;
                margin: 0 5px;
                border-radius: 4px;
                cursor: pointer;
                font-family: inherit;
                font-size: 14px;
                transition: 0.2s;
            }
            .btn:hover { background-color: #3d7873; }
            .btn-secondary { background-color: #6c757d; }
            .btn-secondary:hover { background-color: #5a6268; }
            #reportbro-container { height: calc(100% - 50px); }
        </style>
    </head>
    <body>
        <div id="toolbar">
            <button id="saveBtn" class="btn">💾 ذخیره قالب</button>
            <input type="file" id="loadFileInput" accept=".rpt" style="display: none;" />
            <button id="loadBtn" class="btn btn-secondary">📂 بارگذاری قالب (فایل)</button>
            <button id="exportBtn" class="btn">📥 دریافت JSON قالب</button>
            <label style="margin-right: 20px; font-size: 12px;">شناسه قالب:</label>
            <input type="text" id="templateId" value="default" style="width: 100px;">
            <button id="saveApiBtn" class="btn">💾 ذخیره روی سرور (API)</button>
            <button id="loadApiBtn" class="btn">📂 بارگذاری از سرور (API)</button>
        </div>
        <div id="reportbro-container"></div>

        <script src="/reportbro/reportbro.js"></script>
        <script>
            let rb = null;
            let currentTemplate = null;

            // مقداردهی اولیه دیزاینر
            rb = new ReportBro(document.getElementById('reportbro-container'));
            // بارگذاری یک قالب خالی ساده برای شروع
            const emptyTemplate = { "pages": [{ "content": [{"type": "text", "text": "قالب جدید..."}] }] };
            rb.loadTemplate(emptyTemplate);
            rb.onTemplateChange = (template) => { currentTemplate = template; };

            // ذخیره در فایل محلی
            document.getElementById('saveBtn').onclick = () => {
                const jsonStr = JSON.stringify(currentTemplate);
                const blob = new Blob([jsonStr], {type: "application/json"});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `template_${new Date().toISOString()}.rpt`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                alert("قالب با موفقیت ذخیره شد!");
            };
            // بارگذاری از فایل محلی
            document.getElementById('loadBtn').onclick = () => document.getElementById('loadFileInput').click();
            document.getElementById('loadFileInput').onchange = (event) => {
                const file = event.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const template = JSON.parse(e.target.result);
                        rb.loadTemplate(template);
                        currentTemplate = template;
                        alert("قالب با موفقیت بارگذاری شد!");
                    } catch(err) { alert("خطا در خواندن فایل: " + err.message); }
                };
                reader.readAsText(file);
            };
            // خروجی JSON
            document.getElementById('exportBtn').onclick = () => {
                const jsonStr = JSON.stringify(currentTemplate);
                const blob = new Blob([jsonStr], {type: "application/json"});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `template_backup_${Date.now()}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            };
            // ذخیره روی سرور (API)
            document.getElementById('saveApiBtn').onclick = async () => {
                const tid = document.getElementById('templateId').value;
                if (!tid) { alert("لطفاً شناسه قالب را وارد کنید."); return; }
                const res = await fetch('/save-template', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ id: tid, template: currentTemplate })
                });
                const data = await res.json();
                alert(data.status === 'ok' ? "قالب روی سرور ذخیره شد." : "خطا در ذخیره روی سرور");
            };
            // بارگذاری از سرور (API)
            document.getElementById('loadApiBtn').onclick = async () => {
                const tid = document.getElementById('templateId').value;
                if (!tid) { alert("لطفاً شناسه قالب را وارد کنید."); return; }
                const res = await fetch(`/load-template/${tid}`);
                if (res.status === 404) { alert("قالبی با این شناسه یافت نشد."); return; }
                const template = await res.json();
                rb.loadTemplate(template);
                currentTemplate = template;
                alert("قالب از سرور بارگذاری شد.");
            };
        </script>
    </body>
    </html>
    """
    return render_template_string(designer_html)

# -----------------------------
# 5. API ذخیره‌سازی قالب (ذخیره روی هارد دیسک)
# -----------------------------
@app.route('/save-template', methods=['POST'])
def save_template_endpoint():
    data = request.get_json()
    template_id = data.get('id')
    template_json = data.get('template')
    if not template_id or not template_json:
        return jsonify({'status': 'error', 'message': 'شناسه قالب و محتوای قالب الزامی است'}), 400
    try:
        # نام فایل امن با استفاده از شناسه
        filename = secure_filename(f"{template_id}.rpt")
        filepath = os.path.join(app.config['TEMPLATE_STORAGE'], filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template_json, f, ensure_ascii=False, indent=2)
        logging.info(f"Template saved: {filepath}")
        return jsonify({'status': 'ok', 'id': template_id})
    except Exception as e:
        logging.error(f"Error saving template: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# -----------------------------
# 6. API بارگذاری قالب (خواندن از هارد دیسک)
# -----------------------------
@app.route('/load-template/<template_id>', methods=['GET'])
def load_template_endpoint(template_id):
    filename = secure_filename(f"{template_id}.rpt")
    filepath = os.path.join(app.config['TEMPLATE_STORAGE'], filename)
    if not os.path.exists(filepath):
        return jsonify({'status': 'error', 'message': 'Template not found'}), 404
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            template_json = json.load(f)
        return jsonify(template_json)
    except Exception as e:
        logging.error(f"Error loading template: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# -----------------------------
# 7. تولید PDF نهایی از روی قالب و داده
# -----------------------------
@app.route('/render', methods=['POST'])
def render_report():
    data = request.get_json()
    template_json = data.get('template')
    report_data = data.get('data')  # داده‌های واقعی فاکتور مثل فروشنده، خریدار، لیست خدمات
    if not template_json or not report_data:
        return jsonify({'status': 'error', 'message': 'قالب و داده الزامی است'}), 400
    try:
        report = Report(report_definition=template_json, data=report_data)
        pdf_bytes = report.generate_pdf()
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='invoice_report.pdf'
        )
    except ReportBroError as e:
        logging.error(f"ReportBro generation error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'خطا در تولید گزارش: {str(e)}'}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# -----------------------------
# 8. راه‌اندازی سرویس
# -----------------------------
if __name__ == '__main__':
    # اطمینان از وجود پوشه ذخیره قالب‌ها
    os.makedirs(app.config['TEMPLATE_STORAGE'], exist_ok=True)
    # اجرا روی تمام interfaceها و پورت 5001 (برای جلوگیری از تداخل با سرویس قبلی)
    app.run(host='0.0.0.0', port=5001, debug=False)