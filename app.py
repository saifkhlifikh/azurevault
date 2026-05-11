# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, jsonify, send_file
import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from datetime import datetime
from io import BytesIO
import json
import re

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
    <title>AzureVault Notes - Markdown Note Manager</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/highlight.js@11.8.0/styles/atom-one-dark.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked@11.0.0/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.6/dist/purify.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highlight.js@11.8.0/highlight.min.js"></script>
    <style>
        :root {
            --primary: #0078d4;
            --secondary: #005a9e;
            --success: #28a745;
            --danger: #dc3545;
            --light: #f5f5f5;
            --dark: #1f1f1f;
            --sidebar-bg: #f8f9fa;
            --border: #e0e0e0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: #fafafa;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        
        .navbar {
            background: white;
            border-bottom: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            padding: 12px 20px;
        }
        
        .navbar-brand {
            font-weight: 700;
            font-size: 1.3rem;
            color: var(--primary) !important;
            margin: 0;
        }
        
        .navbar-brand i {
            margin-right: 8px;
        }
        
        .main-container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        
        .sidebar {
            width: 300px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border);
            overflow-y: auto;
            padding: 15px;
            display: flex;
            flex-direction: column;
        }
        
        .sidebar-header {
            margin-bottom: 20px;
        }
        
        .search-box {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.9rem;
            margin-bottom: 15px;
        }
        
        .sidebar-section {
            margin-bottom: 25px;
        }
        
        .sidebar-section-title {
            font-size: 0.75rem;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 10px;
            letter-spacing: 0.5px;
        }
        
        .note-item {
            padding: 12px;
            margin-bottom: 8px;
            background: white;
            border-radius: 6px;
            border-left: 3px solid var(--primary);
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid #e0e0e0;
            font-size: 0.9rem;
        }
        
        .note-item:hover {
            background: #f0f0f0;
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .note-item.active {
            background: var(--primary);
            color: white;
            border-left-color: var(--secondary);
        }
        
        .note-item-title {
            font-weight: 500;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .note-item-date {
            font-size: 0.75rem;
            opacity: 0.7;
        }
        
        .tag {
            display: inline-block;
            background: #e3f2fd;
            color: var(--primary);
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            margin: 2px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .tag:hover {
            background: var(--primary);
            color: white;
        }
        
        .tag.active {
            background: var(--primary);
            color: white;
        }
        
        .editor-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .editor-header {
            background: white;
            padding: 15px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .editor-title-input {
            font-size: 1.5rem;
            font-weight: 600;
            border: none;
            outline: none;
            background: transparent;
            flex: 1;
            margin-right: 20px;
        }
        
        .editor-buttons {
            display: flex;
            gap: 10px;
        }
        
        .btn-sm {
            padding: 6px 12px;
            font-size: 0.85rem;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary-sm {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary-sm:hover {
            background: var(--secondary);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 120, 212, 0.3);
        }
        
        .btn-secondary-sm {
            background: #6c757d;
            color: white;
        }
        
        .btn-danger-sm {
            background: var(--danger);
            color: white;
        }
        
        .editor-content {
            display: flex;
            flex: 1;
            overflow: hidden;
            gap: 0;
        }
        
        .editor-pane {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            border-right: 1px solid var(--border);
        }
        
        .markdown-editor {
            flex: 1;
            padding: 20px;
            font-family: 'Fira Code', 'Courier New', monospace;
            font-size: 0.95rem;
            border: none;
            outline: none;
            background: white;
            resize: none;
            line-height: 1.6;
        }
        
        .preview-pane {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: white;
        }
        
        .markdown-preview {
            font-size: 1rem;
            line-height: 1.8;
            color: #333;
        }
        
        .markdown-preview h1 {
            font-size: 2rem;
            margin: 24px 0 16px 0;
            font-weight: 700;
            border-bottom: 2px solid var(--primary);
            padding-bottom: 8px;
        }
        
        .markdown-preview h2 {
            font-size: 1.5rem;
            margin: 20px 0 12px 0;
            font-weight: 600;
            color: var(--primary);
        }
        
        .markdown-preview h3 {
            font-size: 1.2rem;
            margin: 16px 0 8px 0;
            font-weight: 600;
        }
        
        .markdown-preview p {
            margin: 12px 0;
        }
        
        .markdown-preview ul, .markdown-preview ol {
            margin: 12px 0 12px 20px;
        }
        
        .markdown-preview li {
            margin: 6px 0;
        }
        
        .markdown-preview code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Fira Code', monospace;
            font-size: 0.9rem;
        }
        
        .markdown-preview pre {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 12px 0;
        }
        
        .markdown-preview pre code {
            background: none;
            padding: 0;
            color: inherit;
        }
        
        .markdown-preview blockquote {
            border-left: 4px solid var(--primary);
            padding-left: 16px;
            margin: 12px 0;
            color: #666;
            font-style: italic;
        }
        
        .markdown-preview table {
            border-collapse: collapse;
            width: 100%;
            margin: 12px 0;
        }
        
        .markdown-preview th, .markdown-preview td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        
        .markdown-preview th {
            background: #f4f4f4;
            font-weight: 600;
        }
        
        .markdown-preview a {
            color: var(--primary);
            text-decoration: none;
        }
        
        .markdown-preview a:hover {
            text-decoration: underline;
        }
        
        .empty-state {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100%;
            color: #999;
            text-align: center;
        }
        
        .empty-state i {
            font-size: 4rem;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        .tab-bar {
            display: flex;
            gap: 10px;
            padding: 15px 20px;
            border-bottom: 1px solid var(--border);
            background: #f9f9f9;
        }
        
        .tab {
            padding: 8px 16px;
            background: white;
            border: 1px solid var(--border);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9rem;
        }
        
        .tab:hover {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        
        .tab.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        
        .stats-bar {
            display: flex;
            gap: 15px;
            padding: 10px 20px;
            background: #f9f9f9;
            border-top: 1px solid var(--border);
            font-size: 0.85rem;
            color: #666;
        }
        
        .stat-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
        }
        
        @media (max-width: 1024px) {
            .editor-content {
                flex-direction: column;
            }
            
            .editor-pane {
                border-right: none;
                border-bottom: 1px solid var(--border);
            }
        }
        
        @media (max-width: 768px) {
            .sidebar {
                width: 250px;
            }
        }
        
        .create-note-btn {
            width: 100%;
            padding: 12px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            margin-bottom: 15px;
            transition: all 0.3s;
        }
        
        .create-note-btn:hover {
            background: var(--secondary);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <span class="navbar-brand">
            <i class="bi bi-book"></i>AzureVault Notes
        </span>
    </nav>

    <!-- Main Layout -->
    <div class="main-container">
        <!-- Sidebar -->
        <div class="sidebar">
            <button class="create-note-btn" onclick="createNewNote()">
                <i class="bi bi-plus-lg"></i> New Note
            </button>
            
            <input type="text" class="search-box" id="searchInput" placeholder="Search notes..." onkeyup="filterNotes()">
            
            <div class="sidebar-section">
                <div class="sidebar-section-title">Tags</div>
                <div id="tagsContainer"></div>
            </div>
            
            <div class="sidebar-section" style="flex: 1; overflow-y: auto;">
                <div class="sidebar-section-title">Recent Notes</div>
                <div id="notesList"></div>
            </div>
        </div>

        <!-- Editor -->
        <div class="editor-container">
            <!-- Empty State -->
            <div id="emptyState" class="empty-state" style="display: flex;">
                <i class="bi bi-file-text"></i>
                <h3>Welcome to AzureVault Notes</h3>
                <p>Create a new note or select one from the sidebar</p>
            </div>

            <!-- Editor Content -->
            <div id="editorContent" style="display: none; flex: 1; overflow: hidden;">
                <!-- Editor Header -->
                <div class="editor-header">
                    <input type="text" class="editor-title-input" id="noteTitle" placeholder="Note Title">
                    <div class="editor-buttons">
                        <button class="btn-sm btn-primary-sm" onclick="saveNote()">
                            <i class="bi bi-check-lg"></i> Save
                        </button>
                        <button class="btn-sm btn-secondary-sm" onclick="exportNote()">
                            <i class="bi bi-download"></i> Export
                        </button>
                        <button class="btn-sm btn-danger-sm" onclick="deleteCurrentNote()">
                            <i class="bi bi-trash"></i> Delete
                        </button>
                    </div>
                </div>

                <!-- Tab Bar -->
                <div class="tab-bar">
                    <button class="tab active" onclick="switchView('split')">
                        <i class="bi bi-layout-split"></i> Split View
                    </button>
                    <button class="tab" onclick="switchView('edit')">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    <button class="tab" onclick="switchView('preview')">
                        <i class="bi bi-eye"></i> Preview
                    </button>
                </div>

                <!-- Editor Content Area -->
                <div class="editor-content">
                    <!-- Editor Pane -->
                    <div class="editor-pane" id="editorPane">
                        <textarea class="markdown-editor" id="markdownEditor" placeholder="Write your note in Markdown..."></textarea>
                    </div>

                    <!-- Preview Pane -->
                    <div class="preview-pane" id="previewPane">
                        <div class="markdown-preview" id="markdownPreview"></div>
                    </div>
                </div>

                <!-- Stats Bar -->
                <div class="stats-bar">
                    <div class="stat-item">
                        <i class="bi bi-type"></i>
                        <span id="charCount">0</span> characters
                    </div>
                    <div class="stat-item">
                        <i class="bi bi-card-text"></i>
                        <span id="wordCount">0</span> words
                    </div>
                    <div class="stat-item">
                        <i class="bi bi-clock"></i>
                        Last saved: <span id="lastSaved">never</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentNote = null;
        let allNotes = [];
        let currentView = 'split';

        // Initialize
        loadNotes();
        
        document.getElementById('markdownEditor').addEventListener('input', () => {
            updatePreview();
            updateStats();
        });

        function createNewNote() {
            const title = prompt('Note Title:', 'Untitled Note');
            if (!title) return;

            const note = {
                id: Date.now().toString(),
                title: title,
                content: '# ' + title + '\\n\\nStart typing...',
                tags: [],
                created: new Date().toISOString()
            };

            currentNote = note;
            allNotes.unshift(note);
            displayEditor();
            showNotes();
            showToast('Note created', 'success');
        }

        function loadNotes() {
            fetch('/notes')
                .then(r => r.json())
                .then(notes => {
                    allNotes = notes;
                    showNotes();
                    showTags();
                })
                .catch(e => showToast('Error loading notes', 'danger'));
        }

        function showNotes() {
            const container = document.getElementById('notesList');
            if (allNotes.length === 0) {
                container.innerHTML = '<p style="color: #999; font-size: 0.9rem;">No notes yet</p>';
                return;
            }

            container.innerHTML = allNotes.map(note => `
                <div class="note-item ${currentNote && currentNote.id === note.id ? 'active' : ''}" onclick="selectNote('${note.id}')">
                    <div class="note-item-title">${note.title}</div>
                    <div class="note-item-date">${new Date(note.created).toLocaleDateString()}</div>
                </div>
            `).join('');
        }

        function showTags() {
            const allTags = [...new Set(allNotes.flatMap(n => n.tags || []))];
            const container = document.getElementById('tagsContainer');
            
            if (allTags.length === 0) {
                container.innerHTML = '<p style="color: #999; font-size: 0.9rem;">No tags</p>';
                return;
            }

            container.innerHTML = allTags.map(tag => `
                <span class="tag" onclick="filterByTag('${tag}')">#${tag}</span>
            `).join('');
        }

        function selectNote(id) {
            const note = allNotes.find(n => n.id === id);
            if (!note) return;

            if (currentNote && currentNote.content !== document.getElementById('markdownEditor').value) {
                if (!confirm('Save changes to current note?')) return;
                saveNote();
            }

            currentNote = note;
            document.getElementById('noteTitle').value = note.title;
            document.getElementById('markdownEditor').value = note.content;
            updatePreview();
            updateStats();
            displayEditor();
            showNotes();
        }

        function displayEditor() {
            document.getElementById('emptyState').style.display = 'none';
            document.getElementById('editorContent').style.display = 'flex';
        }

        function saveNote() {
            if (!currentNote) return;

            currentNote.title = document.getElementById('noteTitle').value;
            currentNote.content = document.getElementById('markdownEditor').value;
            currentNote.tags = extractTags(currentNote.content);

            fetch('/save-note', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentNote)
            })
            .then(r => r.json())
            .then(d => {
                showToast('Note saved', 'success');
                document.getElementById('lastSaved').textContent = new Date().toLocaleTimeString();
                showTags();
            })
            .catch(e => showToast('Error saving note', 'danger'));
        }

        function deleteCurrentNote() {
            if (!currentNote || !confirm('Delete this note?')) return;

            fetch(`/delete-note?id=${currentNote.id}`, { method: 'DELETE' })
                .then(r => r.json())
                .then(d => {
                    allNotes = allNotes.filter(n => n.id !== currentNote.id);
                    currentNote = null;
                    document.getElementById('emptyState').style.display = 'flex';
                    document.getElementById('editorContent').style.display = 'none';
                    showNotes();
                    showToast('Note deleted', 'success');
                })
                .catch(e => showToast('Error deleting note', 'danger'));
        }

        function exportNote() {
            if (!currentNote) return;

            const element = document.createElement('a');
            const file = new Blob([currentNote.content], { type: 'text/markdown' });
            element.href = URL.createObjectURL(file);
            element.download = currentNote.title + '.md';
            element.click();
            showToast('Note exported', 'success');
        }

        function updatePreview() {
            const content = document.getElementById('markdownEditor').value;
            const html = marked.parse(content);
            document.getElementById('markdownPreview').innerHTML = DOMPurify.sanitize(html);
            
            document.querySelectorAll('pre code').forEach(block => {
                hljs.highlightElement(block);
            });
        }

        function updateStats() {
            const content = document.getElementById('markdownEditor').value;
            document.getElementById('charCount').textContent = content.length;
            document.getElementById('wordCount').textContent = content.trim().split(/\\s+/).filter(w => w).length;
        }

        function extractTags(content) {
            const matches = content.match(/#\\w+/g) || [];
            return matches.map(tag => tag.substring(1));
        }

        function filterNotes() {
            const search = document.getElementById('searchInput').value.toLowerCase();
            const filtered = allNotes.filter(n => n.title.toLowerCase().includes(search));
            
            const container = document.getElementById('notesList');
            container.innerHTML = filtered.map(note => `
                <div class="note-item ${currentNote && currentNote.id === note.id ? 'active' : ''}" onclick="selectNote('${note.id}')">
                    <div class="note-item-title">${note.title}</div>
                    <div class="note-item-date">${new Date(note.created).toLocaleDateString()}</div>
                </div>
            `).join('');
        }

        function filterByTag(tag) {
            // Filter notes by tag
            const filtered = allNotes.filter(n => (n.tags || []).includes(tag));
            const container = document.getElementById('notesList');
            container.innerHTML = filtered.map(note => `
                <div class="note-item" onclick="selectNote('${note.id}')">
                    <div class="note-item-title">${note.title}</div>
                </div>
            `).join('');
        }

        function switchView(view) {
            currentView = view;
            const editor = document.getElementById('editorPane');
            const preview = document.getElementById('previewPane');

            if (view === 'split') {
                editor.style.display = 'flex';
                preview.style.display = 'block';
                editor.style.borderRight = '1px solid var(--border)';
            } else if (view === 'edit') {
                editor.style.display = 'flex';
                preview.style.display = 'none';
            } else if (view === 'preview') {
                editor.style.display = 'none';
                preview.style.display = 'block';
            }
        }

        function showToast(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `alert alert-${type} alert-dismissible fade show`;
            toast.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.getElementById('toastContainer').appendChild(toast);
            setTimeout(() => toast.remove(), 5000);
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/notes', methods=['GET'])
def get_notes():
    try:
        if not STORAGE_CONNECTION_STRING:
            return jsonify([])
        
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        
        notes = []
        for blob in container.list_blobs():
            if blob.name.endswith('.md'):
                try:
                    content = blob_service.get_blob_client(CONTAINER_NAME, blob.name).download_blob().readall().decode('utf-8')
                    title = blob.name.replace('.md', '')
                    notes.append({
                        'id': blob.name,
                        'title': title,
                        'content': content,
                        'tags': extractTags(content),
                        'created': blob.last_modified.isoformat() if blob.last_modified else ''
                    })
                except:
                    pass
        
        return jsonify(sorted(notes, key=lambda x: x['created'], reverse=True))
    except Exception as e:
        return jsonify([]), 500

def extractTags(content):
    matches = re.findall(r'#\w+', content)
    return [tag[1:] for tag in matches]

@app.route('/save-note', methods=['POST'])
def save_note():
    try:
        if not STORAGE_CONNECTION_STRING:
            return jsonify({'error': 'Storage not configured'}), 400
        
        data = request.json
        note_title = data.get('title', 'Untitled')
        note_content = data.get('content', '')
        
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        
        blob_name = f"{note_title}.md"
        container.upload_blob(blob_name, note_content.encode('utf-8'), overwrite=True)
        
        return jsonify({'message': 'Note saved'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete-note', methods=['DELETE'])
def delete_note():
    try:
        if not STORAGE_CONNECTION_STRING:
            return jsonify({'error': 'Storage not configured'}), 400
        
        note_id = request.args.get('id')
        
        blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(CONTAINER_NAME)
        container.delete_blob(note_id)
        
        return jsonify({'message': 'Note deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
