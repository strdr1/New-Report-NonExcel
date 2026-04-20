#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import threading
import time

if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from backend.config import HOST, PORT

SERVER_MODE = '--server' in sys.argv


def run_flask(app, host='127.0.0.1', port=PORT):
    app.run(host=host, port=port, debug=False, use_reloader=False)


def wait_for_flask(port, timeout=15):
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


# ─── DESKTOP MODE ────────────────────────────────────────────────────────────

def run_desktop():
    app = create_app()
    t = threading.Thread(target=run_flask, args=(app,), daemon=True)
    t.start()
    time.sleep(1)

    try:
        import webview
    except Exception as e:
        print(f"[ERROR] pywebview not found: {e}")
        sys.exit(1)

    try:
        window = webview.create_window(
            'Учёт топлива',
            f'http://{HOST}:{PORT}',
            width=1400,
            height=900,
            min_size=(800, 600),
        )
        webview.start(gui='edgechromium', private_mode=True)
    except Exception as e:
        msg = str(e)
        if 'WebView2' in msg or 'EdgeChromium' in msg or 'edgechromium' in msg.lower():
            print("\n" + "=" * 60)
            print("  WebView2 Runtime не установлен!")
            print("  https://developer.microsoft.com/ru-ru/microsoft-edge/webview2/")
            print("=" * 60)
        else:
            print(f"[ERROR] {e}")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)


# ─── SERVER MODE ─────────────────────────────────────────────────────────────

def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_tunnel_exe():
    import subprocess
    local = os.path.join(get_base_dir(), 'cloudflared.exe')
    if os.path.exists(local):
        return local
    try:
        result = subprocess.run(['where', 'cloudflared'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


def download_cloudflared():
    import urllib.request
    dest = os.path.join(get_base_dir(), 'cloudflared.exe')
    url = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'
    print('  Скачиваю cloudflared...', end='', flush=True)
    try:
        urllib.request.urlretrieve(url, dest)
        print(' готово.')
        return dest
    except Exception as e:
        print(f' ошибка: {e}')
        return None


def get_cloudflared_url(proc, timeout=15):
    import re
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            line = proc.stderr.readline()
            if not line:
                time.sleep(0.2)
                continue
            line = line.decode('utf-8', errors='ignore')
            match = re.search(r'https://[a-z0-9\-]+\.trycloudflare\.com', line)
            if match:
                return match.group(0)
        except Exception:
            break
    return None


def start_tunnel(port):
    import subprocess
    exe = get_tunnel_exe()
    if not exe:
        return None, None
    try:
        proc = subprocess.Popen(
            [exe, 'tunnel', '--url', f'http://localhost:{port}'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        url = get_cloudflared_url(proc)
        return proc, url
    except Exception as e:
        print(f'cloudflared error: {e}')
        return None, None


def run_server():
    port = PORT
    ip = get_local_ip()

    if not get_tunnel_exe():
        download_cloudflared()

    app = create_app()
    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False),
        daemon=True
    )
    flask_thread.start()

    print('Запуск сервера...')
    wait_for_flask(port)

    print('Запуск туннеля Cloudflare...')
    tunnel_proc, public_url = start_tunnel(port)

    print()
    print('=' * 55)
    print('  Сервер запущен!')
    print(f'  Локально:        http://127.0.0.1:{port}')
    print(f'  WiFi (телефон):  http://{ip}:{port}')
    if public_url:
        print(f'  Интернет:        {public_url}')
        print(f'  (работает с любого места, любой сети)')
    else:
        print('  Туннель не запустился (нет интернета?)')
    print('=' * 55)
    print()
    print('  Нажмите Ctrl+C для остановки.')
    print()

    try:
        flask_thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        if tunnel_proc:
            tunnel_proc.terminate()


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if SERVER_MODE:
        run_server()
    else:
        run_desktop()
