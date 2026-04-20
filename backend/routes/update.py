import os
import sys
import subprocess
import threading
import urllib.request
import json
from flask import Blueprint, jsonify

bp = Blueprint('update', __name__, url_prefix='/api/update')

GITHUB_REPO  = 'strdr1/New-Report-NonExcel'
RELEASES_API = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
EXE_NAME     = 'FuelTracker.exe'


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
        return '1.0.0'


def _parse_version(v):
    v = v.lstrip('v')
    try:
        return tuple(int(x) for x in v.split('.'))
    except Exception:
        return (0, 0, 0)


_update_state = {'status': 'idle', 'message': '', 'progress': 0}


def _do_update(download_url, tag_name):
    base_dir = get_base_dir()
    exe_path = os.path.join(base_dir, EXE_NAME)
    tmp_path = os.path.join(base_dir, '_FuelTracker_update.exe')

    def cb(status, message, progress=0):
        _update_state.update({'status': status, 'message': message, 'progress': progress})

    try:
        cb('downloading', 'Скачиваю новую версию...', 0)

        def reporthook(count, block_size, total_size):
            if total_size > 0:
                pct = min(int(count * block_size * 100 / total_size), 99)
                cb('downloading', f'Скачиваю... {pct}%', pct)

        urllib.request.urlretrieve(download_url, tmp_path, reporthook)

        # Обновляем version.txt
        ver_file = os.path.join(base_dir, 'version.txt')
        with open(ver_file, 'w') as f:
            f.write(tag_name.lstrip('v'))

        cb('installing', 'Устанавливаю обновление...', 99)

        if getattr(sys, 'frozen', False):
            # EXE режим: создаём bat-helper который заменит EXE и перезапустит
            bat_path = os.path.join(base_dir, '_updater.bat')
            bat = f'''@echo off
ping 127.0.0.1 -n 3 > nul
move /Y "{tmp_path}" "{exe_path}"
start "" "{exe_path}"
del "%~f0"
'''
            with open(bat_path, 'w') as f:
                f.write(bat)

            subprocess.Popen(
                ['cmd', '/c', bat_path],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True
            )
            cb('done', 'Обновление установлено! Приложение перезапускается...', 100)
            threading.Timer(1.5, lambda: os._exit(0)).start()

        else:
            # Режим Python (start.bat): просто сообщаем перезапустить
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            cb('done', 'Обновление установлено! Перезапустите приложение.', 100)

    except Exception as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        cb('error', f'Ошибка: {e}', 0)


@bp.route('/check')
def check_update():
    try:
        req = urllib.request.Request(RELEASES_API, headers={'User-Agent': 'FuelTracker'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())

        tag_name    = data.get('tag_name', 'v1.0.0')
        release_msg = data.get('name') or data.get('body', '')[:100] or tag_name
        release_date = (data.get('published_at') or '')[:10]

        # Ищем FuelTracker.exe в assets релиза
        download_url = None
        for asset in data.get('assets', []):
            if asset['name'] == EXE_NAME:
                download_url = asset['browser_download_url']
                break

        remote_version  = tag_name.lstrip('v')
        current_version = get_current_version()
        has_update = _parse_version(remote_version) > _parse_version(current_version)

        return jsonify({
            'current':      current_version,
            'latest':       remote_version,
            'has_update':   has_update,
            'message':      release_msg,
            'date':         release_date,
            'download_url': download_url,
            'version':      current_version,
            'is_exe':       getattr(sys, 'frozen', False),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/install', methods=['POST'])
def install_update():
    if _update_state['status'] in ('downloading', 'installing'):
        return jsonify({'error': 'Update already in progress'}), 409

    try:
        req = urllib.request.Request(RELEASES_API, headers={'User-Agent': 'FuelTracker'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())

        tag_name = data.get('tag_name', 'v1.0.0')
        download_url = None
        for asset in data.get('assets', []):
            if asset['name'] == EXE_NAME:
                download_url = asset['browser_download_url']
                break

        if not download_url:
            return jsonify({'error': f'{EXE_NAME} не найден в релизе. Загрузи его на GitHub Releases.'}), 404

        threading.Thread(target=_do_update, args=(download_url, tag_name), daemon=True).start()
        return jsonify({'status': 'started'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/progress')
def update_progress():
    return jsonify(_update_state)
