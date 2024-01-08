from flask import Flask, render_template, request, send_file, redirect
import os
import fitz  # PyMuPDF
from datetime import datetime, timedelta
import threading

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

file_deletion_schedule = {}

def compress_pdf(input_path, output_path):
    pdf = fitz.open(input_path)
    pdf.save(output_path, garbage=10, deflate=True)
    pdf.close()

def merge_pdfs(input_paths, output_path):
    merger = PdfMerger()

    for path in input_paths:
        merger.append(path)

    merger.write(output_path)
    merger.close()

def delete_files(files):
    for file in files:
        os.remove(file)

def schedule_file_deletion(files):
    deletion_time = datetime.utcnow() + timedelta(seconds=30)
    file_deletion_schedule[deletion_time] = files
    threading.Timer((deletion_time - datetime.utcnow()).total_seconds(), delete_files, args=[files]).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compress', methods=['POST'])
def compress():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        output_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'compressed_' + file.filename)
        compress_pdf(filename, output_filename)

        response = send_file(output_filename, as_attachment=True)

        schedule_file_deletion([filename, output_filename])

        return response

@app.route('/merge', methods=['POST'])
def merge():
    files = request.files.getlist('files[]')

    if not files or any(file.filename == '' for file in files):
        return redirect(request.url)

    filenames = []

    for file in files:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        filenames.append(filename)

    output_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'merged.pdf')
    merge_pdfs(filenames, output_filename)

    response = send_file(output_filename, as_attachment=True)

    schedule_file_deletion(filenames + [output_filename])

    return response

if __name__ == '__main__':
    app.run(debug=True)
