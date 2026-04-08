import os
import sys
import subprocess
import threading
import urllib.request
import json
from flask import Blueprint, jsonify

bp = Blueprint('update', __name__, url_prefix='/api/update')

GITHUB_REPO = 'strdr1/New-Report-NonExcel'
GITHUB_API  = f'https://api.github.com/repos/{GITHUB_REPO}/commits/main'


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_current_commit():
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, cwd=get_base_dir()
        )
        return result.stdout.strip()
    except Exception:
        return 'unknown'


def get_current_version():
    ver_file = os.path.join(get_base_dir(), 'version.txt')
    try:
        with open(ver_file, 'r') as f:
            return f.read().strip()
    except Exception:
        return '1.0.0'


_update_state = {'status': 'idle', 'message': ''}


def do_git_pull(callback):
    base_dir = get_base_dir()
    try:
        callback({'status': 'pulling', 'message': 'Получаю обновления с GitHub...'})

        result = subprocess.run(
            ['git', 'pull', 'origin', 'main', '--rebase'],
            capture_output=True, text=True, cwd=base_dir
        )

        if result.returncode != 0:
            callback({'status': 'error', 'message': result.stderr or result.stdout or 'git pull failed'})
            return

        output = result.stdout.strip()
        if 'Already up to date' in output:
            callback({'status': 'done', 'message': 'Уже последняя версия.'})
        else:
            # Ставим зависимости если поменялись
            callback({'status': 'pulling', 'message': 'Устанавливаю зависимости...'})
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '-q'],
                cwd=base_dir, capture_output=True
            )
            callback({'status': 'done', 'message': 'Обновление установлено! Перезапустите приложение.'})

    except FileNotFoundError:
        callback({'status': 'error', 'message': 'git не найден. Установите Git: https://git-scm.com'})
    except Exception as e:
        callback({'status': 'error', 'message': str(e)})


@bp.route('/check')
def check_update():
    try:
        req = urllib.request.Request(
            GITHUB_API,
            headers={'User-Agent': 'FuelTracker'}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())

        remote_sha   = data['sha'][:7]
        remote_msg   = data['commit']['message'].split('\n')[0]
        remote_date  = data['commit']['author']['date'][:10]
        current_sha  = get_current_commit()
        has_update   = remote_sha != current_sha

        return jsonify({
            'current':    current_sha,
            'latest':     remote_sha,
            'has_update': has_update,
            'message':    remote_msg,
            'date':       remote_date,
            'version':    get_current_version(),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/install', methods=['POST'])
def install_update():
    if _update_state['status'] == 'pulling':
        return jsonify({'error': 'Update already in progress'}), 409

    def cb(state):
        _update_state.update(state)

    threading.Thread(target=do_git_pull, args=(cb,), daemon=True).start()
    return jsonify({'status': 'started'})


@bp.route('/progress')
def update_progress():
    return jsonify(_update_state)
