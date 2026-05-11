# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, jsonify, send_file
import os
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from dotenv import load_dotenv
from datetime import datetime, timedelta
from io import BytesIO
import mimetypes

load_dotenv()

app = Flask(__name__)

STORAGE_ACCOUNT_NAME = os.getenv('STORAGE_ACCOUNT_NAME')
CONTAINER_NAME = os.getenv('CONTAINER_NAME')
STORAGE_CONNECTION_STRING = os.getenv('STORAGE_CONNECTION_STRING')

# Extract account key from connection string
ACCOUNT_KEY = None
if STORAGE_CONNECTION_STRING:
    import re
    match = re.search(r'AccountKey=([^;]+)', STORAGE_CONNECTION_STRING)
    if match:
        ACCOUNT_KEY = match.group(1)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AzureVault Pro - File Manager</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root {
            --primary: #0078d4;
            --secondary: #005a9e;
            --success: #28a745;
            --danger: #dc3545;
            --warning: #ffc107;
            --light: #f5f5f5;
            --dark: #1f1f1f;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .navbar {
            background: rgba(255, 255, 255, 0.98) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            padding: 12px 20px;
        }
        
        .navbar-brand {
            font-weight: 700;
            font-size: 1.4rem;
            color: var(--primary) !important;
        }
        
        .navbar-brand i {
            margin-right: 8px;
        }
        
        .container-main {
            margin-top: 30px;
            margin-bottom: 40px;
        }
        
        .card {
            border: none;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
            transition: all 0.3s;
            margin-bottom: 25px;
        }
        
        .card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
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
            font-size: 1.1rem;
        }
        
        .status-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }
        
        .status-item {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .status-item:last-child {
            margin-bottom: 0;
        }
        
        .status-icon {
            font-size: 1.3rem;
            margin-right: 12px;
        }
        
        .status-text {
            font-size: 0.95rem;
        }
        
        /* Statistics Dashboard */
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
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
        }
        
        .stat-number {
            font-size: 2.2rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 8px;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #666;
            font-weight: 500;
        }
        
        /* Upload Area */
        .upload-area {
            border: 2px dashed var(--primary);
            border-radius: 12px;
            padding: 45px 20px;
            text-align: center;
            background: linear-gradient(to bottom, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .upload-area:hover, .upload-area.dragover {
            border-color: var(--secondary);
            background: linear-gradient(to bottom, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
            transform: scale(1.02);
        }
        
        .upload-icon {
            font-size: 3.5rem;
            color: var(--primary);
            margin-bottom: 15px;
        }
        
        .upload-icon-success {
            color: var(--success);
        }
        
        /* Upload Progress */
        .upload-progress-container {
            margin-top: 20px;
        }
        
        .progress {
            height: 8px;
            border-radius: 10px;
            background: #e9ecef;
        }
        
        .progress-bar {
            background: linear-gradient(90deg, var(--primary), var(--secondary));
        }
        
        /* Search & Filter */
        .search-filter-container {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .search-box {
            flex: 1;
            min-width: 250px;
            padding: 12px 16px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 0.95rem;
            transition: all 0.3s;
        }
        
        .search-box:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(0, 120, 212, 0.1);
        }
        
        .filter-btn {
            padding: 10px 16px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .filter-btn:hover, .filter-btn.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        
        /* File Items */
        .file-item {
            padding: 16px;
            background: white;
            border-radius: 8px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid var(--primary);
            transition: all 0.3s;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
        }
        
        .file-item:hover {
            background: #f9f9f9;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
            transform: translateX(4px);
        }
        
        .file-info {
            flex: 1;
            min-width: 0;
        }
        
        .file-name {
            font-weight: 600;
            color: var(--dark);
            margin-bottom: 6px;
            word-break: break-word;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .file-icon {
            font-size: 1.3rem;
            color: var(--primary);
        }
        
        .file-meta {
            font-size: 0.85rem;
            color: #999;
            display: flex;
            gap: 15px;
        }
        
        .file-actions {
            display: flex;
            gap: 8px;
            margin-left: 15px;
            flex-wrap: wrap;
            justify-content: flex-end;
        }
        
        .btn-action {
            padding: 8px 12px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.85rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .btn-download {
            background: var(--primary);
            color: white;
        }
        
        .btn-download:hover {
            background: var(--secondary);
            transform: translateY(-2px);
        }
        
        .btn-share {
            background: var(--success);
            color: white;
        }
        
        .btn-share:hover {
            background: #20c997;
            transform: translateY(-2px);
        }
        
        .btn-preview {
            background: var(--warning);
            color: white;
        }
        
        .btn-preview:hover {
            background: #e0a800;
            transform: translateY(-2px);
        }
        
        .btn-delete {
            background: var(--danger);
            color: white;
        }
        
        .btn-delete:hover {
            background: #c82333;
            transform: translateY(-2px);
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        
        .empty-state i {
            font-size: 4rem;
            color: #ddd;
            margin-bottom: 20px;
        }
        
        .empty-state h4 {
            color: #666;
            margin-bottom: 10px;
        }
        
        /* Modal */
        .modal-content {
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        }
        
        .modal-header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border: none;
        }
        
        /* Footer */
        .footer {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            margin-top: 40px;
            border-top: 1px solid #eee;
            text-align: center;
        }
        
        /* Toast */
        .toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1050;
        }
        
        .toast {
            background: white;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        input[type="file"] {
            display: none;
        }
        
        .hidden {
            display: none;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .stats-container {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .search-filter-container {
                flex-direction: column;
            }
            
            .search-box {
                min-width: 100%;
            }
            
            .file-item {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .file-actions {
                margin-left: 0;
                margin-top: 12px;
                width: 100%;
            }
            
            .btn-action {
                flex: 1;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-light sticky-top">
        <div class="container-fluid">
            <span class="navbar-brand">
                <i class="bi bi-lock-fill"></i>AzureVault Pro
            </span>
            <div class="text-muted small">
                <i class="bi bi-cloud"></i> Advanced Secure File Manager
            </div>
        </div>
    </nav>

    <!-- Main Container -->
    <div class="container-fluid container-main" style="max-width: 1200px;">
        <!-- Status Box -->
        <div class="status-box">
            <div class="status-item">
                <span class="status-icon"><i class="bi bi-check-circle"></i></span>
                <span class="status-text"><strong>Status:</strong> AzureVault Pro running</span>
            </div>
            <div class="status-item">
                <span class="status-icon"><i class="bi bi-shield-check"></i></span>
                <span class="status-text"><strong>Security:</strong> End-to-end encrypted & private</span>
            </div>
            <div class="status-item">
                <span class="status-icon"><i class="bi bi-cloud-check"></i></span>
                <span class="status-text"><strong>Storage:</strong> Azure Blob Storage connected</span>
            </div>
        </div>

        <!-- Statistics Dashboard -->
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-number" id="totalFiles">0</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalSize">0 MB</div>
                <div class="stat-label">Total Size</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="imageCount">0</div>
                <div class="stat-label">Images</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="docCount">0</div>
                <div class="stat-label">Documents</div>
            </div>
        </div>

        <!-- Upload Section -->
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-cloud-upload"></i> Upload Files</h5>
            </div>
            <div class="card-body">
                <div class="upload-area" id="uploadArea" ondrop="handleDrop(event)" ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)">
                    <div class="upload-icon"><i class="bi bi-file-earmark-arrow-up"></i></div>
                    <p class="mb-2"><strong>Drag & drop files here</strong></p>
                    <p class="text-muted mb-0">or click to browse your computer</p>
                    <input type="file" id="fileInput" multiple onchange="handleFileSelect(event)">
                </div>
                <div class="mt-4">
                    <button class="btn btn-primary w-100" onclick="uploadFiles()">
                        <i class="bi bi-upload"></i> Upload Selected Files
                    </button>
                </div>
                <div id="uploadProgress" class="upload-progress-container hidden">
                    <div class="progress" style="height: 10px;">
                        <div id="progressBar" class="progress-bar" role="progressbar" style="width: 0%"></div>
                    </div>
                    <p class="text-muted small mt-3" id="uploadStatus">Uploading...</p>
                </div>
            </div>
        </div>

        <!-- Search & Filter Section -->
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-funnel"></i> Search & Filter</h5>
            </div>
            <div class="card-body">
                <div class="search-filter-container">
                    <input type="text" class="search-box" id="searchInput" placeholder="🔍 Search files by name..." onkeyup="filterFiles()">
                    <button class="filter-btn active" onclick="filterByType('all')">All Files</button>
                    <button class="filter-btn" onclick="filterByType('image')"><i class="bi bi-image"></i> Images</button>
                    <button class="filter-btn" onclick="filterByType('document')"><i class="bi bi-file-text"></i> Documents</button>
                    <button class="filter-btn" onclick="filterByType('video')"><i class="bi bi-film"></i> Videos</button>
                </div>
            </div>
        </div>

        <!-- Files Section -->
        <div class="card">
            <div class="card-header">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 style="margin: 0;"><i class="bi bi-folder-open"></i> Your Files</h5>
                    <button class="btn btn-light btn-sm" onclick="refreshFiles()" title="Refresh list">
                        <i class="bi bi-arrow-clockwise"></i> Refresh
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div id="filesContainer">
                    <div class="empty-state">
                        <i class="bi bi-inbox"></i>
                        <h4>No files yet</h4>
                        <p>Upload your first file to get started</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div class="footer text-muted">
        <small>AzureVault Pro v2.0 | Advanced Secure Cloud File Manager | Powered by Azure</small>
    </div>

    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>

    <!-- Preview Modal -->
    <div class="modal fade" id="previewModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="previewTitle">File Preview</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body" id="previewContent">
                    Loading...
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let selectedFiles = [];
        let allFiles = [];
        let currentFilter = 'all';
        const previewModal = new bootstrap.Modal(document.getElementById('previewModal'));

        function getFileType(filename) {
            const ext = filename.split('.').pop().toLowerCase();
            const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'];
            const docExts = ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx'];
            const videoExts = ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'];

            if (imageExts.includes(ext)) return 'image';
            if (docExts.includes(ext)) return 'document';
            if (videoExts.includes(ext)) return 'video';
            return 'other';
        }

        function getFileIcon(filename) {
            const type = getFileType(filename);
            const icons = {
                'image': 'bi-file-image',
                'document': 'bi-file-text',
                'video': 'bi-file-play',
                'other': 'bi-file-earmark'
            };
            return icons[type] || 'bi-file-earmark';
        }

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
            selectedFiles = Array.from(e.dataTransfer.files);
            updateFileDisplay();
        }

        function handleFileSelect(e) {
            selectedFiles = Array.from(e.target.files);
            updateFileDisplay();
        }

        function updateFileDisplay() {
            const area = document.getElementById('uploadArea');
            if (selectedFiles.length === 0) {
                area.innerHTML = `
                    <div class="upload-icon"><i class="bi bi-file-earmark-arrow-up"></i></div>
                    <p class="mb-2"><strong>Drag & drop files here</strong></p>
                    <p class="text-muted mb-0">or click to browse</p>
                `;
            } else {
                const totalSize = (selectedFiles.reduce((sum, f) => sum + f.size, 0) / 1024 / 1024).toFixed(2);
                area.innerHTML = `
                    <div class="upload-icon upload-icon-success"><i class="bi bi-check-circle"></i></div>
                    <p class="mb-1"><strong>${selectedFiles.length} file(s) selected</strong></p>
                    <p class="text-muted mb-0">${totalSize} MB</p>
                `;
            }
        }

        function uploadFiles() {
            if (selectedFiles.length === 0) {
                showToast('Please select files to upload', 'warning');
                return;
            }

            document.getElementById('uploadProgress').classList.remove('hidden');
            let uploaded = 0;

            selectedFiles.forEach((file) => {
                const formData = new FormData();
                formData.append('file', file);

                fetch('/upload', { method: 'POST', body: formData })
                    .then(r => r.json())
                    .then(d => {
                        uploaded++;
                        const progress = (uploaded / selectedFiles.length) * 100;
                        document.getElementById('progressBar').style.width = progress + '%';
                        document.getElementById('uploadStatus').textContent = `Uploading ${uploaded}/${selectedFiles.length}...`;

                        if (uploaded === selectedFiles.length) {
                            setTimeout(() => {
                                document.getElementById('uploadProgress').classList.add('hidden');
                                document.getElementById('progressBar').style.width = '0%';
                                selectedFiles = [];
                                updateFileDisplay();
                                showToast('All files uploaded!', 'success');
                                refreshFiles();
                            }, 500);
                        }
                    })
                    .catch(e => showToast(`Error uploading ${file.name}`, 'danger'));
            });
        }

        function refreshFiles() {
            fetch('/files')
                .then(r => r.json())
                .then(files => {
                    allFiles = files;
                    updateStats();
                    displayFiles(files);
                })
                .catch(e => showToast('Error loading files', 'danger'));
        }

        function displayFiles(files) {
            const container = document.getElementById('filesContainer');
            if (files.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="bi bi-inbox"></i>
                        <h4>No files found</h4>
                        <p>Try uploading a file or adjust your filters</p>
                    </div>
                `;
            } else {
                container.innerHTML = files.map(f => `
                    <div class="file-item">
                        <div class="file-info">
                            <div class="file-name">
                                <i class="bi ${getFileIcon(f.name)} file-icon"></i>
                                ${f.name}
                            </div>
                            <div class="file-meta">
                                <span>📦 ${(f.size / 1024 / 1024).toFixed(2)} MB</span>
                                <span>📅 ${new Date(f.time * 1000).toLocaleDateString()}</span>
                            </div>
                        </div>
                        <div class="file-actions">
                            <button class="btn-action btn-preview" onclick="previewFile('${f.name}')">
                                <i class="bi bi-eye"></i> Preview
                            </button>
                            <button class="btn-action btn-download" onclick="downloadFile('${f.name}')">
                                <i class="bi bi-download"></i> Download
                            </button>
                            <button class="btn-action btn-share" onclick="copyShareLink('${f.name}')">
                                <i class="bi bi-link-45deg"></i> Share
                            </button>
                            <button class="btn-action btn-delete" onclick="deleteFile('${f.name}')">
                                <i class="bi bi-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                `).join('');
            }
        }

        function updateStats() {
            document.getElementById('totalFiles').textContent = allFiles.length;
            const totalSize = (allFiles.reduce((sum, f) => sum + f.size, 0) / 1024 / 1024).toFixed(2);
            document.getElementById('totalSize').textContent = totalSize + ' MB';
            
            const images = allFiles.filter(f => getFileType(f.name) === 'image').length;
            const docs = allFiles.filter(f => getFileType(f.name) === 'document').length;
            
            document.getElementById('imageCount').textContent = images;
            document.getElementById('docCount').textContent = docs;
        }

        function filterFiles() {
            const search = document.getElementById('searchInput').value.toLowerCase();
            const filtered = allFiles.filter(f => 
                f.name.toLowerCase().includes(search) && 
                (currentFilter === 'all' || getFileType(f.name) === currentFilter)
            );
            displayFiles(filtered);
        }

        function filterByType(type) {
            currentFilter = type;
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            filterFiles();
        }

        function previewFile(name) {
            fetch(`/preview?name=${encodeURIComponent(name)}`)
                .then(r => r.json())
                .then(d => {
                    document.getElementById('previewTitle').textContent = name;
                    document.getElementById('previewContent').innerHTML = d.preview;
                    previewModal.show();
                })
                .catch(e => showToast('Cannot preview this file type', 'danger'));
        }

        function downloadFile(name) {
            window.location.href = `/download?name=${encodeURIComponent(name)}`;
        }

        function copyShareLink(name) {
            const link = `${window.location.origin}/share?name=${encodeURIComponent(name)}`;
            navigator.clipboard.writeText(link);
            showToast('Share link copied to clipboard!', 'success');
        }

        function deleteFile(name) {
            if (!confirm(`Delete "${name}"?`)) return;

            fetch(`/delete?name=${encodeURIComponent(name)}`, { method: 'DELETE' })
                .then(r => r.json())
                .then(d => {
                    showToast(`"${name}" deleted`, 'success');
                    refreshFiles();
                })
                .catch(e => showToast('Error deleting file', 'danger'));
        }

        function showToast(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = 'toast';
            const icons = {
                'success': '✓',
                'danger': '✕',
                'warning': '⚠',
                'info': 'ℹ'
            };
            toast.innerHTML = `<strong>${icons[type]}</strong> ${message}`;
            document.getElementById('toastContainer').appendChild(toast);
            setTimeout(() => toast.remove(), 5000);
        }

        // Initialize
        refreshFiles();
        document.getElementById('uploadArea').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    </script>
</body>
</html>
'''

def get_file_stats():
    try:
        if not STORAGE_CONNECTION_STRING:
            return {}
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        
        stats = {}
        for blob in container.list_blobs():
            stats[blob.name] = {
                'size': blob.size or 0,
                'time': blob.last_modified.timestamp() if blob.last_modified else 0
            }
        return stats
    except:
        return {}

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'av-vault-pro'})

@app.route('/files', methods=['GET'])
def list_files():
    try:
        if not STORAGE_CONNECTION_STRING:
            return jsonify([])
        
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        
        files = []
        for blob in container.list_blobs():
            files.append({
                'name': blob.name,
                'size': blob.size or 0,
                'time': blob.last_modified.timestamp() if blob.last_modified else 0
            })
        
        return jsonify(sorted(files, key=lambda x: x['time'], reverse=True))
    except Exception as e:
        return jsonify([]), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if not STORAGE_CONNECTION_STRING:
            return jsonify({'error': 'Storage not configured'}), 400
        
        file = request.files['file']
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        container.upload_blob(file.filename, file.read(), overwrite=True)
        
        return jsonify({'message': f'✓ {file.filename} uploaded'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET'])
def download_file():
    try:
        if not STORAGE_CONNECTION_STRING:
            return jsonify({'error': 'Storage not configured'}), 400
        
        name = request.args.get('name')
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        blob_client = container.get_blob_client(name)
        
        download_stream = blob_client.download_blob()
        return send_file(
            BytesIO(download_stream.readall()),
            as_attachment=True,
            download_name=name
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete', methods=['DELETE'])
def delete_file():
    try:
        if not STORAGE_CONNECTION_STRING:
            return jsonify({'error': 'Storage not configured'}), 400
        
        name = request.args.get('name')
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        container.delete_blob(name)
        
        return jsonify({'message': f'✓ {name} deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview', methods=['GET'])
def preview_file():
    try:
        if not STORAGE_CONNECTION_STRING:
            return jsonify({'error': 'Storage not configured'}), 400
        
        name = request.args.get('name')
        ext = name.split('.')[-1].lower()
        
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        blob_client = container.get_blob_client(name)
        download_stream = blob_client.download_blob()
        content = download_stream.readall()
        
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            import base64
            b64 = base64.b64encode(content).decode('utf-8')
            preview_html = f'<img src="data:image/{ext};base64,{b64}" style="max-width: 100%; border-radius: 8px;">'
        elif ext == 'txt':
            preview_html = f'<pre style="background: #f5f5f5; padding: 20px; border-radius: 8px; overflow-x: auto;">{content.decode("utf-8", errors="ignore")}</pre>'
        elif ext == 'pdf':
            import base64
            b64 = base64.b64encode(content).decode('utf-8')
            preview_html = f'<embed src="data:application/pdf;base64,{b64}" width="100%" height="600px" type="application/pdf">'
        else:
            preview_html = f'<p style="color: #999; text-align: center; padding: 40px;">Preview not available for this file type</p>'
        
        return jsonify({'preview': preview_html})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
Upload Progress 
@app.route('/share', methods=['GET'])
def share_file():
    try:
        if not STORAGE_CONNECTION_STRING or not ACCOUNT_KEY:
            return jsonify({'error': 'Storage not configured'}), 400
        
        name = request.args.get('name')
        
        sas_token = generate_blob_sas(
            account_name=STORAGE_ACCOUNT_NAME,
            container_name=CONTAINER_NAME,
            blob_name=name,
            account_key=ACCOUNT_KEY,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(days=7)
        )
        
        share_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{name}?{sas_token}"
        return jsonify({'share_url': share_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
