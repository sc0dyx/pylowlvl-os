; bruteforce_all_modes.asm
; Перебирает ВСЕ видеорежимы (0x00-0xFF) с выводом на экран
[bits 16]
[org 0x7C00]

    jmp main           ; прыгаем через процедуры и данные

; ===== ПРОЦЕДУРЫ =====
bios_print:
    pusha
.loop:
    lodsb
    test al, al
    jz .done
    mov ah, 0x0E
    int 0x10
    jmp .loop
.done:
    popa
    ret

print_hex_byte:
    push ax
    shr al, 4
    call print_nibble
    pop ax
    and al, 0x0F
    call print_nibble
    ret

print_nibble:
    cmp al, 10
    jb .digit
    add al, 'A' - 10
    jmp .do
.digit:
    add al, '0'
.do:
    mov ah, 0x0E
    int 0x10
    ret

; ===== ДАННЫЕ =====
msg_mode db 'Mode: ', 0
msg_done db ' Done!', 13, 10, 0
msg_alive db '!', 0

; ===== ОСНОВНОЙ КОД =====
main:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00
    sti

    mov cx, 256         ; 256 режимов (0x00-0xFF)
    xor bx, bx          ; начинаем с режима 0

try_mode:
    push cx
    push bx
    
    ; Выводим "Mode: XX"
    mov si, msg_mode
    call bios_print
    mov ax, bx
    call print_hex_byte
    
    ; Короткая задержка
    mov cx, 0x0005
delay1:
    push cx
    mov cx, 0xFFFF
delay1_inner:
    loop delay1_inner
    pop cx
    loop delay1
    
    ; Устанавливаем видеорежим
    pop bx
    mov ax, bx
    int 0x10
    
    ; Пробуем вывести '!' в этом режиме
    mov ah, 0x0E
    mov al, '!'
    int 0x10
    
    ; Задержка чтобы увидеть результат (3 секунды)
    mov cx, 0x0010
delay2:
    push cx
    mov cx, 0xFFFF
delay2_inner:
    loop delay2_inner
    pop cx
    loop delay2
    
    pop cx
    inc bx
    loop try_mode

    ; Возвращаемся в текстовый режим
    mov ax, 0x0003
    int 0x10
    
    mov si, msg_done
    call bios_print
    
    jmp $

; ===== ЗАГРУЗОЧНЫЙ СЕКТОР =====
times 510-($-$$) db 0
dw 0xAA55
