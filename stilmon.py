import xml.etree.ElementTree as ET
import requests
import os
from pathlib import Path
import uuid
from ftplib import FTP
import tempfile

def fetch_xml_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching XML from URL: {e}")
        return None

def convert_xml(input_xml):
    try:
        # Parse input XML
        root = ET.fromstring(input_xml)
        # Create output XML root
        output_root = ET.Element("products")
        
        # Copy script elements
        for script in root.findall("script"):
            output_root.append(script)
        
        # Process each product
        for product in root.findall("product"):
            out_product = ET.SubElement(output_root, "product")
            
            # Map basic product fields
            out_product.set("id", product.find("code").text)
            out_product.set("productCode", product.find("ws_code").text)
            barcode = product.find("barcode").text or ""
            ET.SubElement(out_product, "barcode").text = barcode
            ET.SubElement(out_product, "main_category").text = product.find("cat1name").text
            ET.SubElement(out_product, "top_category").text = product.find("cat2name").text
            ET.SubElement(out_product, "sub_category").text = product.find("cat2name").text
            ET.SubElement(out_product, "sub_category_")
            ET.SubElement(out_product, "categoryID").text = product.find("cat2code").text
            ET.SubElement(out_product, "category").text = product.find("category_path").text
            ET.SubElement(out_product, "active").text = "1"
            ET.SubElement(out_product, "brandID").text = "0"  # Assuming default brand ID
            ET.SubElement(out_product, "brand").text = product.find("brand").text
            ET.SubElement(out_product, "name").text = product.find("name").text
            ET.SubElement(out_product, "description").text = product.find("detail").text
            ET.SubElement(out_product, "listPrice").text = product.find("price_list_vat_included").text
            ET.SubElement(out_product, "price").text = product.find("price_special_vat_included").text
            ET.SubElement(out_product, "tax").text = str(float(product.find("vat").text) / 100)
            ET.SubElement(out_product, "currency").text = "TRY" if product.find("currency").text == "TL" else product.find("currency").text
            ET.SubElement(out_product, "desi").text = product.find("desi").text
            ET.SubElement(out_product, "quantity").text = product.find("stock").text
            
            # Process images
            images = product.find("images")
            for i, img in enumerate(images.findall("img_item"), 1):
                ET.SubElement(out_product, f"image{i}").text = img.text
            
            # Process variants
            variants = ET.SubElement(out_product, "variants")
            for subproduct in product.find("subproducts").findall("subproduct"):
                variant = ET.SubElement(variants, "variant")
                ET.SubElement(variant, "name1").text = "Renk"
                ET.SubElement(variant, "value1").text = subproduct.find("type1").text
                ET.SubElement(variant, "name2").text = "Beden"
                ET.SubElement(variant, "value2").text = subproduct.find("type2").text
                ET.SubElement(variant, "quantity").text = subproduct.find("stock").text
                ET.SubElement(variant, "barcode").text = subproduct.find("barcode").text or ""
        
        # Convert to string with proper XML declaration
        output_xml = ET.tostring(output_root, encoding="unicode", method="xml")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + output_xml
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None

def upload_to_ftp(xml_content, ftp_config):
    """
    Upload XML content to FTP server
    
    ftp_config should be a dictionary with:
    - host: FTP server hostname
    - username: FTP username
    - password: FTP password
    - remote_path: Remote directory path (optional, defaults to '/')
    - filename: Remote filename (optional, defaults to 'stilmondeneme.xml')
    """
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(xml_content)
            temp_file_path = temp_file.name
        
        # Connect to FTP server
        ftp = FTP()
        ftp.connect(ftp_config['host'])
        ftp.login(ftp_config['username'], ftp_config['password'])
        
        # Change to remote directory if specified
        remote_path = ftp_config.get('remote_path', '/')
        if remote_path != '/':
            try:
                ftp.cwd(remote_path)
            except:
                print(f"Warning: Could not change to directory {remote_path}")
        
        # Upload file
        filename = ftp_config.get('filename', 'stilmondeneme.xml')
        with open(temp_file_path, 'rb') as file:
            ftp.storbinary(f'STOR {filename}', file)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        # Close FTP connection
        ftp.quit()
        
        print(f"File uploaded successfully to FTP server: {filename}")
        return True
        
    except Exception as e:
        print(f"Error uploading to FTP: {e}")
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        return False

def save_to_desktop(xml_content, filename="stilmondeneme.xml"):
    desktop = Path.home() / "Desktop"
    output_path = desktop / filename
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
        print(f"File saved successfully to {output_path}")
    except Exception as e:
        print(f"Error saving file: {e}")

def main():
    url = "https://stilimon.com/xml/?R=9412&K=21c1&AltUrun=1&TamLink=1&Dislink=1&Imgs=1&start=0&limit=99999&pass=Z9K0aQM9"
    input_xml = fetch_xml_from_url(url)
    if input_xml:
        output_xml = convert_xml(input_xml)
        if output_xml:
            # FTP configuration - Bu bilgileri kendi hosting bilgilerinizle değiştirin
            ftp_config = {
                'host': 'ftp.eterella.com',  # FTP sunucu adresi
                'username': 'windamdx',     # FTP kullanıcı adı
                'password': 'c_bJ!-PGMwG57#Hx',     # FTP şifresi
                'remote_path': '/public_html/yasinxml/',  # Uzak dizin (isteğe bağlı)
                'filename': 'stilmondeneme.xml'  # Uzak dosya adı
            }
            
            # FTP'ye yükle
            if upload_to_ftp(output_xml, ftp_config):
                print("XML dosyası başarıyla hostinge yüklendi!")
            else:
                print("FTP yükleme başarısız oldu, yerel olarak kaydediliyor...")
                save_to_desktop(output_xml)

if __name__ == "__main__":
    main()