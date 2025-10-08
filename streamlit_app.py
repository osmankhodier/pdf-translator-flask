import streamlit as st
import PyPDF2
from deep_translator import GoogleTranslator
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import arabic_reshaper
from bidi.algorithm import get_display
import io
import os

# ----------------------------------------------------
# 1. إعداد الخطوط (مهم للغة العربية)
# ----------------------------------------------------
# تأكد أن ملف 'Amiri.ttf' موجود في مجلد المشروع الرئيسي
FONT_FILE = 'Amiri.ttf' 
FONT_NAME = 'ArabicFont'

try:
    # نقوم بتسجيل الخط مرة واحدة
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
except Exception as e:
    # سيظهر هذا الخطأ إذا لم يتم العثور على الخط، لكنه لن يوقف التطبيق في Streamlit
    st.error(f"⚠️ خطأ: فشل تسجيل الخط '{FONT_FILE}'. الرجاء التأكد من وجوده في المجلد.")


# ----------------------------------------------------
# 2. وظيفة إنشاء PDF بالعربية (معالجة RTL)
# ----------------------------------------------------
def create_arabic_pdf(translated_text, font_name, output_buffer):
    c = canvas.Canvas(output_buffer, pagesize=A4)
    c.setFont(font_name, 12)
    width, height = A4
    y = height - 50

    for line in translated_text.split("\n"):
        if line.strip():
            reshaped_text = arabic_reshaper.reshape(line)
            bidi_text = get_display(reshaped_text)

            if y < 50:
                c.showPage()
                c.setFont(font_name, 12)
                y = height - 50

            text_width = c.stringWidth(bidi_text, font_name, 12)
            x_position = width - 50 - text_width
            
            c.drawString(x_position, y, bidi_text)
            y -= 20

    c.save()
    return output_buffer.getvalue()

# ----------------------------------------------------
# 3. واجهة Streamlit (الواجهة الأمامية الجديدة)
# ----------------------------------------------------

st.set_page_config(page_title="مترجم PDF عربي", layout="centered")

st.title("مترجم ملفات PDF 📄 (إنجليزي ⬅ عربي)")
st.markdown("---")

uploaded_file = st.file_uploader(
    "يرجى رفع ملف PDF باللغة الإنجليزية:", 
    type="pdf", 
    accept_multiple_files=False
)

if uploaded_file is not None:
    st.info("⏳ جاري استخراج النص والترجمة. يرجى الانتظار...")
    
    # 1. استخلاص النص
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text_content = ""
        for page in reader.pages:
            text_content += page.extract_text() + "\n"
        
        if not text_content.strip():
            st.warning("الملف لا يحتوي على نص يمكن قراءته (ربما يكون صورة).")
            st.stop()
            
    except Exception as e:
        st.error(f"خطأ في قراءة الملف: {e}")
        st.stop()
    
    # 2. الترجمة
    with st.spinner('يتم الآن الترجمة...'):
        try:
            # الترجمة على دفعات لتجنب الأخطاء
            translated_text = GoogleTranslator(source='en', target='ar').translate(text_content)
        except Exception as e:
            st.error(f"خطأ في الترجمة: {e}")
            st.stop()

    st.success("✅ تم الانتهاء من الترجمة، جاري إنشاء ملف PDF.")

    # 3. إنشاء الملف الجديد
    try:
        pdf_buffer = io.BytesIO()
        pdf_bytes = create_arabic_pdf(translated_text, FONT_NAME, pdf_buffer)
        
        # 4. زر التنزيل
        st.download_button(
            label="🎉 تنزيل ملف PDF المترجم (العربية)",
            data=pdf_bytes,
            file_name=uploaded_file.name.replace(".pdf", "_AR.pdf"),
            mime="application/pdf"
        )
        
        st.markdown("---")
        st.success("يمكنك الآن تنزيل الملف ومشاركته!")
        
    except Exception as e:
        st.error(f"خطأ في إنشاء ملف PDF: {e}")
        st.warning("تأكد أنك وضعت ملف الخط 'Amiri.ttf' في المجلد الرئيسي.")