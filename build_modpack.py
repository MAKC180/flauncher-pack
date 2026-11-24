# build_modpack.py — собирает сборку для лаунчера.
# Что делает:
#   1) копирует моды из CurseForge сюда (папка mods);
#   2) для каждого файла считает «отпечаток» (SHA-1) и записывает список в modpack.json.
#   3) добавляет в modpack.json список модов, которые можно выключить (из optional_mods.json).
# Запускать каждый раз, когда поменял моды в CurseForge.

import os
import json
import shutil
import hashlib

# ---------- Настройки ----------
CURSEFORGE_DIR = r"C:\Users\user\curseforge\minecraft\Instances\F"  # откуда берём моды
FOLDERS = ["mods"]   # какие папки переносим в сборку (config не раздаём — каждый настраивает сам)
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
        # Временные папки модов (кэш) не берём — моды создают их сами
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("cache", ".archive-unpack"))
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

# 3) Моды, которые игрок может выключить в лаунчере (кнопка «Моды»).
#    Список ведётся вручную в optional_mods.json: название и начало имени файла.
#    По началу имени, а не по полному — чтобы после обновления мода (новая версия в имени)
#    ничего не пришлось менять.
with open(os.path.join(PACK_DIR, "optional_mods.json"), "r", encoding="utf-8") as f:
    optional_list = json.load(f)

optional = []
for entry in optional_list:
    found = []
    for file in files:
        name = file["path"][len("mods/"):]   # "mods/jei-1.21.jar" -> "jei-1.21.jar"
        for start in entry["files"]:
            if name.startswith(start):
                found.append(file["path"])
    if found:
        optional.append({"name": entry["name"], "files": found})
    else:
        print("ВНИМАНИЕ: не нашёл в сборке мод для «" + entry["name"] + "» — его не будет в списке")

modpack = {
    "minecraft": MC_VERSION,
    "neoforge": NEOFORGE_VERSION,
    "files": files,
    "optional": optional,
}

with open(os.path.join(PACK_DIR, "modpack.json"), "w", encoding="utf-8") as f:
    json.dump(modpack, f, indent=2, ensure_ascii=False)

print("Готово! Файлов в сборке:", len(files))
print("Модов, которые можно выключить:", len(optional))
