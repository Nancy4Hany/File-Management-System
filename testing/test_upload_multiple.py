import os
import requests
import threading

upload_url = "http://localhost:5000/upload"
files_to_upload = [
    ("file1.pdf", "C:/Users/nancy/Downloads/Nancy-Hany-Cover-Letter-laviar.pdf"),
    ("file2.pdf", "C:/Users/nancy/Downloads/Nancy-Hany-CV-1.pdf"),
    ("file3.pdf", "C:/Users/nancy/Downloads/Mostafa_s_Résumé.pdf"),
]

def upload_file(file_name, file_path):
    with open(file_path, 'rb') as file_data:
        form_data = {
            'title': file_name,
            'description': 'Testing multiple uploads',
        }
        response = requests.post(upload_url, files={'file': file_data}, data=form_data)
        if response.status_code == 200:
            print(f"Successfully uploaded {file_name}")
        else:
            print(f"Failed to upload {file_name}: {response.status_code} - {response.text}")
threads = []
for file_name, file_path in files_to_upload:
    t = threading.Thread(target=upload_file, args=(file_name, file_path))
    t.start()
    threads.append(t)
for t in threads:
    t.join()
