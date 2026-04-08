#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Серверный режим: Flask слушает на 0.0.0.0 — доступ с телефона по локальной сети.
nginx (если есть) проксирует порт 80 -> 5000.
"""
import sys
import os
import subprocess
import socket

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

if __name__ == '__main__':
    app = create_app()
    ip = get_local_ip()

    # Запускаем nginx если есть
    nginx_path = os.path.join(os.path.dirname(__file__), 'nginx', 'nginx.exe')
    nginx_running = False
    if os.path.exists(nginx_path):
        try:
            subprocess.Popen(
                [nginx_path],
                cwd=os.path.dirname(nginx_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            nginx_running = True
            print(f'nginx started on port 80')
        except Exception as e:
            print(f'nginx failed to start: {e}')

    port = 5000
    access_port = 80 if nginx_running else port

    print()
    print('=' * 50)
    print(f'  Сервер запущен!')
    print(f'  Локально:  http://127.0.0.1:{access_port}')
    print(f'  С телефона: http://{ip}:{access_port}')
    print(f'  (телефон должен быть в той же WiFi сети)')
    print('=' * 50)
    print()

    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    finally:
        if nginx_running:
            subprocess.run(
                [nginx_path, '-s', 'stop'],
                cwd=os.path.dirname(nginx_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
