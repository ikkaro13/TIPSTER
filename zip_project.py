import os
import shutil
import zipfile

def zip_project(source_dir, output_filename, exclude_dirs, exclude_files):
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Exclude directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not any(ex in os.path.join(root, d) for ex in exclude_dirs)]
            
            for file in files:
                if file in exclude_files:
                    continue
                # Exclude specific extensions or patterns if needed
                if file.endswith('.pyc') or file.startswith('.env'):
                    if file == '.env.example':
                        pass # keep this one
                    else:
                        continue
                
                # Exclude zip itself
                if file == os.path.basename(output_filename):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)

if __name__ == '__main__':
    source_dir = '.'
    output_filename = 'ATHENA_Audit_Export.zip'
    exclude_dirs = ['.git', '.venv', '__pycache__', 'node_modules', '.next', '.gemini']
    exclude_files = ['.env', 'tipster.db', 'portfolio_db.json', 'tree_output.txt', 'tree2.txt', 'tree3.txt']
    
    zip_project(source_dir, output_filename, exclude_dirs, exclude_files)
    print(f"Project successfully zipped into {output_filename}")
