# Reference Cards

Five printed one-pagers. **These are what students keep** — the durable takeaway,
not the slides. Print them double-sided (cards 1+4, 2+3, 5 alone), issue as the
sessions call for them (issue schedule below), and reprint spares each session.

Physical cards get used during the no-tools segments in a way a PDF never does.

| Card | Title | Issue at |
|---|---|---|
| 1 | The Triage Toolbox | S1 |
| 2 | x86-64 Quick Reference | end of S1 (for S2) |
| 3 | The System V AMD64 ABI | S4 |
| 4 | gdb / pwndbg Field Guide | S6 (for S7) |
| 5 | RE Methodology + Shape Catalogue | S9 |

---

## Card 1 — The Triage Toolbox

**First contact with any file. Run top to bottom.**

```
file X            # what is it? (a GUESS — confirm with xxd)
xxd X | head      # the ground truth: the actual bytes
strings -n 8 X    # printable runs: errors, formats, banners, paths
nm -C X           # symbols, if not stripped
readelf -h X      # ELF header: arch, type, entry
readelf -d X      # dynamic: NEEDED libraries, or "not a dynamic exe"
readelf -S X      # sections
strace ./X        # syscalls: files, network, env (what it TOUCHES)
ltrace ./X        # library calls (what it CALLS)
```

**Golden rule:** `file` is a hypothesis. `xxd` is evidence. Always confirm.

**Magic numbers:** `7f 45 4c 46` ELF · `89 50 4e 47` PNG · `1f 8b` gzip ·
`4d 5a` PE(MZ) · `ca fe ba be` Mach-O fat / Java class.

**Endianness (x86 is little-endian):** bytes `41 55 52 41` in memory = the string
"AURA"; as a u32 = `0x41525541`. A version that reads as an absurd number means
you read the byte order backwards.

---

## Card 2 — x86-64 Quick Reference

**Registers** (64 / 32 / 16 / 8):
```
rax eax  ax  al     rsi esi  si  sil    r8  r8d  r8w  r8b
rbx ebx  bx  bl     rdi edi  di  dil    ...  r9–r15 likewise
rcx ecx  cx  cl     rbp ebp  bp  bpl    rip = instruction pointer
rdx edx  dx  dl     rsp esp  sp  spl    rflags = ZF SF CF OF ...
```
**TRAP: writing a 32-bit reg (`eax`) ZEROES the upper 32 bits of `rax`.**
Writing 16/8-bit does not.

**Core instructions:**
```
mov  d,s     d = s              lea  d,[expr]  d = address (arithmetic, no load!)
movzx/movsx  zero/sign-extend   add/sub/imul   arithmetic
and/or/xor/not  bitwise         shl/shr/sar    shift (sar = signed)
cmp  a,b     flags of a-b       test a,b       flags of a&b
push/pop     stack              call/ret       call/return
jmp          unconditional      jcc            conditional (see Card 3)
```
**Idioms:** `xor eax,eax` = set to 0 · `test rax,rax; je` = "is rax zero?"

**Addressing** `[base + index*scale + disp]` (scale ∈ 1,2,4,8):
```
[rbx]              M[rbx]
[rbx+8]            M[rbx+8]            constant offset → struct field
[rbx+rcx*4]        M[rbx+4*rcx]        variable*scale  → array, elem size = scale
[rip+disp]         a global
lea rax,[rdi+rdi*2]   rax = rdi*3      (lea = free arithmetic)
```
**The scale is the array element size, handed to you free.**

---

## Card 3 — The System V AMD64 ABI

**Integer / pointer arguments, in order:**
```
  rdi   rsi   rdx   rcx   r8   r9   → then the stack (right to left)
   1     2     3     4     5    6
```
**Return value:** `rax` (128-bit: `rdx:rax`). Floats: `xmm0–xmm7` args, `xmm0` ret.

**Register preservation:**
```
Callee-saved (fn must restore):  rbx  rbp  r12 r13 r14 r15  rsp
Caller-saved (may be clobbered): rax rcx rdx rsi rdi  r8 r9 r10 r11
```

**Recovering a signature — the one move:**
> A register **read before it is written** was an incoming argument.
> `rdx` read early ⇒ at least 3 arguments. `rax` meaningful at `ret` ⇒ non-void.

**Comparison → jump (after `cmp a, b`):**
```
je/jz  a==b    jne/jnz a!=b
SIGNED:   jl  jle  jg  jge      (<, <=, >, >=)
UNSIGNED: jb  jbe  ja  jae      (<, <=, >, >=)
```
**Signed vs unsigned jumps reveal a type the compiler erased.**
**The compiler branches on the NEGATION:** source `if (x>5)` → `jle` (jump away
when false).

**Stack frame (`-O0`):**
```
push rbp; mov rbp,rsp; sub rsp,N   ← prologue      locals at [rbp-8], [rbp-16]...
...                                                 saved ret addr at [rbp+8]
leave; ret                         ← epilogue
```
`-O2` may omit `rbp` (everything off `rsp`), use the red zone (128 B below rsp),
or tail-call (`jmp` to another fn instead of `call`).

---

## Card 4 — gdb / pwndbg Field Guide

**Start / step:**
```
gdb ./x            starti     stop at very first instruction
break main / b *0xADDR        run [args]      continue / c
si   step one instruction     ni   step over call     finish   run to return
```
**Inspect:**
```
info registers [reg]          x/8gx $rsp    8 giant hex from rsp
x/20i $pc     20 instrs       x/s  $rdi     string at rdi
x/1bx $pc     1 byte (see the 0xCC of a breakpoint!)
p/x $rax      print rax hex   p $eflags     flags
```
**Watch / conditional:**
```
watch  <expr>   break on WRITE      rwatch <expr>  break on READ
break f if x==5      conditional
```
**Breakpoint = an int3 (0xCC) byte patched over the instruction.** A watchpoint is
hardware — the CPU traps on access, no byte patching.

**Scripting (log without stopping):**
```
break *0xADDR
commands
  silent
  printf "acc=%#x\n", $rax
  continue
end
```
Python: `gdb.Breakpoint`, override `stop()` returning `False` to log-and-continue.

**Patching:** `je`(0x74)↔`jne`(0x75) · any jump → `nop`(0x90) · stub a fn →
`ret`(0xc3). *A patch is a hypothesis test, not a victory.*

---

## Card 5 — RE Methodology + Shape Catalogue

**The triage order — 5 steps before you read one instruction:**
```
1. What is it?        file, readelf   (arch, linkage, stripped?)
2. What does it touch? strace/ltrace   (files, net, env)
3. What can it say?   strings          (errors, formats, paths)
4. What does it call?  PLT list         (crypto? net? both?)
5. Where's my target?  xref a string/import → the code
   THEN read code — only the 2% triage pointed you to.
```

**The hypothesis loop:**
```
FORM → PREDICT (what I'd observe if true) → TEST (gdb/observe) → RECORD → repeat
```
Keep dead ends. A dead end is a result. Notes make findings reproducible.

**Algorithm shapes — recognise, then look up:**
```
AES       S-box 63 7c 77 7b ...            base64  alphabet A–Za–z0–9+/, >>6 &0x3f
SHA-256   init 6a09e667 ...; 64 rounds     CRC32   256-entry table, xor+shift/byte
MD5       67452301 ...                     XOR     single byte xor'd across buffer
state machine  switch on a state var in a loop
parser         char-class checks + a cursor pointer advancing
protocol       read length, then read that many bytes
```

**Specialised zoo — recognise, DON'T memorise (look it up):**
```
Packer     tiny .text, huge high-entropy .data, odd entry stub   → unpack (upx -d)
Anti-debug ptrace(TRACEME); timing; scan self for 0xCC           → patch/attach
Custom VM  fetch-decode-execute loop over a bytecode array       → recover opcodes
Obfusc.    opaque predicates, bogus flow, encrypted strings      → deobfusc. dynamically
```

**The whole job:** decide *which* code to read (nothing does this for you — it
depends on your goal). Use generators (decompiler, LLM) for speed; settle truth
with evidence (a register, an offset, a breakpoint). You can only tell the
difference because you can read the evidence.
