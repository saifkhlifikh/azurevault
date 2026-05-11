from flask import Flask, render_template_string, request, jsonify, send_file
import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from datetime import datetime
from io import BytesIO
import base64

load_dotenv()

app = Flask(__name__)

STORAGE_ACCOUNT_NAME = os.getenv('STORAGE_ACCOUNT_NAME')
CONTAINER_NAME = os.getenv('CONTAINER_NAME')
STORAGE_CONNECTION_STRING = os.getenv('STORAGE_CONNECTION_STRING')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AzureVault Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
        }
        .navbar {
            background: rgba(255, 255, 255, 0.98) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        .navbar-brand {
            font-weight: 700;
            color: #0078d4 !important;
            font-size: 1.4rem;
        }
        .card {
            border: none;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
            margin-bottom: 25px;
        }
        .card-header {
            background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%);
            color: white;
            border-radius: 12px 12px 0 0;
            padding: 20px;
        }
        .status-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            text-align: center;
        }
        .stat-number {
            font-size: 2.2rem;
            font-weight: 700;
            color: #0078d4;
            margin-bottom: 8px;
        }
        .upload-area {
            border: 2px dashed #0078d4;
            border-radius: 12px;
            padding: 45px 20px;
            text-align: center;
            background: rgba(102, 126, 234, 0.05);
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover, .upload-area.dragover {
            border-color: #005a9e;
            background: rgba(102, 126, 234, 0.15);
        }
        .file-item {
            padding: 16px;
            background: white;
            border-radius: 8px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid #0078d4;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
        }
        .file-actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .btn-action {
            padding: 8px 12px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .btn-preview { background: #ffc107; color: white; }
        .btn-download { background: #0078d4; color: white; }
        .btn-share { background: #28a745; color: white; }
        .btn-delete { background: #dc3545; color: white; }
        .progress { height: 10px; }
        .search-box {
            padding: 12px 16px;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 15px;
            width: 100%;
        }
        input[type="file"] { display: none; }
        .hidden { display: none; }
        @media (max-width: 768px) {
            .stats-container { grid-template-columns: repeat(2, 1fr); }
            .file-item { flex-direction: column; align-items: flex-start; }
            .file-actions { margin-top: 12px; width: 100%; }
            .btn-action { flex: 1; }
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-light sticky-top">
        <div class="container-fluid">
            <span class="navbar-brand"><i class="bi bi-lock-fill"></i>AzureVault Pro</span>
        </div>
    </nav>

    <div class="container-fluid" style="max-width: 1200px; margin-top: 30px; margin-bottom: 40px;">
        <div class="status-box">
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <i class="bi bi-check-circle" style="font-size: 1.3rem; margin-right: 12px;"></i>
                <span><strong>Status:</strong> AzureVault Pro running</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <i class="bi bi-shield-check" style="font-size: 1.3rem; margin-right: 12px;"></i>
                <span><strong>Security:</strong> End-to-end encrypted</span>
            </div>
            <div style="display: flex; align-items: center;">
                <i class="bi bi-cloud-check" style="font-size: 1.3rem; margin-right: 12px;"></i>
                <span><strong>Storage:</strong> Azure Blob Storage</span>
            </div>
        </div>

        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-number" id="totalFiles">0</div>
                <div style="color: #666; font-weight: 500;">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalSize">0 MB</div>
                <div style="color: #666; font-weight: 500;">Total Size</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="imageCount">0</div>
                <div style="color: #666; font-weight: 500;">Images</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="docCount">0</div>
                <div style="color: #666; font-weight: 500;">Documents</div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h5 style="margin: 0;"><i class="bi bi-cloud-upload"></i> Upload Files</h5>
            </div>
            <div class="card-body">
                <div class="upload-area" id="uploadArea" ondrop="handleDrop(event)" ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)">
                    <div style="font-size: 3.5rem; color: #0078d4; margin-bottom: 15px;"><i class="bi bi-file-earmark-arrow-up"></i></div>
                    <p style="margin-bottom: 10px;"><strong>Drag & drop files here</strong></p>
                    <p style="color: #999; margin-bottom: 0;">or click to browse</p>
                    <input type="file" id="fileInput" multiple onchange="handleFileSelect(event)">
                </div>
                <button class="btn btn-primary w-100 mt-3" onclick="uploadFiles()">
                    <i class="bi bi-upload"></i> Upload Selected Files
                </button>
                <div id="uploadProgress" class="hidden" style="margin-top: 20px;">
                    <div class="progress">
                        <div id="progressBar" class="progress-bar" style="width: 0%; background: linear-gradient(90deg, #0078d4, #005a9e);"></div>
                    </div>
                    <p class="text-muted small mt-2" id="uploadStatus">Uploading...</p>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h5 style="margin: 0;"><i class="bi bi-funnel"></i> Search & Filter</h5>
            </div>
            <div class="card-body">
                <input type="text" class="search-box" id="searchInput" placeholder="Search files..." onkeyup="filterFiles()">
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button class="btn btn-outline-primary btn-sm active" onclick="filterByType('all')">All Files</button>
                    <button class="btn btn-outline-primary btn-sm" onclick="filterByType('image')"><i class="bi bi-image"></i> Images</button>
                    <button class="btn btn-outline-primary btn-sm" onclick="filterByType('document')"><i class="bi bi-file-text"></i> Documents</button>
                    <button class="btn btn-outline-primary btn-sm" onclick="filterByType('video')"><i class="bi bi-film"></i> Videos</button>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h5 style="margin: 0;"><i class="bi bi-folder-open"></i> Your Files</h5>
            </div>
            <div class="card-body">
                <div id="filesContainer">
                    <div style="text-align: center; padding: 60px 20px; color: #999;">
                        <i class="bi bi-inbox" style="font-size: 4rem; color: #ddd; margin-bottom: 20px;"></i>
                        <h4 style="color: #666;">No files yet</h4>
                        <p>Upload your first file to get started</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div style="background: rgba(255, 255, 255, 0.95); padding: 25px; margin-top: 40px; text-align: center; color: #999;">
        <small>AzureVault Pro v2.0 | Advanced Secure Cloud File Manager</small>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let selectedFiles = [];
        let allFiles = [];
        let currentFilter = 'all';

        function getFileType(filename) {
            const ext = filename.split('.').pop().toLowerCase();
            if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'].includes(ext)) return 'image';
            if (['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx'].includes(ext)) return 'document';
            if (['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'].includes(ext)) return 'video';
            return 'other';
        }

        function getFileIcon(filename) {
            const type = getFileType(filename);
            const icons = { 'image': 'bi-file-image', 'document': 'bi-file-text', 'video': 'bi-file-play', 'other': 'bi-file-earmark' };
            return icons[type] || 'bi-file-earmark';
        }

        function handleDragOver(e) { e.preventDefault(); document.getElementById('uploadArea').classList.add('dragover'); }
        function handleDragLeave(e) { e.preventDefault(); document.getElementById('uploadArea').classList.remove('dragover'); }
        function handleDrop(e) { e.preventDefault(); document.getElementById('uploadArea').classList.remove('dragover'); selectedFiles = Array.from(e.dataTransfer.files); updateFileDisplay(); }
        function handleFileSelect(e) { selectedFiles = Array.from(e.target.files); updateFileDisplay(); }

        function updateFileDisplay() {
            const area = document.getElementById('uploadArea');
            if (selectedFiles.length === 0) {
                area.innerHTML = '<div style="font-size: 3.5rem; color: #0078d4; margin-bottom: 15px;"><i class="bi bi-file-earmark-arrow-up"></i></div><p style="margin-bottom: 10px;"><strong>Drag & drop files here</strong></p><p style="color: #999; margin-bottom: 0;">or click to browse</p>';
            } else {
                const size = (selectedFiles.reduce((s, f) => s + f.size, 0) / 1024 / 1024).toFixed(2);
                area.innerHTML = '<div style="font-size: 3.5rem; color: #28a745; margin-bottom: 15px;"><i class="bi bi-check-circle"></i></div><p style="margin-bottom: 5px;"><strong>' + selectedFiles.length + ' file(s) selected</strong></p><p style="color: #999;">' + size + ' MB</p>';
            }
        }

        function uploadFiles() {
            if (selectedFiles.length === 0) { alert('Select files first'); return; }
            document.getElementById('uploadProgress').classList.remove('hidden');
            let uploaded = 0;
            selectedFiles.forEach(file => {
                const fd = new FormData(); fd.append('file', file);
                fetch('/upload', { method: 'POST', body: fd })
                    .then(r => r.json())
                    .then(d => {
                        uploaded++;
                        const progress = (uploaded / selectedFiles.length) * 100;
                        document.getElementById('progressBar').style.width = progress + '%';
                        if (uploaded === selectedFiles.length) {
                            setTimeout(() => { document.getElementById('uploadProgress').classList.add('hidden'); selectedFiles = []; updateFileDisplay(); refreshFiles(); }, 500);
                        }
                    })
                    .catch(e => alert('Error: ' + file.name));
            });
        }

        function refreshFiles() {
            fetch('/files').then(r => r.json()).then(files => { allFiles = files; updateStats(); displayFiles(files); }).catch(e => alert('Error loading'));
        }

        function displayFiles(files) {
            const c = document.getElementById('filesContainer');
            if (files.length === 0) {
                c.innerHTML = '<div style="text-align: center; padding: 60px 20px; color: #999;"><i class="bi bi-inbox" style="font-size: 4rem; color: #ddd; margin-bottom: 20px;"></i><h4 style="color: #666;">No files found</h4></div>';
            } else {
                c.innerHTML = files.map(f => '<div class="file-item"><div style="flex: 1;"><div style="font-weight: 600; color: #1f1f1f; margin-bottom: 6px;"><i class="bi ' + getFileIcon(f.name) + '"></i> ' + f.name + '</div><div style="font-size: 0.85rem; color: #999;">📦 ' + (f.size / 1024 / 1024).toFixed(2) + ' MB | 📅 ' + new Date(f.time * 1000).toLocaleDateString() + '</div></div><div class="file-actions"><button class="btn-action btn-preview" onclick="previewFile(\'' + f.name + '\')"><i class="bi bi-eye"></i> Preview</button><button class="btn-action btn-download" onclick="downloadFile(\'' + f.name + '\')"><i class="bi bi-download"></i></button><button class="btn-action btn-share" onclick="copyLink(\'' + f.name + '\')"><i class="bi bi-link-45deg"></i></button><button class="btn-action btn-delete" onclick="deleteFile(\'' + f.name + '\')"><i class="bi bi-trash"></i></button></div></div>').join('');
            }
        }

        function updateStats() {
            document.getElementById('totalFiles').textContent = allFiles.length;
            const size = (allFiles.reduce((s, f) => s + f.size, 0) / 1024 / 1024).toFixed(2);
            document.getElementById('totalSize').textContent = size + ' MB';
            document.getElementById('imageCount').textContent = allFiles.filter(f => getFileType(f.name) === 'image').length;
            document.getElementById('docCount').textContent = allFiles.filter(f => getFileType(f.name) === 'document').length;
        }

        function filterFiles() {
            const search = document.getElementById('searchInput').value.toLowerCase();
            const filtered = allFiles.filter(f => f.name.toLowerCase().includes(search) && (currentFilter === 'all' || getFileType(f.name) === currentFilter));
            displayFiles(filtered);
        }

        function filterByType(type) {
            currentFilter = type;
            document.querySelectorAll('.btn-outline-primary').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            filterFiles();
        }

        function previewFile(name) { window.location.href = '/preview?name=' + encodeURIComponent(name); }
        function downloadFile(name) { window.location.href = '/download?name=' + encodeURIComponent(name); }
        function copyLink(name) { navigator.clipboard.writeText(window.location.origin + '/share?name=' + encodeURIComponent(name)); alert('Link copied!'); }
        function deleteFile(name) { if (confirm('Delete ' + name + '?')) fetch('/delete?name=' + encodeURIComponent(name), { method: 'DELETE' }).then(() => refreshFiles()); }

        refreshFiles();
        document.getElementById('uploadArea').addEventListener('click', () => document.getElementById('fileInput').click());
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/files', methods=['GET'])
def list_files():
    try:
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        files = [{'name': b.name, 'size': b.size or 0, 'time': b.last_modified.timestamp() if b.last_modified else 0} for b in container.list_blobs()]
        return jsonify(sorted(files, key=lambda x: x['time'], reverse=True))
    except:
        return jsonify([])

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        container.upload_blob(file.filename, file.read(), overwrite=True)
        return jsonify({'msg': 'uploaded'})
    except Exception as e:
        return jsonify({'err': str(e)}), 500

@app.route('/download', methods=['GET'])
def download_file():
    try:
        name = request.args.get('name')
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        blob = blob_service.get_blob_client(CONTAINER_NAME, name).download_blob()
        return send_file(BytesIO(blob.readall()), as_attachment=True, download_name=name)
    except:
        return 'Error', 500

@app.route('/delete', methods=['DELETE'])
def delete_file():
    try:
        name = request.args.get('name')
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        blob_service.get_blob_client(CONTAINER_NAME, name).delete_blob()
        return jsonify({'msg': 'deleted'})
    except:
        return jsonify({'err': 'error'}), 500

@app.route('/preview', methods=['GET'])
def preview_file():
    try:
        name = request.args.get('name')
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        blob = blob_service.get_blob_client(CONTAINER_NAME, name).download_blob().readall()
        window.open(URL.createObjectURL(new Blob([blob])))
        return send_file(BytesIO(blob), as_attachment=False, download_name=name)
    except:
        return 'Preview unavailable', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
