# SSH into your VM
ssh -i ~/.ssh/id_rsa vm@40.89.132.89

# Stop the current Flask app (Ctrl+C if running)

# Go to your app directory
cd ~/AzureVault

# Activate virtual environment
source venv/bin/activate

# Backup the old app
cp app.py app.py.backup

# Create the new modern app
cat > app.py << 'EOF'
# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, jsonify
import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)

STORAGE_ACCOUNT_NAME = os.getenv('STORAGE_ACCOUNT_NAME')
CONTAINER_NAME = os.getenv('CONTAINER_NAME')
STORAGE_CONNECTION_STRING = os.getenv('STORAGE_CONNECTION_STRING')

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AzureVault - Secure File Manager</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root {
            --primary: #0078d4;
            --secondary: #005a9e;
            --light: #f5f5f5;
            --dark: #1f1f1f;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .navbar {
            background: rgba(255, 255, 255, 0.95) !important;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
            color: var(--primary) !important;
        }
        
        .navbar-brand i {
            margin-right: 8px;
        }
        
        .container-main {
            margin-top: 40px;
            margin-bottom: 40px;
        }
        
        .card {
            border: none;
            border-radius: 12px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        .card-header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border: none;
            border-radius: 12px 12px 0 0;
            padding: 20px;
        }
        
        .card-header h5 {
            margin: 0;
            font-weight: 600;
        }
        
        .btn-primary {
            background: var(--primary);
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .btn-primary:hover {
            background: var(--secondary);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 120, 212, 0.3);
        }
        
        .btn-danger {
            background: #dc3545;
            border: none;
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 0.9rem;
        }
        
        .btn-danger:hover {
            background: #c82333;
        }
        
        .upload-area {
            border: 2px dashed var(--primary);
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            background: linear-gradient(to bottom, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .upload-area:hover {
            border-color: var(--secondary);
            background: linear-gradient(to bottom, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        }
        
        .upload-area.dragover {
            border-color: var(--secondary);
            background: linear-gradient(to bottom, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
        }
        
        .upload-icon {
            font-size: 3rem;
            color: var(--primary);
            margin-bottom: 10px;
        }
        
        .file-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .file-item {
            padding: 15px;
            background: #f9f9f9;
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid var(--primary);
            transition: all 0.3s;
        }
        
        .file-item:hover {
            background: #f0f0f0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .file-info {
            flex: 1;
        }
        
        .file-name {
            font-weight: 500;
            color: var(--dark);
            margin-bottom: 5px;
        }
        
        .file-meta {
            font-size: 0.85rem;
            color: #666;
        }
        
        .status-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .status-item:last-child {
            margin-bottom: 0;
        }
        
        .status-icon {
            font-size: 1.2rem;
            margin-right: 10px;
        }
        
        .status-text {
            font-size: 0.95rem;
        }
        
        .footer {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            margin-top: 40px;
            border-top: 1px solid #eee;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #666;
        }
        
        .empty-state i {
            font-size: 3rem;
            color: #ccc;
            margin-bottom: 20px;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-light sticky-top">
        <div class="container-fluid">
            <span class="navbar-brand">
                <i class="bi bi-lock-fill"></i>AzureVault
            </span>
            <div class="text-muted small">
                <i class="bi bi-cloud"></i> Secure File Manager on Azure
            </div>
        </div>
    </nav>

    <div class="container container-main" style="max-width: 900px;">
        <div class="status-box">
            <div class="status-item">
                <span class="status-icon"><i class="bi bi-check-circle"></i></span>
                <span class="status-text"><strong>Status:</strong> Flask running on Azure VM</span>
            </div>
            <div class="status-item">
                <span class="status-icon"><i class="bi bi-lock"></i></span>
                <span class="status-text"><strong>Security:</strong> Private IP with Bastion access</span>
            </div>
            <div class="status-item">
                <span class="status-icon"><i class="bi bi-cloud-check"></i></span>
                <span class="status-text"><strong>Storage:</strong> Connected to Azure Blob Storage</span>
            </div>
        </div>

        <div class="card mb-4">
            <div class="card-header">
                <h5><i class="bi bi-cloud-upload"></i> Upload Files</h5>
            </div>
            <div class="card-body">
                <div class="upload-area" id="uploadArea" ondrop="handleDrop(event)" ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)">
                    <div class="upload-icon"><i class="bi bi-file-earmark-arrow-up"></i></div>
                    <p class="mb-2"><strong>Drag & drop files here</strong></p>
                    <p class="text-muted mb-0">or click to browse</p>
                    <input type="file" id="fileInput" multiple onchange="handleFileSelect(event)">
                </div>
                <div class="mt-3">
                    <button class="btn btn-primary w-100" onclick="uploadFiles()">
                        <i class="bi bi-upload"></i> Upload Selected Files
                    </button>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 style="margin: 0;"><i class="bi bi-folder-open"></i> Your Files</h5>
                    <button class="btn btn-light btn-sm" onclick="refreshFiles()" title="Refresh list">
                        <i class="bi bi-arrow-clockwise"></i>
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div id="filesContainer">
                    <div class="empty-state">
                        <i class="bi bi-inbox"></i>
                        <p>No files yet. Upload one to get started!</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="footer text-center text-muted">
        <small>AzureVault v1.0 | Secure cloud file manager powered by Azure</small>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let selectedFiles = [];

        function handleDragOver(e) {
            e.preventDefault();
            document.getElementById('uploadArea').classList.add('dragover');
        }

        function handleDragLeave(e) {
            e.preventDefault();
            document.getElementById('uploadArea').classList.remove('dragover');
        }

        function handleDrop(e) {
            e.preventDefault();
            document.getElementById('uploadArea').classList.remove('dragover');
            const files = e.dataTransfer.files;
            selectedFiles = Array.from(files);
            updateFileDisplay();
        }

        function handleFileSelect(e) {
            selectedFiles = Array.from(e.target.files);
            updateFileDisplay();
        }

        function updateFileDisplay() {
            if (selectedFiles.length === 0) {
                document.getElementById('uploadArea').innerHTML = `
                    <div class="upload-icon"><i class="bi bi-file-earmark-arrow-up"></i></div>
                    <p class="mb-2"><strong>Drag & drop files here</strong></p>
                    <p class="text-muted mb-0">or click to browse</p>
                `;
            } else {
                document.getElementById('uploadArea').innerHTML = `
                    <div class="upload-icon"><i class="bi bi-check-circle" style="color: #28a745;"></i></div>
                    <p class="mb-0"><strong>${selectedFiles.length} file(s) selected</strong></p>
                `;
            }
        }

        function uploadFiles() {
            if (selectedFiles.length === 0) {
                alert('Please select files to upload');
                return;
            }

            let uploaded = 0;
            selectedFiles.forEach((file, index) => {
                const formData = new FormData();
                formData.append('file', file);

                fetch('/upload', { method: 'POST', body: formData })
                    .then(r => r.json())
                    .then(d => {
                        uploaded++;
                        if (uploaded === selectedFiles.length) {
                            selectedFiles = [];
                            updateFileDisplay();
                            refreshFiles();
                        }
                    })
                    .catch(e => alert('Error uploading ' + file.name));
            });
        }

        function refreshFiles() {
            fetch('/files')
                .then(r => r.json())
                .then(files => {
                    const container = document.getElementById('filesContainer');
                    if (files.length === 0) {
                        container.innerHTML = `
                            <div class="empty-state">
                                <i class="bi bi-inbox"></i>
                                <p>No files yet. Upload one to get started!</p>
                            </div>
                        `;
                    } else {
                        container.innerHTML = '<ul class="file-list">' + files.map(f => `
                            <li class="file-item">
                                <div class="file-info">
                                    <div class="file-name"><i class="bi bi-file-earmark"></i> ${f}</div>
                                    <div class="file-meta">Stored in Azure Blob Storage</div>
                                </div>
                                <button class="btn btn-danger btn-sm" onclick="deleteFile('${f}')">
                                    <i class="bi bi-trash"></i> Delete
                                </button>
                            </li>
                        `).join('') + '</ul>';
                    }
                })
                .catch(e => alert('Error loading files'));
        }

        function deleteFile(name) {
            if (!confirm('Are you sure you want to delete ' + name + '?')) return;

            fetch('/delete?name=' + encodeURIComponent(name), { method: 'DELETE' })
                .then(r => r.json())
                .then(d => refreshFiles())
                .catch(e => alert('Error deleting file'));
        }

        refreshFiles();
        document.getElementById('uploadArea').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'av-vault'})

@app.route('/files', methods=['GET'])
def list_files():
    try:
        if not STORAGE_CONNECTION_STRING:
            return jsonify([])
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        blobs = [blob.name for blob in container.list_blobs()]
        return jsonify(sorted(blobs, reverse=True))
    except Exception as e:
        return jsonify([]), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if not STORAGE_CONNECTION_STRING:
            return jsonify({'message': 'Storage not configured'}), 400
        file = request.files['file']
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        container.upload_blob(file.filename, file.read(), overwrite=True)
        return jsonify({'message': f'✓ {file.filename} uploaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete', methods=['DELETE'])
def delete_file():
    try:
        if not STORAGE_CONNECTION_STRING:
            return jsonify({'message': 'Storage not configured'}), 400
        name = request.args.get('name')
        if not name:
            return jsonify({'error': 'No file name provided'}), 400
        
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        container.delete_blob(name)
        return jsonify({'message': f'✓ {name} deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF

# Restart Flask
python3 app.py
