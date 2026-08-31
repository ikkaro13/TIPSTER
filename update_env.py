import re

with open('backend/.env', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'TELEGRAM_BOT_TOKEN=.*', 'TELEGRAM_BOT_TOKEN=8986944818:AAHtfx8xojPD0h2LNZwzSFweJ5OpKl67C7c', content)

with open('backend/.env', 'w', encoding='utf-8') as f:
    f.write(content)
