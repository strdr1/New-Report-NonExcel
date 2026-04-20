#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Установщик FuelTracker — собирается в setup.exe через PyInstaller.
Внутри содержит всё приложение, распаковывает в выбранную папку,
создаёт ярлыки на рабочем столе и в меню Пуск.
"""
import os
import sys
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import winreg
import subprocess

# Папка с bundled-файлами приложения (внутри setup.exe)
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = os.path.join(sys._MEIPASS, 'app')
else:
    BUNDLE_DIR = os.path.join(os.path.dirname(__file__), 'dist', 'FuelTracker')

APP_NAME = 'Учёт топлива'
DEFAULT_DIR = r'C:\Учёт топлива'
UNINSTALL_KEY = r'Software\Microsoft\Windows\CurrentVersion\Uninstall\FuelTracker'


def create_shortcut(target, shortcut_path, work_dir, description=''):
    """Создать ярлык .lnk через PowerShell."""
    ps = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut("{shortcut_path}"); '
        f'$s.TargetPath = "{target}"; '
        f'$s.WorkingDirectory = "{work_dir}"; '
        f'$s.Description = "{description}"; '
        f'$s.Save()'
    )
    subprocess.run(['powershell', '-Command', ps],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_desktop():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
        val, _ = winreg.QueryValueEx(key, 'Desktop')
        return val
    except Exception:
        return os.path.join(os.path.expanduser('~'), 'Desktop')


def get_start_menu():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
        val, _ = winreg.QueryValueEx(key, 'Programs')
        return val
    except Exception:
        return os.path.join(os.path.expanduser('~'),
                            'AppData', 'Roaming', 'Microsoft', 'Windows', 'Start Menu', 'Programs')


def register_uninstaller(install_dir):
    """Регистрируем в «Программы и компоненты»."""
    uninstall_exe = os.path.join(install_dir, 'uninstall.exe')
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
        winreg.SetValueEx(key, 'DisplayName',        0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, 'UninstallString',    0, winreg.REG_SZ, f'"{uninstall_exe}"')
        winreg.SetValueEx(key, 'InstallLocation',    0, winreg.REG_SZ, install_dir)
        winreg.SetValueEx(key, 'DisplayVersion',     0, winreg.REG_SZ, '1.0')
        winreg.SetValueEx(key, 'Publisher',          0, winreg.REG_SZ, 'strdr1')
        winreg.SetValueEx(key, 'NoModify',           0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, 'NoRepair',           0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except Exception:
        pass


def write_uninstaller(install_dir):
    """Простой uninstall.bat → переименовываем в uninstall.exe не выйдет,
    вместо этого создаём uninstall.bat который удаляет папку и ярлыки."""
    bat = os.path.join(install_dir, 'uninstall.bat')
    desktop = get_desktop()
    start_menu = os.path.join(get_start_menu(), APP_NAME)
    content = f'''@echo off
echo Удаление {APP_NAME}...
del /Q "{desktop}\\{APP_NAME}.lnk" 2>nul
del /Q "{desktop}\\{APP_NAME} (Сервер).lnk" 2>nul
rmdir /S /Q "{start_menu}" 2>nul
reg delete "HKCU\\{UNINSTALL_KEY}" /f >nul 2>&1
rmdir /S /Q "{install_dir}" 2>nul
echo Готово.
'''
    with open(bat, 'w', encoding='cp1251') as f:
        f.write(content)


class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f'Установка — {APP_NAME}')
        self.root.resizable(False, False)
        self.root.geometry('520x340')
        self.root.configure(bg='#f0f0f0')

        # Центрируем окно
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 520) // 2
        y = (self.root.winfo_screenheight() - 340) // 2
        self.root.geometry(f'520x340+{x}+{y}')

        self._build_ui()

    def _build_ui(self):
        # Заголовок
        header = tk.Frame(self.root, bg='#1565c0', height=70)
        header.pack(fill='x')
        tk.Label(header, text=APP_NAME, font=('Segoe UI', 16, 'bold'),
                 bg='#1565c0', fg='white').pack(pady=20)

        body = tk.Frame(self.root, bg='#f0f0f0', padx=20, pady=20)
        body.pack(fill='both', expand=True)

        # Папка установки
        tk.Label(body, text='Папка установки:', bg='#f0f0f0',
                 font=('Segoe UI', 10)).pack(anchor='w')

        dir_frame = tk.Frame(body, bg='#f0f0f0')
        dir_frame.pack(fill='x', pady=(4, 16))

        self.dir_var = tk.StringVar(value=DEFAULT_DIR)
        tk.Entry(dir_frame, textvariable=self.dir_var, font=('Segoe UI', 10),
                 width=46).pack(side='left')
        tk.Button(dir_frame, text='...', command=self._browse,
                  font=('Segoe UI', 9), width=4).pack(side='left', padx=(4, 0))

        # Ярлык на рабочем столе
        self.desktop_var = tk.BooleanVar(value=True)
        tk.Checkbutton(body, text='Создать ярлыки на рабочем столе',
                       variable=self.desktop_var, bg='#f0f0f0',
                       font=('Segoe UI', 10)).pack(anchor='w')

        # Прогресс
        self.progress = ttk.Progressbar(body, length=480, mode='determinate')
        self.progress.pack(fill='x', pady=(16, 4))

        self.status_var = tk.StringVar(value='Готов к установке')
        tk.Label(body, textvariable=self.status_var, bg='#f0f0f0',
                 font=('Segoe UI', 9), fg='#555').pack(anchor='w')

        # Кнопки
        btn_frame = tk.Frame(self.root, bg='#f0f0f0', padx=20, pady=10)
        btn_frame.pack(fill='x')

        self.install_btn = tk.Button(btn_frame, text='Установить',
                                     command=self._start_install,
                                     bg='#1565c0', fg='white',
                                     font=('Segoe UI', 10, 'bold'),
                                     padx=20, pady=6, relief='flat')
        self.install_btn.pack(side='right')

        tk.Button(btn_frame, text='Отмена', command=self.root.destroy,
                  font=('Segoe UI', 10), padx=20, pady=6,
                  relief='flat').pack(side='right', padx=(0, 8))

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get(),
                                    title='Выберите папку установки')
        if d:
            self.dir_var.set(os.path.normpath(d))

    def _start_install(self):
        self.install_btn.config(state='disabled')
        threading.Thread(target=self._install, daemon=True).start()

    def _install(self):
        install_dir = self.dir_var.get()
        try:
            os.makedirs(install_dir, exist_ok=True)

            # Считаем файлы
            all_files = []
            for root, dirs, files in os.walk(BUNDLE_DIR):
                for f in files:
                    all_files.append(os.path.join(root, f))
            total = len(all_files)

            # Копируем файлы
            for i, src in enumerate(all_files):
                rel = os.path.relpath(src, BUNDLE_DIR)
                dst = os.path.join(install_dir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                pct = int((i + 1) / total * 85)
                self.progress['value'] = pct
                self.status_var.set(f'Копирование: {rel}')
                self.root.update_idletasks()

            # Ярлыки
            self.status_var.set('Создание ярлыков...')
            self.progress['value'] = 90

            app_exe    = os.path.join(install_dir, 'FuelTracker.exe')
            desktop    = get_desktop()
            start_menu = os.path.join(get_start_menu(), APP_NAME)
            os.makedirs(start_menu, exist_ok=True)

            if self.desktop_var.get():
                create_shortcut(app_exe, os.path.join(desktop, f'{APP_NAME}.lnk'), install_dir, 'Учёт топлива')

            create_shortcut(app_exe, os.path.join(start_menu, f'{APP_NAME}.lnk'), install_dir)

            # Uninstaller + регистрация
            write_uninstaller(install_dir)
            register_uninstaller(install_dir)

            self.progress['value'] = 100
            self.status_var.set('Установка завершена!')

            messagebox.showinfo('Готово',
                f'{APP_NAME} успешно установлен в:\n{install_dir}\n\n'
                'Ярлыки созданы на рабочем столе.')
            self.root.destroy()

        except Exception as e:
            messagebox.showerror('Ошибка установки', str(e))
            self.install_btn.config(state='normal')
            self.status_var.set('Ошибка!')


if __name__ == '__main__':
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()
