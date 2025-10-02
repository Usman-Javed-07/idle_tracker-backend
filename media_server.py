import os
from flask import Flask, send_from_directory, abort
from backend.config import MEDIA_ROOT

app = Flask(__name__)


@app.get("/media/<path:relpath>")
def serve_media(relpath):
    # Only serve files beneath MEDIA_ROOT
    full_path = os.path.abspath(os.path.join(MEDIA_ROOT, relpath))
    root_abs = os.path.abspath(MEDIA_ROOT)
    if not full_path.startswith(root_abs):
        abort(404)
    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)
    if not os.path.exists(full_path):
        abort(404)
    return send_from_directory(directory, filename)


if __name__ == "__main__":
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    app.run(host="127.0.0.1", port=5000, debug=False)
