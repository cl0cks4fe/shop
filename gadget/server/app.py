from flask import Flask, request, render_template, redirect, url_for
import os
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')
ALLOWED_EXTENSIONS = {'prg', 'nc', 'txt', 'p-1'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file selected', 400

        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return 'Invalid file type', 400

        # Save the uploaded file
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Call your bash script to update USB gadget
        try:
            subprocess.run([os.path.join(os.getcwd(), 'scripts/transfer.sh')'], check=True)
            return redirect(url_for('upload_file', success=True))
        except subprocess.CalledProcessError:
            return 'Update failed', 500

    success = request.args.get('success')
    return render_template('index.html', success=success)

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)
