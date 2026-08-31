import os
import re

files_with_verify = [
    'backend/api_football_engine.py',
    'backend/main.py',
    'backend/nfl_lab.py',
    'backend/telegram_bot.py'
]

for file in files_with_verify:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        with open(file, 'r', encoding='latin-1') as f:
            content = f.read()
            
    if 'VERIFY_SSL =' not in content:
        content = re.sub(
            r'(import os\n(from dotenv import load_dotenv\nload_dotenv\(\)\n)?)', 
            r'\1VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"\n', 
            content, 
            count=1
        )
        
    content = content.replace('verify=False', 'verify=VERIFY_SSL')
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
print('Done!')
