#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Серверный режим.
- Локальная сеть: Flask на 0.0.0.0:5000
- Интернет (с любого места): ngrok туннель
"""
import sys
import os
import subprocess
import socket
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from backend.app import create_app


def get_local_ip():
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
    """Ищем cloudflared.exe рядом с приложением или в PATH."""
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
    """Скачиваем cloudflared.exe автоматически (Cloudflare Tunnel, без регистрации)."""
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
    """Читаем URL туннеля из вывода cloudflared."""
    import re
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            line = proc.stderr.readline()
            if not line:
                time.sleep(0.2)
                continue
            line = line.decode('utf-8', errors='ignore')
            # cloudflared печатает URL вида https://xxxx.trycloudflare.com
            match = re.search(r'https://[a-z0-9\-]+\.trycloudflare\.com', line)
            if match:
                return match.group(0)
        except Exception:
            break
    return None


def start_tunnel(port):
    """Запускаем cloudflared tunnel и возвращаем публичный URL."""
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


def wait_for_flask(port, timeout=15):
    """Ждём пока Flask поднимется и начнёт слушать порт."""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


if __name__ == '__main__':
    app = create_app()
    ip = get_local_ip()
    port = 5000

    # Скачиваем cloudflared если нет
    if not get_tunnel_exe():
        download_cloudflared()

    # Запускаем Flask в фоне
    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False),
        daemon=True
    )
    flask_thread.start()

    # Ждём пока Flask реально поднимется
    print('Запуск сервера...')
    wait_for_flask(port)

    # Только после этого запускаем туннель
    print('Запуск туннеля Cloudflare...')
    ngrok_proc, public_url = start_tunnel(port)

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
        if ngrok_proc:
            ngrok_proc.terminate()
