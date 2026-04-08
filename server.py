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


def get_ngrok_exe():
    """Ищем ngrok.exe рядом с приложением или в PATH."""
    local = os.path.join(get_base_dir(), 'ngrok.exe')
    if os.path.exists(local):
        return local
    try:
        result = subprocess.run(['where', 'ngrok'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


def download_ngrok():
    """Скачиваем ngrok.exe автоматически."""
    import urllib.request
    import zipfile
    import tempfile

    dest = os.path.join(get_base_dir(), 'ngrok.exe')
    url = 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip'

    print('  Скачиваю ngrok...', end='', flush=True)
    try:
        tmp = tempfile.mktemp(suffix='.zip')
        urllib.request.urlretrieve(url, tmp)
        with zipfile.ZipFile(tmp, 'r') as z:
            z.extract('ngrok.exe', get_base_dir())
        os.remove(tmp)
        print(' готово.')
        return dest
    except Exception as e:
        print(f' ошибка: {e}')
        return None


def get_ngrok_url(port, timeout=10):
    """Получаем публичный URL из ngrok API."""
    import urllib.request
    import json
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen('http://127.0.0.1:4040/api/tunnels', timeout=2) as r:
                data = json.loads(r.read())
                tunnels = data.get('tunnels', [])
                for t in tunnels:
                    if t.get('proto') == 'https':
                        return t['public_url']
                    if t.get('proto') == 'http':
                        return t['public_url']
        except Exception:
            pass
        time.sleep(1)
    return None


def start_ngrok(port):
    """Запускаем ngrok и возвращаем публичный URL."""
    ngrok = get_ngrok_exe()
    if not ngrok:
        return None, None
    try:
        proc = subprocess.Popen(
            [ngrok, 'http', str(port), '--log=stdout'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        url = get_ngrok_url(port)
        return proc, url
    except Exception as e:
        print(f'ngrok error: {e}')
        return None, None


if __name__ == '__main__':
    app = create_app()
    ip = get_local_ip()
    port = 5000

    # Скачиваем ngrok если нет
    if not get_ngrok_exe():
        download_ngrok()

    # Запускаем ngrok
    print('Запуск ngrok туннеля...')
    ngrok_proc, public_url = start_ngrok(port)

    print()
    print('=' * 55)
    print('  Сервер запущен!')
    print(f'  Локально:        http://127.0.0.1:{port}')
    print(f'  WiFi (телефон):  http://{ip}:{port}')
    if public_url:
        print(f'  Интернет:        {public_url}')
        print(f'  (работает с любого места, любой сети)')
    else:
        ngrok_exe = get_ngrok_exe()
        if not ngrok_exe:
            print()
            print('  Для доступа из любого места:')
            print('  1. Скачайте ngrok: https://ngrok.com/download')
            print('  2. Положите ngrok.exe рядом с приложением')
            print('  3. Перезапустите сервер')
        else:
            print('  ngrok не запустился. Проверьте ngrok.exe')
    print('=' * 55)
    print()
    print('  Нажмите Ctrl+C для остановки.')
    print()

    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    finally:
        if ngrok_proc:
            ngrok_proc.terminate()
