import sys

sys.path.insert(0, "..")  # добавить src/ в путь

from pylowlvl_os.x86_64.pyabstract import PyLowLvl
from pylowlvl_os.builder import PLowBuilder

boot = PyLowLvl(aprint16_method="bios_teletype")
boot.init_enviroment16(cli=False)
boot.clear_all_registers()

boot.set_vga_mode("40x25")
boot.aprint_auto("Hello world!")
boot.asleep_auto(3_000_000)
boot.set_vga_mode("80x50")
boot.aprint_auto("Hello world!")
boot.asleep_auto(3_000_000)
boot.aprint_auto("Welcome to pylowlvl_os")
boot.asleep_auto(3_000_000)
boot.stoooop()
boot.finalize_disk_sector()
print("\n".join(boot.asm_code))
build = PLowBuilder(boot)
build.run("boot.bin")
