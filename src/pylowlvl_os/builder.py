from .x86_64.pyabstract import PyLowLvl
import subprocess
import tempfile
import os as _os
import os.path

import pycdlib


class PLowBuilder:
    def __init__(self, os_instance: PyLowLvl) -> None:
        self.os = os_instance

    def build(self, output: str = "boot.iso") -> None:
        """
        Собирает образ. Формат определяется по расширению файла:
          .iso -> ISO9660 с El Torito (для Ventoy, QEMU)
          .bin -> сырой бинарный файл (для dd, QEMU)
          .img -> то же, что .bin
        """
        ext = os.path.splitext(output)[1].lower()

        if ext in (".bin", ".img"):
            self._build_raw(output)
        elif ext == ".iso":
            self._build_iso(output)
        else:
            raise ValueError(f"Unsupported output format: {ext}")

    def _build_raw(self, output: str) -> None:
        """Собирает сырой бинарный образ."""
        asm_text = "\n".join(self.os.asm_code)

        with tempfile.NamedTemporaryFile(
            suffix=".asm", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(asm_text)
            asm_path = f.name

        try:
            subprocess.run(["nasm", "-f", "bin", "-o", output, asm_path], check=True)
        finally:
            _os.unlink(asm_path)

    def _build_iso(self, output: str) -> None:
        """Собирает ISO-образ с загрузочным сектором (El Torito) без эмуляции."""
        # Шаг 1: компилируем загрузчик в bin
        asm_text = "\n".join(self.os.asm_code)

        with tempfile.NamedTemporaryFile(
            suffix=".asm", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(asm_text)
            asm_path = f.name

        boot_bin_path = None
        try:
            boot_bin_path = tempfile.mktemp(suffix=".bin")
            subprocess.run(
                ["nasm", "-f", "bin", "-o", boot_bin_path, asm_path],
                check=True,
            )
        finally:
            _os.unlink(asm_path)

        # Шаг 2: создаем ISO с загрузчиком
        fp_boot = None
        try:
            iso = pycdlib.PyCdlib()
            iso.new(
                interchange_level=4,
                sys_ident="",
                vol_ident="PYLOWLVL_OS",
                app_ident_str="pylowlvl-os",
            )

            # Файл ДОЛЖЕН оставаться открытым до вызова iso.write()
            fp_boot = open(boot_bin_path, "rb")
            iso.add_fp(fp_boot, len(open(boot_bin_path, "rb").read()), "/BOOT.BIN;1")

            # Правильный способ: No Emulation
            iso.add_eltorito(
                "/BOOT.BIN;1",
                bootcatfile="/BOOT.CAT;1",
                boot_load_size=1,  # Загружаем 1 сектор (512 байт)
                media_name="noemul",  # Никакой эмуляции дискет!
            )

            iso.write(output)
            iso.close()

        finally:
            if fp_boot:
                fp_boot.close()
            if boot_bin_path and _os.path.exists(boot_bin_path):
                _os.unlink(boot_bin_path)

    def run(self, output: str = "boot.iso") -> None:
        """Собирает и запускает образ в QEMU."""
        self.build(output)

        ext = os.path.splitext(output)[1].lower()
        if ext == ".iso":
            # QEMU с ISO
            subprocess.run(
                [
                    "qemu-system-x86_64",
                    "-cdrom",
                    output,
                ]
            )
        else:
            # QEMU с сырым образом
            subprocess.run(
                [
                    "qemu-system-x86_64",
                    "-drive",
                    f"format=raw,file={output},media=disk,index=0",
                ]
            )
