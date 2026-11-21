# build_modpack.py — собирает сборку для лаунчера.
# Что делает:
#   1) копирует моды и настройки из CurseForge сюда (папки mods и config);
#   2) для каждого файла считает «отпечаток» (SHA-1) и записывает список в modpack.json.
# Запускать каждый раз, когда поменял моды в CurseForge.

import os
import json
import shutil
import hashlib

# ---------- Настройки ----------
CURSEFORGE_DIR = r"C:\Users\user\curseforge\minecraft\Instances\F"  # откуда берём моды
FOLDERS = ["mods", "config"]   # какие папки переносим в сборку
MC_VERSION = "1.21.1"
NEOFORGE_VERSION = "21.1.265"

# Папка, где лежит этот скрипт (= папка сборки)
PACK_DIR = os.path.dirname(os.path.abspath(__file__))


def sha1_of_file(path):
    # Читаем файл кусками по 1 МБ и считаем отпечаток SHA-1
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


# 1) Копируем папки из CurseForge (старую копию сначала удаляем — чтобы убрать удалённые моды)
for folder in FOLDERS:
    source = os.path.join(CURSEFORGE_DIR, folder)
    target = os.path.join(PACK_DIR, folder)
    if os.path.exists(target):
        shutil.rmtree(target)
    if folder == "mods":
        # Из mods берём только включённые моды (.jar), выключенные (.jar.disabled) пропускаем
        os.makedirs(target)
        for name in os.listdir(source):
            if name.endswith(".jar"):
                shutil.copy2(os.path.join(source, name), target)
    else:
        shutil.copytree(source, target)
    print("Скопировано:", folder)

# 2) Составляем список всех файлов с отпечатками
files = []
for folder in FOLDERS:
    for root, dirs, names in os.walk(os.path.join(PACK_DIR, folder)):
        for name in names:
            full_path = os.path.join(root, name)
            # Путь относительно папки сборки, с "/" как на GitHub: "mods/create.jar"
            rel_path = os.path.relpath(full_path, PACK_DIR).replace("\\", "/")
            files.append({
                "path": rel_path,
                "sha1": sha1_of_file(full_path),
                "size": os.path.getsize(full_path),
            })

files.sort(key=lambda f: f["path"])

modpack = {
    "minecraft": MC_VERSION,
    "neoforge": NEOFORGE_VERSION,
    "files": files,
}

with open(os.path.join(PACK_DIR, "modpack.json"), "w", encoding="utf-8") as f:
    json.dump(modpack, f, indent=2, ensure_ascii=False)

print("Готово! Файлов в сборке:", len(files))
