"""Pitchora desktop launcher: opens a native app window, not Chrome/Edge."""
import os
import sys
import threading


def resource_path(relative):
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, relative)

# Configure paths before starting the native window.
import app as pitchora_app
pitchora_app.app.template_folder = resource_path("templates")
pitchora_app.app.static_folder = resource_path("static")


def main():
    import webview
    from werkzeug.serving import make_server

    # Use an available local port; the user sees only the desktop window.
    server = make_server("127.0.0.1", 0, pitchora_app.app, threaded=True)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    url = f"http://127.0.0.1:{server.server_port}/"

    try:
        webview.create_window(
            "Pitchora - AI Pitch Deck Generator",
            url,
            width=1280,
            height=820,
            min_size=(960, 640),
        )
        webview.start()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
