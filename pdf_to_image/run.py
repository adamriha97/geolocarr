import fitz
import PIL.Image
import io

import tabula

def get_images(pdf_file_path):
    pdf = fitz.open(pdf_file_path)
    counter = 1
    for i in range(len(pdf)):
        page = pdf[i]
        images = page.get_images()
        for image in images:
            base_img = pdf.extract_image(image[0])
            image_data = base_img['image']
            img = PIL.Image.open(io.BytesIO(image_data))
            extension = base_img['ext']
            img.save(open(f'pdf_to_image/get_images/image{counter}.{extension}', 'wb'))
            counter += 1

def convert_pdf_to_images(pdf_file_path):
    pdf = fitz.open(pdf_file_path) 
    for page in pdf: 
        pix = page.get_pixmap(matrix=fitz.Identity, dpi=300, 
                              colorspace=fitz.csRGB, clip=None, alpha=False, annots=True) 
        pix.save("pdf_to_image/convert_pdf_to_images/pdfimage%i.jpg" % page.number)  # save file 

def tables_from_pdf(pdf_file_path):
    tables = tabula.read_pdf(pdf_file_path, pages='all')
    print(tables)


convert_pdf_to_images('pdfs/C555018250.pdf') # C555018250 C555005528