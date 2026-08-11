import zipfile
import xml.etree.ElementTree as ET

def read_docx(path):
    try:
        document = zipfile.ZipFile(path)
        xml_content = document.read('word/document.xml')
        document.close()
        tree = ET.XML(xml_content)
        
        paragraphs = []
        for paragraph in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = [node.text
                     for node in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
                     if node.text]
            if texts:
                paragraphs.append(''.join(texts))
        return '\n'.join(paragraphs)
    except Exception as e:
        return f"Error: {e}"

print("=== ATHENA_Recalibracion_LIVE_v1.1.docx ===")
print(read_docx(r"D:\Work\ANTIGRAVITY\TIPSTER\ATHENA_Recalibracion_LIVE_v1.1.docx"))
print("\n======================================================\n")
print("=== ATHENA_Experimental_v1.1-R1_Protocolo_Maestro_PREMATCH_LIVE.docx ===")
print(read_docx(r"D:\Work\ANTIGRAVITY\TIPSTER\ATHENA_Experimental_v1.1-R1_Protocolo_Maestro_PREMATCH_LIVE.docx"))
