import os
from flask import Flask, request, render_template, redirect, url_for, send_file, flash
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()
app = Flask(__name__)
app.secret_key = "change-me"

CONN = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER = os.getenv("AZURE_CONTAINER_NAME")
blob_service = BlobServiceClient.from_connection_string(CONN)
container = blob_service.get_container_client(CONTAINER)

@app.route("/")
def index():
    blobs = [b.name for b in container.list_blobs()]
    return render_template("index.html", files=blobs)

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["file"]
    if f:
        container.upload_blob(name=f.filename, data=f.read(), overwrite=True)
        flash(f"Uploaded {f.filename}")
    return redirect(url_for("index"))

@app.route("/download/<name>")
def download(name):
    stream = container.download_blob(name).readall()
    return send_file(BytesIO(stream), as_attachment=True, download_name=name)

@app.route("/delete/<name>", methods=["POST"])
def delete(name):
    container.delete_blob(name)
    flash(f"Deleted {name}")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)