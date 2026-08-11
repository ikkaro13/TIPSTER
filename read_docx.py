import subprocess
import sys

try:
    import docx2txt
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "docx2txt"])
    import docx2txt

print("=== ATHENA_Recalibracion_LIVE_v1.1.docx ===")
try:
    text1 = docx2txt.process(r"D:\Work\ANTIGRAVITY\TIPSTER\ATHENA_Recalibracion_LIVE_v1.1.docx")
    print(text1)
except Exception as e:
    print(f"Error reading doc 1: {e}")

print("\n======================================================\n")

print("=== ATHENA_Experimental_v1.1-R1_Protocolo_Maestro_PREMATCH_LIVE.docx ===")
try:
    text2 = docx2txt.process(r"D:\Work\ANTIGRAVITY\TIPSTER\ATHENA_Experimental_v1.1-R1_Protocolo_Maestro_PREMATCH_LIVE.docx")
    print(text2)
except Exception as e:
    print(f"Error reading doc 2: {e}")
