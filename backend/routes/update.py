import os
import sys
import zipfile
import tempfile
import threading
import urllib.request
import json
from flask import Blueprint, jsonify

bp = Blueprint('update', __name__, url_prefix='/api/update')

GITHUB_REPO = 'strdr1/New-Report-NonExcel'
GITHUB_API  = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_current_version():
    ver_file = os.path.join(get_base_dir(), 'version.txt')
    try:
        with open(ver_file, 'r') as f:
            return f.read().strip()
    except Exception:
        return '0.0.0'


def version_tuple(v):
    try:
        return tuple(int(x) for x in v.lstrip('v').split('.'))
    except Exception:
        return (0, 0, 0)


def do_update(download_url, tag_name, callback):
    """Скачиваем zip релиза и распаковываем поверх текущей папки."""
    base_dir = get_base_dir()
    try:
        callback({'status': 'downloading', 'message': 'Скачивание обновления...'})

        tmp_zip = os.path.join(tempfile.gettempdir(), 'fueltracker_update.zip')
        urllib.request.urlretrieve(download_url, tmp_zip)

        callback({'status': 'extracting', 'message': 'Установка обновления...'})

        with zipfile.ZipFile(tmp_zip, 'r') as z:
            for member in z.infolist():
                # Пропускаем БД и логи — не трогаем данные пользователя
                name = member.filename
                if any(name.endswith(x) for x in ['.db', '.log', 'ngrok.exe']):
                    continue
                # Убираем верхнюю папку из zip (FuelTracker/...)
                parts = name.split('/', 1)
                if len(parts) == 2 and parts[1]:
                    target = os.path.join(base_dir, parts[1])
                    if member.is_dir():
                        os.makedirs(target, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target), exist_ok=True)
                        with z.open(member) as src, open(target, 'wb') as dst:
                            dst.write(src.read())

        os.remove(tmp_zip)

        # Записываем новую версию
        ver_file = os.path.join(base_dir, 'version.txt')
        with open(ver_file, 'w') as f:
            f.write(tag_name.lstrip('v') + '\n')

        callback({'status': 'done', 'message': 'Обновление установлено. Перезапустите приложение.'})

    except Exception as e:
        callback({'status': 'error', 'message': str(e)})


# Хранит прогресс текущего обновления
_update_state = {'status': 'idle', 'message': ''}


@bp.route('/check')
def check_update():
    try:
        req = urllib.request.Request(GITHUB_API, headers={'User-Agent': 'FuelTracker'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())

        latest_tag = data.get('tag_name', '0.0.0')
        current    = get_current_version()

        has_update = version_tuple(latest_tag) > version_tuple(current)

        # Ищем zip-ассет релиза
        assets = data.get('assets', [])
        zip_url = next(
            (a['browser_download_url'] for a in assets if a['name'].endswith('.zip')),
            None
        )

        return jsonify({
            'current':    current,
            'latest':     latest_tag.lstrip('v'),
            'has_update': has_update,
            'zip_url':    zip_url,
            'notes':      data.get('body', ''),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/install', methods=['POST'])
def install_update():
    from flask import request as freq
    data    = freq.get_json()
    zip_url = data.get('zip_url')
    tag     = data.get('tag', '1.0.0')

    if not zip_url:
        return jsonify({'error': 'No zip_url provided'}), 400

    if _update_state['status'] == 'downloading':
        return jsonify({'error': 'Update already in progress'}), 409

    def cb(state):
        _update_state.update(state)

    threading.Thread(target=do_update, args=(zip_url, tag, cb), daemon=True).start()
    return jsonify({'status': 'started'})


@bp.route('/progress')
def update_progress():
    return jsonify(_update_state)
