import os
import PyPDF2
# تم استبدال 'from googletrans import Translator'
from deep_translator import GoogleTranslator 
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from flask import Flask, render_template, request, send_file
import arabic_reshaper
from bidi.algorithm import get_display
import uuid 

# ----------------------------------------------------
# 1. إعدادات Flask والمسارات
# ----------------------------------------------------
app = Flask(__name__)
UPLOAD_FOLDER = 'temp_files' 
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ----------------------------------------------------
# 2. إعداد الخطوط (مهم للغة العربية)
# ----------------------------------------------------
# ❗❗ هام: تأكد أن هذا الاسم يطابق اسم ملف الخط الذي وضعته بجانب app.py (مثل Tahoma.ttf)
FONT_FILE = 'Amiri.ttf' 
FONT_NAME = 'ArabicFont'

try:
    # يجب أن يكون ملف الخط (مثل Arial.ttf) موجودًا بجوار app.py
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE)) 
except:
    print(f"⚠️ تنبيه: لم يتم العثور على ملف الخط '{FONT_FILE}'. سيتم استخدام خط افتراضي.")
    FONT_NAME = 'Helvetica'


# ----------------------------------------------------
# 3. وظيفة إنشاء PDF بالعربية (معالجة RTL)
# ----------------------------------------------------
def create_arabic_pdf(translated_text, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    c.setFont(FONT_NAME, 12)
    width, height = A4
    y = height - 50 

    for line in translated_text.split("\n"):
        if line.strip():
            # 1. معالجة الحروف المتصلة (Reshaping)
            reshaped_text = arabic_reshaper.reshape(line)
            # 2. قلب الاتجاه إلى اليمين لليسار (Bidi)
            bidi_text = get_display(reshaped_text)
            
            if y < 50:
                c.showPage()
                c.setFont(FONT_NAME, 12)
                y = height - 50
            
            # حساب عرض النص لتحديد موضع البداية من اليمين
            text_width = c.stringWidth(bidi_text, FONT_NAME, 12)
            x_position = width - 50 - text_width 
            
            c.drawString(x_position, y, bidi_text)
            y -= 20 

    c.save()


# ----------------------------------------------------
# 4. مسارات تطبيق الويب (Routing)
# ----------------------------------------------------

@app.route('/')
def index():
    # سيتم البحث عن index.html في مجلد templates/
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate_pdf():
    if 'file' not in request.files:
        return "لم يتم إرسال أي ملف", 400
    
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return "يرجى رفع ملف PDF صالح.", 400
    
    file_id = str(uuid.uuid4())
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_input.pdf")
    output_filename = "translated_" + file.filename.replace(".pdf", "_ar.pdf")
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_output.pdf")
    
    file.save(input_path)
    translated_text = ""
    
    try:
        reader = PyPDF2.PdfReader(input_path)
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                # **التعديل الهام هنا:** استخدام GoogleTranslator من deep_translator
                translated = GoogleTranslator(source='en', target='ar').translate(text)
                translated_text += translated + "\n\n"
        
        create_arabic_pdf(translated_text, output_path)
        
        # إرسال الملف المترجم للمستخدم
        return send_file(output_path, as_attachment=True, download_name=output_filename)

    except Exception as e:
        print(f"حدث خطأ أثناء المعالجة: {e}")
        # رسالة خطأ أكثر وضوحًا
        return f"حدث خطأ أثناء المعالجة: تأكد من أن ملف PDF يحتوي على نص يمكن قراءته وليس صورة. الخطأ: {e}", 500
    
    finally:
        # تنظيف الملفات المؤقتة
        if os.path.exists(input_path):
            os.remove(input_path)


# ... (باقي الكود)

# ... (الكود السابق)
if __name__ == '__main__':
    # port يجب أن يكون متغيراً محلياً، وليس جزءاً من app.run
    port = int(os.environ.get('PORT', 5000))
    # host='0.0.0.0' ضروري لكي يعمل التطبيق على أي خادم سحابي
    app.run(host='0.0.0.0', port=port, debug=True)