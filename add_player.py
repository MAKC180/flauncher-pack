# add_player.py — управление игроками: добавить, сменить пароль, удалить, показать список.
# Пароли НЕ хранятся: в players.json пишется только «соль» и «отпечаток» (хэш) пароля.
# После изменений не забудь отправить players.json на GitHub (add, commit, push).

import os
import re
import json
import getpass    # ввод пароля без показа на экране
import secrets    # надёжные случайные числа — для «соли»
import hashlib

PACK_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYERS_FILE = os.path.join(PACK_DIR, "players.json")

# Сколько раз «перемешивать» пароль. Больше — медленнее подбор пароля.
# ВАЖНО: это число должно совпадать с тем, что в лаунчере (launcher.py).
ITERATIONS = 200_000


def hash_password(password, salt_hex):
    # PBKDF2 — специальный медленный способ сделать «отпечаток» пароля
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                 bytes.fromhex(salt_hex), ITERATIONS)
    return digest.hex()


def load_players():
    try:
        with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)["players"]
    except FileNotFoundError:
        return []   # файла ещё нет — игроков нет


def save_players(players):
    players.sort(key=lambda p: p["nick"].lower())
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"players": players}, f, indent=2, ensure_ascii=False)


def find_player(players, nick):
    # Ник ищем без учёта больших/маленьких букв: HE_MAKC и he_makc — один игрок
    for player in players:
        if player["nick"].lower() == nick.lower():
            return player
    return None


def add_or_change(players):
    nick = input("Ник: ").strip()
    if not re.fullmatch(r"[A-Za-z0-9_]{3,16}", nick):
        print("Ник должен быть 3–16 символов: латинские буквы, цифры и _")
        return
    password = getpass.getpass("Пароль (символы не видны): ")
    if len(password) < 4:
        print("Пароль слишком короткий — нужно хотя бы 4 символа")
        return
    if getpass.getpass("Повтори пароль: ") != password:
        print("Пароли не совпали — ничего не изменено")
        return

    salt = secrets.token_hex(16)   # новая случайная «соль»
    player = find_player(players, nick)
    if player:
        player["salt"] = salt
        player["hash"] = hash_password(password, salt)
        print("Пароль игрока", player["nick"], "изменён")
    else:
        players.append({"nick": nick, "salt": salt, "hash": hash_password(password, salt)})
        print("Игрок", nick, "добавлен")
    save_players(players)


def remove(players):
    nick = input("Ник для удаления: ").strip()
    player = find_player(players, nick)
    if not player:
        print("Такого игрока нет")
        return
    players.remove(player)
    save_players(players)
    print("Игрок", player["nick"], "удалён")


players = load_players()
print("1 — добавить игрока или сменить пароль")
print("2 — удалить игрока")
print("3 — показать список игроков")
choice = input("Выбор: ").strip()

if choice == "1":
    add_or_change(players)
elif choice == "2":
    remove(players)
elif choice == "3":
    for p in players:
        print(" -", p["nick"])
    print("Всего:", len(players))
else:
    print("Нет такого пункта")

if choice in ("1", "2"):
    print("Теперь отправь изменения на GitHub (add, commit, push) — см. инструкцию.")
