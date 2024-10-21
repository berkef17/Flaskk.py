from flask import Flask, request, jsonify
import fitz
import cv2
import pytesseract
import os
import re



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

    tc_id_pattern = r'\b\d{11}\b'  # TC Kimlik Numarası için regex deseni (11 haneli)
    dob_pattern = r'\b\d{2}[./-]\d{2}[./-]\d{4}\b'

    for i, image_file in enumerate(image_files):
        image_path = os.path.join(directory, image_file)
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Görsel dosyasi okunamadi veya bozuk.")

            # Görüntü ön işleme
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, thresh_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY)

            tessdata_dir_config = '--tessdata-dir "C:\\Program Files\\Tesseract-OCR\\tessdata_best" --psm 6'
            data = pytesseract.image_to_data(thresh_image, lang='tur', config=tessdata_dir_config, output_type=pytesseract.Output.DICT)

            n_boxes = len(data['text'])
            found_tc = False
            for j in range(n_boxes):
                if re.match(tc_id_pattern, data['text'][j]):
                    tc = data['text'][j]
                    last_digit = int(tc[-1])

                    if last_digit in [2, 4, 6, 8, 0]:  # Çift sayılar kontrol ediliyor
                        print(f"Doğru TC Kimlik Numarasi bulundu: {tc}")
                        found_tc = True

                        # Koordinatları alalım ve kutu çizelim
                        x, y, w, h = data['left'][j], data['top'][j], data['width'][j], data['height'][j]
                        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0,0), -1)

                if re.match(dob_pattern, data['text'][j]):
                    dob = data['text'][j]
                    print(f"Doğum tarihi bulundu: {dob}")
                    found_dob = True

                    x, y, w, h = data['left'][j], data['top'][j], data['width'][j], data['height'][j]
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)
                        # Güncellenmiş görseli kaydet
                    if found_tc or found_dob:
                        output_image_path = os.path.join(directory, f"tc_boxed_{image_file}")
                        cv2.imwrite(output_image_path, image)
                        print(f"Kutucuk içine alinmiş görüntü kaydedildi: {output_image_path}")


            else:
                print(f"Görsel {i + 1}: {image_file} üzerinde TC Kimlik Numarasi bulunamadi.")

        except Exception as e:
            print(f"Görsel {i + 1}: {image_file} okunamadi. Hata: {e}")
            print(f"Detayli hata bilgisi: {type(e).__name__}: {e}")


pdf_path = "C:\\Users\\Berke Filiz\\Desktop\\dosyacik\\ailem.pdf"
output_folder = "C:\\Users\\Berke Filiz\\Desktop\\dosyacik\\"

pdf_to_images(pdf_path, output_folder)
ocr_on_images(output_folder)
