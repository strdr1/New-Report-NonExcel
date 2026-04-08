#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Точка входа: запускает Flask в фоновом треде, затем открывает нативное окно через pywebview.
Требует WebView2 Runtime (на Windows 10 устанавливается через start.bat автоматически).
"""
import threading
import sys
import os
import time

# Фиксим кодировку вывода для Windows (при сборке stdout может быть None)
if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Чтобы импорты backend работали из корня проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from backend.config import HOST, PORT


def run_flask(app):
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


if __name__ == '__main__':
    app = create_app()

    t = threading.Thread(target=run_flask, args=(app,), daemon=True)
    t.start()

    # Ждём, пока Flask поднимется
    time.sleep(1)

    try:
        import webview
    except Exception as e:
        print(f"[ОШИБКА] Не удалось загрузить pywebview: {e}")
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
            print()
            print("=" * 60)
            print("  WebView2 Runtime не установлен!")
            print("  Скачайте и установите по ссылке:")
            print("  https://developer.microsoft.com/ru-ru/microsoft-edge/webview2/")
            print("=" * 60)
        else:
            print(f"[ОШИБКА] {e}")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
