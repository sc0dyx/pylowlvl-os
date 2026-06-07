
[🇷🇺 Russian Translation / Русская версия](/README_ru.md)

---

# pylowlvl-os

A Python framework for automating the generation of low-level code (x86_64) and the automated build of bootable disk images. This project provides an abstraction layer over the `nasm` assembler, allowing you to describe CPU initialization logic and data output using Python methods.

---

## 🚀 Key Features

* **Real/Protected Mode Code Generation:** Automatic generation of compiler directives (`[bits 16]`, `[org 0x7C00]`), segment register setup, and stack pointer initialization.
* **Video Mode Management:** Switching between standard VGA modes (e.g., text modes `40x25`, `80x50`) and VESA BIOS graphics modes via the `int 0x10` interrupt.
* **Dynamic Procedure Generation:** Print (`aprint`) and sleep (`asleep`) functions inject their assembly implementations into the final listing only when actually called, keeping the resulting binary footprint minimal.
* **Flexible Image Builder (PLowBuilder):** * Compiles source ASM code into temporary files using `nasm`.
* Generates flat binary images (`.bin`, `.img`) for direct writing via `dd` or emulation.
* Creates bootable ISO images following the ISO9660 standard using the El Torito specification in *No Emulation* mode.
* Automated execution of the built result in QEMU.

---

## 🛠 Installation

To work with `pylowlvl-os`, you need `nasm` installed on your system. You can install the library via `pip` directly from the repository:

```bash
# Install the latest version from Git
pip install git+https://github.com/sc0dyx/pylowlvl-os

```

If you plan to contribute or modify the framework code, use editable mode:

```bash
# Clone the repository
git clone https://github.com/sc0dyx/pylowlvl-os
cd pylowlvl-os

# Install in editable mode
pip install -e .

```

*Note: Before running examples, ensure `nasm` is available in your `PATH` (verify with `nasm -v`).*

---

## 💻 Usage Example

Below is a working example of initializing a 16-bit environment, cycling through VGA text modes, printing strings, and compiling the result into a raw binary image with automated execution in QEMU.

```python
from pylowlvl_os.x86_64.pyabstract import PyLowLvl
from pylowlvl_os.builder import PLowBuilder

# Initialize the code generator.
# Set output method to BIOS Teletype (int 0x10, ah=0x0E)
boot = PyLowLvl(aprint16_method="bios_teletype")

# Configure 16-bit real mode header ([bits 16], [org 0x7C00], jmp start).
# cli=False keeps interrupts enabled.
boot.init_enviroment16(cli=False)

# Clear general-purpose registers (ax, bx, cx, dx, si, di, bp) using xor
boot.clear_all_registers()

# Switch VGA mode to 40x25 text mode (16 colors)
boot.set_vga_mode("40x25")
boot.aprint_auto("Hello world!")  # Adds string to data section and triggers print
boot.asleep_auto(3_000_000)       # 3-second delay via BIOS (int 0x15)

# Switch to 80x50 text mode
boot.set_vga_mode("80x50")
boot.aprint_auto("Hello world!")
boot.asleep_auto(3_000_000)

boot.aprint_auto("Welcome to pylowlvl_os")
boot.asleep_auto(3_000_000)

# Halt the CPU (hlt and jmp $ instructions)
boot.stoooop()

# Pad to 510 bytes and set the 0xAA55 boot signature
boot.finalize_disk_sector()

# Pass the generated code to the builder
build = PLowBuilder(boot)

# Run the pipeline:
# 1. Assemble code into a string listing.
# 2. Compile via nasm to raw binary.
# 3. Launch QEMU with: -drive format=raw,file=boot.bin,media=disk,index=0
build.run("boot.bin")

```

---

* **[NASM Documentation](https://www.nasm.us/docs.php):** Official manual for the Netwide Assembler.
* **[QEMU Documentation](https://www.qemu.org/docs/master/):** Official guide for the QEMU emulator.
* **[Python Packaging User Guide](https://packaging.python.org/en/latest/):** Learn more about `pyproject.toml` and PEP 440 standards.
* **[OSDev Wiki](https://wiki.osdev.org/):** The ultimate community-driven encyclopedia for OS development.
