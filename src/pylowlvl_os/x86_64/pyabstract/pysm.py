from typing import Literal


class PyLowLvl:
    def __init__(
        self,
        address_bios_boot: str = "0x7C00",
        automode: bool = True,
        aprint16_method: Literal["direct", "bios_color", "bios_teletype"] = "direct",
    ) -> None:
        self.asm_code = []
        self.c_code = []
        self.address_bios_boot = address_bios_boot
        self._print16 = False
        self._print32 = False
        self._sleep16 = False
        self._sleep32 = False
        self.automode = automode
        self.aprint16_method = aprint16_method  # direct, #bios_color, #bios_teletype
        if self.automode:
            self.mode = "16bit"

    def __add_const_string(self, text: str, backtick: bool) -> str:
        label = f"_str_{len(self.asm_code)}"

        try:
            idx = self.asm_code.index("db_section:")
        except ValueError:
            idx = self.asm_code.index("   jmp start") + 1
            self.asm_code[idx:idx] = ["db_section:"]

        if backtick:
            self.asm_code.insert(idx + 1, f"{label} db `{text}`, 0")
        else:
            self.asm_code.insert(idx + 1, f'{label} db "{text}", 0')
        return label

    def __add_const_data(self, label: str, data: str) -> str:
        """Добавляет labelled данные в секцию db_section."""
        try:
            idx = self.asm_code.index("db_section:")
        except ValueError:
            idx = self.asm_code.index("   jmp start") + 1
            self.asm_code[idx:idx] = ["db_section:"]
        self.asm_code.insert(idx + 1, f"{label} {data}")
        return label

    def __escape_nasm_string(self, text: str) -> str:
        text = text.replace("\\", "\\\\")  # reverse slash
        text = text.replace("\a", "\\a")  # bell
        text = text.replace("\b", "\\b")  # backspace
        text = text.replace("\f", "\\f")  # form feed
        text = text.replace("\n", "\\n")  # line feed
        text = text.replace("\r", "\\r")  # carriage return
        text = text.replace("\t", "\\t")  # tab
        text = text.replace("\v", "\\v")  # vertical tab
        text = text.replace("'", "\\'")  # single quote
        text = text.replace('"', '\\"')  # double quote
        text = text.replace("\0", "\\0")  # null
        text = text.replace("\x0e", "\\x0E")  # shift out
        text = text.replace("\x0f", "\\x0F")  # shift in
        text = text.replace("\x1b", "\\x1B")
        return text

    def _asleep_16(self, time_us: int = 1000000):
        if not self._sleep16:
            procedure = []
            procedure.extend(
                [
                    "sleep_bios:",
                    "    pusha",
                    "    mov ah, 0x86",
                    "    int 0x15",
                    "    popa",
                    "    ret",
                ]
            )
            self.asm_code[3:3] = procedure
            self._sleep16 = True
        time_hex = f"{time_us:08X}"
        self.asm_code.extend(
            [
                f"mov cx, 0x{time_hex[0:4]}",
                f"mov dx, 0x{time_hex[4:]}",
                "call sleep_bios",
            ]
        )

    def _asleep_32(self, time_us: int = 1000000):
        if not self._sleep32:
            procedure = [
                "sleep_pit:",
                "    pushad",
                "    mov al, 0x30",
                "    out 0x43, al",
                "    mov ax, dx",
                "    out 0x40, al",
                "    mov al, ah",
                "    out 0x40, al",
                ".wait_pit:",
                "    in al, 0x40",
                "    test al, 0xFF",
                "    jnz .wait_pit",
                "    popad",
                "    ret",
            ]
            idx = self.asm_code.index("protected_mode:") + 1
            self.asm_code[idx:idx] = procedure

        time_hex = f"{time_us:08X}"
        self.asm_code.extend(
            [
                f"mov cx, 0x{time_hex[0:4]}",
                f"mov dx, 0x{time_hex[4:]}",
                "call sleep_pit",
            ]
        )

    def _aprint_32(
        self, *values: object, sep: str | None = " ", end: str | None = "\n", color: int = 0x0F
    ) -> None:
        if not self._print32:
            procedure = [
                "aprint32:",
                "    pushad",
                "    mov edi, [aprint32_offset]",
                "    add edi, 0xB8000",
                ".loop:",
                "    lodsb",
                "    test al, al",
                "    jz .done",
                "    mov byte [edi], al",
                "    inc edi",
                "    mov al, [aprint32_color]",
                "    mov byte [edi], al",
                "    inc edi",
                "    jmp .loop",
                ".done:",
                "    sub edi, 0xB8000",
                "    mov [aprint32_offset], edi",
                "    popad",
                "    ret",
            ]
            idx = self.asm_code.index("protected_mode:") + 1
            self.asm_code[idx:idx] = procedure
            self.__add_const_data("aprint32_offset", "dd 0")
            self.__add_const_data("aprint32_color", "db 0x0F")
            self._print32 = True

        text = self.__escape_nasm_string(sep.join(str(v) for v in values) + end)
        label = f"_str32_{len(self.asm_code)}"
        self.asm_code.append(f"{label} db `{text}`, 0")
        self.asm_code.append(f"mov byte [aprint32_color], {color}")
        self.asm_code.append(f"mov esi, {label}")
        self.asm_code.append("call aprint32")

    def _aprint_16(
        self,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        color: int = 0x0F,
        backtick: bool = True,
    ) -> None:
        if not self._print16:
            procedure = []

            if self.aprint16_method == "bios_teletype":
                procedure.extend(
                    [
                        "aprint16:",
                        "    pusha",
                        ".loop:",
                        "    lodsb",
                        "    test al, al",
                        "    jz .done",
                        "    mov ah, 0x0E",
                        "    int 0x10",
                        "    jmp .loop",
                        ".done:",
                        "    popa",
                        "    ret",
                    ]
                )
            elif self.aprint16_method == "bios_color":
                procedure.extend(
                    [
                        "aprint16:",
                        "    pusha",
                        "    mov bh, 0",
                        "    mov cx, 1",
                        ".loop:",
                        "    lodsb",
                        "    test al, al",
                        "    jz .done",
                        "    mov ah, 0x09",
                        "    mov bl, [aprint16_color]",
                        "    int 0x10",
                        "    mov ah, 0x03",
                        "    int 0x10",
                        "    inc dl",
                        "    mov ah, 0x02",
                        "    int 0x10",
                        "    jmp .loop",
                        ".done:",
                        "    popa",
                        "    ret",
                    ]
                )
                self.__add_const_data("aprint16_color", "db 0")
            else:  # direct
                procedure.extend(
                    [
                        "aprint16:",
                        "    pusha",
                        "    push es",
                        "    mov ax, 0xB800",
                        "    mov es, ax",
                        "    mov di, [aprint16_offset]",
                        ".loop:",
                        "    lodsb",
                        "    test al, al",
                        "    jz .done",
                        "    stosb",
                        "    mov al, [aprint16_color]",
                        "    stosb",
                        "    jmp .loop",
                        ".done:",
                        "    mov [aprint16_offset], di",
                        "    pop es",
                        "    popa",
                        "    ret",
                    ]
                )
                self.__add_const_data("aprint32_offset", "dd 0")
                self.__add_const_data("aprint32_color", "db 0x0F")
            self.asm_code[3:3] = procedure
            self._print16 = True

        text = self.__escape_nasm_string(sep.join(str(v) for v in values) + end)
        label = self.__add_const_string(text, backtick)

        if self.aprint16_method != "bios_teletype":
            self.asm_code.append(f"mov byte [aprint16_color], {color}")

        self.asm_code.append(f"mov si, {label}")
        self.asm_code.append("call aprint16")

    def aprint_32(
        self, *values: object, sep: str | None = " ", end: str | None = "\n", color: int = 0x0F
    ) -> None:
        if self.automode:
            raise RuntimeError("aprint_32 unavailable, pls disable automode")
        self._aprint_32(*values, sep=sep, end=end, color=color)

    def aprint_16(
        self,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        color: int = 0x0F,
    ) -> None:
        if self.automode:
            raise RuntimeError("aprint_16 unavailable, pls disable automode")
        self._aprint_16(*values, sep=sep, end=end, color=color)

    def aprint_auto(
        self,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        color: int = 0x0F,
        backtick: bool = True,
    ) -> None:
        if not self.automode:
            raise RuntimeError("aprint_auto unavailable, pls enable automode")
        if self.mode == "32bit":
            self._aprint_32(*values, sep=sep, end=end, color=color)
        elif self.mode == "16bit":
            self._aprint_16(*values, sep=sep, end=end, color=color, backtick=backtick)

    def add_boot(self, welcome_msg: str | None = None) -> None:
        with open("../asm/boot.asm", "r", encoding="utf-8") as f:
            content = f.read()
        if welcome_msg:
            content = content.replace("{{WELCOME_MSG}}", welcome_msg)
        self.asm_code = content.splitlines()

    def clear_register(self, register: str, method: Literal["xor", "mov", "sub"] = "xor"):
        if method == "xor":
            self.asm_code.append(f"   xor {register}, {register}")
        elif method == "mov":
            self.asm_code.append(f"   mov {register}, 0")
        elif method == "sub":
            self.asm_code.append(f"   sub {register}, {register}")

    def clear_all_registers(self):
        for reg in ("ax", "bx", "cx", "dx", "si", "di", "bp"):
            self.clear_register(reg, method="xor")
        self.asm_code.extend(
            [
                "   mov fs, ax",
                "   mov gs, ax",
                "   cld",
            ]
        )

    def init_enviroment16(
        self, cli: bool = True, cld: bool = False, save_drive: bool = False, flush_cs: bool = False
    ):
        self.asm_code.extend(
            [
                "[bits 16]",
                f"[org {self.address_bios_boot}]",
                "   jmp start",
                # "db_section:",
                "start:",
            ]
        )
        if cli:
            self.asm_code.append("    cli")
        if cld:
            self.asm_code.append("    cld")
        self.clear_register("ax")
        for sr in ("ds", "es", "ss"):
            self.asm_code.append(f"    mov {sr}, ax")
        self.asm_code.append(f"    mov sp, {self.address_bios_boot}")
        if flush_cs:
            self.asm_code.extend(["    jmp 0x0000:.flush_cs", ".flush_cs:"])
        if save_drive:
            self.asm_code.append("    mov [boot_drive], dl")

    def stoooop(self, cli: bool = False):
        if cli:
            self.asm_code.append("  cli")
        self.asm_code.extend(["   hlt", "   jmp $"])

    def init_environment32(self, cli: bool = False, stop: bool = False):
        self.asm_code.extend(
            [
                "   mov ax, 0x10",
                "   mov ds, ax",
                "   mov es, ax",
                "   mov fs, ax",
                "   mov gs, ax",
                "   mov ss, ax",
                f"  mov esp, {self.address_bios_boot}",
            ]
        )
        if stop:
            self.stoooop(cli=cli)

    def enable_A20(self, method: Literal["fast", "keyboard", "bios"] = "fast"):
        if method == "fast":
            self.asm_code.extend(["   in al, 0x92", "   or al, 2", "    out 0x92, al"])
        elif method == "keyboard":
            self.asm_code.extend(
                [
                    "wait_kbd:",
                    "    in al, 0x64",
                    "    test al, 2",
                    "    jnz wait_kbd",
                    "    mov al, 0xD1",
                    "    out 0x64, al",
                    "wait_kbd2:",
                    "    in al, 0x64",
                    "    test al, 2",
                    "    jnz wait_kbd2",
                    "    mov al, 0xDF",
                    "    out 0x60, al",
                ]
            )
        elif method == "bios":
            self.asm_code.extend(
                [
                    "   mov ax, 0x2401",
                    "   int 0x15",
                ]
            )

    def enable_protected_mode(
        self, method: Literal["or", "inc", "lmsw", "bts"] = "or", preserve_eax: bool = False
    ):
        if method == "or":
            if preserve_eax:
                self.asm_code.extend(
                    ["push eax", "mov eax, cr0", "or eax, 1", "mov cr0, eax", "pop eax"]
                )
            else:
                self.asm_code.extend(["mov eax, cr0", "or eax, 1", "mov cr0, eax"])

        elif method == "inc":
            if preserve_eax:
                self.asm_code.extend(
                    ["push eax", "mov eax, cr0", "inc eax", "mov cr0, eax", "pop eax"]
                )
            else:
                self.asm_code.extend(["mov eax, cr0", "inc eax", "mov cr0, eax"])

        elif method == "lmsw":
            self.asm_code.extend(["mov ax, 0x0001", "lmsw ax"])

        elif method == "bts":
            if preserve_eax:
                self.asm_code.extend(
                    ["push eax", "mov eax, cr0", "bts eax, 0", "mov cr0, eax", "pop eax"]
                )
            else:
                self.asm_code.extend(["mov eax, cr0", "bts eax, 0", "mov cr0, eax"])

    def load_gdt(self):
        self.asm_code.append("lgdt [gdt32_ptr]")

    def jump_protected_mode(self, address: str = "0x08"):
        self.asm_code.append(f"jmp {address}:protected_mode")
        self.asm_code.extend(["[bits 32]", "protected_mode:"])
        if self.automode:
            self.mode = "32bit"

    def setup_gdt(
        self,
        limit_code: int = 0xFFFF,
        base_code: int = 0x00000000,
        active_code: bool = True,
        right_code: str | int = 0,
        descriptor_type_code: Literal[0, 1] = 1,
        conforming_code: bool = False,
        read_code_data: bool = True,
        accessed: bool = False,
        # ----------------------
        limit_data: int = 0xFFFF,
        base_data: int = 0x00000000,
        active_data: bool = True,
        right_data: str | int = 0,
        descriptor_type_data: Literal[0, 1] = 1,
        writable_data: bool = True,
        accessed_data: bool = False,
        size_data: bool = True,
        granularity_data: bool = True,
    ):
        base_code_hex = f"{base_code:08X}"
        base_data_hex = f"{base_data:08X}"
        ring_map = {
            "god": 0,
            "superroot": 0,
            "ring0": 0,
            "root": 1,
            "ring1": 1,
            "admin": 2,
            "ring2": 2,
            "user": 3,
            "ring3": 3,
            "guest": 3,
        }
        access_code = (
            (active_code << 7)
            | (ring_map.get(right_code, right_code) << 5)
            | (descriptor_type_code << 4)
            | (1 << 3)
            | (conforming_code << 2)
            | (read_code_data << 1)
            | (accessed << 0)
        )
        access_data = (
            (active_data << 7)
            | (ring_map.get(right_data, right_data) << 5)
            | (descriptor_type_data << 4)
            | (0 << 3)
            | (0 << 2)
            | (writable_data << 1)
            | (accessed_data << 0)
        )
        flags_code = (1 << 7) | (1 << 6) | ((limit_code >> 16) & 0xF)
        flags_data = (granularity_data << 7) | (size_data << 6) | ((limit_data >> 16) & 0xF)

        self.asm_code.extend(
            [
                "gdt_start:",
                "gdt_null:",
                "    dd 0x0",
                "    dd 0x0",
                "",
                "gdt_code:",
                f"    dw {limit_code:04X}",
                f"    dw 0x{base_code_hex[4:]}",
                f"    db 0x{base_code_hex[2:4]}",
                f"    db {access_code:08b}b",
                f"    db {flags_code:08b}b",
                f"    db 0x{base_code_hex[0:2]}",
                "",
                "gdt_data:",
                f"    dw {limit_data:04X}",
                f"    dw 0x{base_data_hex[4:]}",
                f"    db 0x{base_data_hex[2:4]}",
                f"    db {access_data:08b}b",
                f"    db {flags_data:08b}b",
                f"    db 0x{base_data_hex[0:2]}",
                "",
                "gdt_end:",
                "",
                "gdt32_ptr:",
                "    dw gdt_end - gdt_start - 1",
                "    dd gdt_start",
            ]
        )

    def finalize_disk_sector(self):
        self.asm_code.extend(
            [
                "   times 510-($-$$) db 0",
                "   dw 0xAA55",
            ]
        )

    def set_vesa_mode(
        self,
        resolution: Literal["640x480", "800x600", "1024x768", "1280x1024", "1920x1080"] = "640x480",
        bit_depth: Literal[8, 16, 24, 32] = 32,
    ) -> None:
        """
        Sets a VESA video mode by human-readable resolution.
        """
        mode_map = {
            "640x480": 0x112,
            "800x600": 0x115,
            "1024x768": 0x118,
            "1280x1024": 0x11B,
            "1920x1080": 0x165,
        }

        target_mode = mode_map[resolution]

        self.asm_code.extend(
            [
                "mov ax, 0x4F02",
                f"mov bx, {target_mode:04X}h",
                "int 0x10",
            ]
        )

    def set_vga_mode(self, mode: Literal["80x25", "40x25", "80x50", "320x200"] = "80x25") -> None:
        """
        Sets a standard VGA text/graphics mode by human-readable name.
        """
        mode_map = {
            "80x25": 0x03,  # Text, 16 colors
            "40x25": 0x01,  # Text, 16 colors
            "80x50": 0x03,  # Text (80x50 needs extra register tweak, fallback to 0x03)
            "320x200": 0x13,  # Graphics, 256 colors
        }

        target_mode = mode_map[mode]

        self.asm_code.extend(
            [
                f"mov ax, {target_mode:04X}h",
                "int 0x10",
            ]
        )

    def asleep_16(self, time_us: int):
        if self.automode:
            raise RuntimeError("asleep_16 unavailable, pls disable automode")

        self._asleep_16(time_us)

    def alseep_32(self, time_us: int):
        if self.automode:
            raise RuntimeError("asleep_32 unavailable, pls disable automode")
        self._asleep_32(time_us)

    def asleep_auto(self, time_us: int):
        if not self.automode:
            raise RuntimeError("asleep_auto unavailable, pls enable automode")
        if self.mode == "16bit":
            self._asleep_16(time_us)
        elif self.mode == "32bit":
            self._asleep_32(time_us)
