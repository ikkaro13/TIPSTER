import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'import os' not in content[:200]:
        content = "import os\nfrom dotenv import load_dotenv\nload_dotenv()\n" + content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            print(f"Fixed {filepath}")
    else:
        print(f"Already fixed {filepath}")

fix_file('backend/api_football_engine.py')
fix_file('backend/nfl_lab.py')
