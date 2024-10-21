from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import fitz
import cv2
import pytesseract
import os
import re

UPLOAD_FOLDER = 'uploads/'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Eğer 'uploads' dizini yoksa oluşturur
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def pdf_to_images(pdf_path, output_folder):
    doc = fitz.open(pdf_path)
    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        pix = page.get_pixmap(dpi=300)  # DPI değerini artırdık
        image_path = os.path.join(output_folder, f"page_{page_number + 1}.jpg")
        pix.save(image_path)
        print(f"{image_path} kaydedildi.")

def ocr_on_images(directory):
    image_files = [file for file in os.listdir(directory) if file.lower().endswith(('.jpg', '.jpeg', '.png'))]
    last_output_image_path = None  # To store the last saved image path

    tc_id_pattern = r'\b\d{11}\b'  
    dob_pattern = r'\b\d{2}[./-]\d{2}[./-]\d{4}\b'

    for i, image_file in enumerate(image_files):
        image_path = os.path.join(directory, image_file)
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Görsel dosyası okunamadı veya bozuk.")

            # Görüntü ön işleme
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, thresh_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY)

            tessdata_dir_config = '--tessdata-dir "C:\\Program Files\\Tesseract-OCR\\tessdata_best" --psm 6'
            data = pytesseract.image_to_data(thresh_image, lang='tur', config=tessdata_dir_config, output_type=pytesseract.Output.DICT)

            n_boxes = len(data['text'])
            found_tc = False
            found_dob = False
            for j in range(n_boxes):
                if re.match(tc_id_pattern, data['text'][j]):
                    tc = data['text'][j]
                    last_digit = int(tc[-1])

                    if last_digit in [2, 4, 6, 8, 0]:  
                        print(f"Doğru TC Kimlik Numarası bulundu: {tc}")
                        found_tc = True

                        
                        x, y, w, h = data['left'][j], data['top'][j], data['width'][j], data['height'][j]
                        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)

                if re.match(dob_pattern, data['text'][j]):
                    dob = data['text'][j]
                    print(f"Doğum tarihi bulundu: {dob}")
                    found_dob = True

                    x, y, w, h = data['left'][j], data['top'][j], data['width'][j], data['height'][j]
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)
                    
            if found_tc or found_dob:
                output_image_path = os.path.join(directory, f"tc_boxed_{image_file}")
                cv2.imwrite(output_image_path, image)
                last_output_image_path = output_image_path  # Keep last saved image path
                
                # Dosyanın gerçekten kaydedilip kaydedilmediğini kontrol edelim
                if os.path.exists(last_output_image_path):
                    print(f"Görüntü başarıyla kaydedildi: {last_output_image_path}")
                else:
                    print(f"Görüntü kaydedilemedi! Dosya yolu: {last_output_image_path}")

            else:
                print(f"Görsel {i + 1}: {image_file} üzerinde TC Kimlik Numarası bulunamadı.")

        except Exception as e:
            print(f"Görsel {i + 1}: {image_file} okunamadı. Hata: {e}")
            print(f"Detaylı hata bilgisi: {type(e).__name__}: {e}")

    return last_output_image_path  # Return last saved image path

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about', methods=['GET', 'POST'])
def about():
    if request.method == 'POST':
        if 'myfile' not in request.files:
            return "Dosya yüklenmedi"

        file = request.files['myfile']
        if file.filename == '':
            return "Dosya seçilmedi"

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # PDF'den görsellere dönüştürme
            pdf_to_images(file_path, app.config['UPLOAD_FOLDER'])
            
            # Görsellerde OCR işlemi yapma ve son görüntü yolunu al
            last_output_image = ocr_on_images(app.config['UPLOAD_FOLDER'])
            
            # Sonuçları result.html'e gönder
            image_url = url_for('static', filename=last_output_image.replace('uploads/', ''))
            print(image_url)
            print(last_output_image)
            return f"""
            Dosya kaydedildi ve OCR işlemi tamamlandı: {file_path}<br>
            Path: {last_output_image}<br>
            <img src="{image_url}" alt="Kutucuklanmış Görüntü" style="max-width: 100%; height: auto;">
            """

    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
