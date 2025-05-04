import easyocr
 
# Create an OCR reader object
reader = easyocr.Reader(['en'])
 
# Read text from an image
result = reader.readtext('logo.jpg')

 
# Print the extracted text
for detection in result:
    print(detection[1])