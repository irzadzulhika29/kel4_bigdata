# ingestion/downloader.py

import os
import shutil
import stat
import subprocess
import sys
import tempfile

from ingestion.config import TARGET_DIR

GOOGLE_DRIVE_FOLDER_URL = (
    "https://drive.google.com/drive/folders/15dLf_PqlRH7dKT1AjYfCMBlZpjysuH2Z?usp=sharing"
)
REQUIRED_FILES = {"customers.csv", "items.csv", "sales_1m.csv"}


def _available_files():
    if not os.path.isdir(TARGET_DIR):
        return set()

    return {
        file_name
        for file_name in os.listdir(TARGET_DIR)
        if os.path.isfile(os.path.join(TARGET_DIR, file_name))
    }


def _missing_files():
    return REQUIRED_FILES - _available_files()


def _ensure_readable(file_path):
    current_mode = stat.S_IMODE(os.stat(file_path).st_mode)
    target_mode = current_mode | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
    if target_mode != current_mode:
        os.chmod(file_path, target_mode)


def _ensure_dataset_permissions():
    for file_name in REQUIRED_FILES & _available_files():
        _ensure_readable(os.path.join(TARGET_DIR, file_name))


def _find_downloaded_files(download_root):
    found_files = {}

    for root, _, files in os.walk(download_root):
        for file_name in files:
            if file_name in REQUIRED_FILES and file_name not in found_files:
                found_files[file_name] = os.path.join(root, file_name)

    return found_files


def download_drive_dataset(force=False):
    """Mengunduh dataset dari folder Google Drive publik bila file wajib belum lengkap."""
    missing_files = _missing_files()

    if not missing_files and not force:
        _ensure_dataset_permissions()
        print(f"Mantap! Data sudah tersedia lengkap di {TARGET_DIR}. Melewati proses download.")
        print("File yang tersedia:", sorted(_available_files()))
        return

    print("Data belum lengkap. Memulai proses download dari folder Google Drive...")
    print(f"File yang belum ada: {sorted(missing_files)}")

    os.makedirs(TARGET_DIR, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="gdrive_dataset_") as temp_dir:
        command = [
            sys.executable,
            "-m",
            "gdown",
            GOOGLE_DRIVE_FOLDER_URL,
            "-O",
            temp_dir,
            "--folder",
        ]

        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                "Gagal mengunduh folder Google Drive. Pastikan link bersifat public "
                "('Anyone with the link') dan package 'gdown' sudah terpasang."
            ) from exc

        downloaded_files = _find_downloaded_files(temp_dir)
        missing_after_download = REQUIRED_FILES - set(downloaded_files)

        if missing_after_download:
            raise RuntimeError(
                "Folder Google Drive tidak memuat semua file yang dibutuhkan: "
                f"{sorted(missing_after_download)}"
            )

        for file_name, source_path in downloaded_files.items():
            target_path = os.path.join(TARGET_DIR, file_name)
            shutil.copy2(source_path, target_path)
            _ensure_readable(target_path)

    print(f"Data berhasil didownload dan disimpan di: {TARGET_DIR}")
    print("File yang tersedia:", sorted(_available_files()))


def download_kaggle_dataset():
    """Backward-compatible alias untuk notebook lama."""
    download_drive_dataset()
