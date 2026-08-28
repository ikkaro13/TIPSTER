with open('backend/analytics.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'dc_1x' in content:
        print("dc_1x IS IN analytics.py!")
    else:
        print("dc_1x IS NOT IN analytics.py")
