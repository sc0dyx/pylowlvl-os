; minimal_boot.asm
[bits 16]           ; (1)
[org 0x7C00]        ; (2)

start:
    cli             ; (3)
    xor ax, ax      ; (4)
    mov ds, ax      ; (5)
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00  ; (6)

    in al, 0x92     ; (7)
    or al, 2        ; (8)
    out 0x92, al    ; (9)

    lgdt [gdt32_ptr] ; (10)

    mov eax, cr0    ; (11)
    or eax, 1       ; (12)
    mov cr0, eax    ; (13)

    jmp 0x08:protected_mode ; (14)

[bits 32]           ; (15)
protected_mode:
    mov ax, 0x10    ; (16)
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov esp, 0x7C00 ; (17)

    cli             ; (18)
    hlt             ; (19)
    jmp $           ; (20)

; ============ GDT ============
gdt_start:          ; (21)

gdt_null:           ; (22)
    dd 0x0
    dd 0x0

gdt_code:           
    dw 0xFFFF       ; 
    dw 0x0000       ; 
    db 0x00         ; 
    db 10011010b    ; 
    db 11001111b    ; 
    db 0x00         ; 

gdt_data:           ;
    dw 0xFFFF
    dw 0x0000
    db 0x00
    db 10010010b    ;
    db 11001111b
    db 0x00

gdt_end:

gdt32_ptr:          ; (25)
    dw gdt_end - gdt_start - 1  ; 
    dd gdt_start                ; 

times 510-($-$$) db 0 
dw 0xAA55             
