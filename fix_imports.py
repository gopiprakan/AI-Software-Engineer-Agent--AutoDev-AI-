import os
import glob

path = r"c:\Users\GOPIPRAKAN\OneDrive\Desktop\AI Software Engineer Agent (AutoDev AI)\backend\app\agents\*.py"
for filepath in glob.glob(path):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = content.replace("from agents.", "from app.agents.")
    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")
