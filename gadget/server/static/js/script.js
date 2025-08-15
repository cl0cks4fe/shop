document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const fileName = document.getElementById('fileName');
    const uploadArea = document.querySelector('.upload-area');
    const uploadBtn = document.getElementById('uploadBtn');

    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            fileName.textContent = `→ ${e.target.files[0].name}`;
            fileName.style.display = 'block';
            uploadBtn.disabled = false;
        }
    });

    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.style.borderColor = '#555';
        uploadArea.style.backgroundColor = '#f0f0f0';
    });

    uploadArea.addEventListener('dragleave', function() {
        uploadArea.style.borderColor = '#ccc';
        uploadArea.style.backgroundColor = '#fafafa';
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.style.borderColor = '#ccc';
        uploadArea.style.backgroundColor = '#fafafa';

        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            fileName.textContent = `→ ${e.dataTransfer.files[0].name}`;
            fileName.style.display = 'block';
            uploadBtn.disabled = false;
        }
    });

    document.getElementById('uploadForm').addEventListener('submit', function() {
        uploadBtn.textContent = 'UPLOADING...';
        uploadBtn.disabled = true;
    });
});
