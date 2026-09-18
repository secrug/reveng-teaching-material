/* asp-escape : AURA-7 coprocessor sandbox (pwn/asp-escape)  [rev + pwn]
 *
 * Runs an uploaded ASP program in a "sandbox": the program may only touch the
 * VM's registers and a 64-byte data memory. Except the memory index is a full
 * byte (0..255) with NO bounds check, and the VM struct places a function
 * pointer immediately after that 64-byte array:
 *
 *     struct asp { unsigned char reg[16];   // offset 0
 *                  unsigned char mem[64];    // offset 16..79
 *                  void (*trap)(struct asp*); // offset 80  == mem[64]
 *                };
 *
 * So a ST to mem index 64..71 overwrites the 8 bytes of `trap`. Set it to &win
 * with eight stores, then execute TRAP -> native code execution -> flag.
 *
 * This is a VM-escape: understand the ISA (rev), find the missing bounds check
 * (rev), then craft a program that writes out of bounds and pivots (pwn).
 *
 * Build:  gcc -O0 -fno-stack-protector -no-pie -o asp-escape asp-escape.c
 *   non-PIE so &win is fixed. The mem[64] -> trap adjacency is a struct-layout
 *   fact (offset 80, 8-aligned), independent of stack frame quirks.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

struct asp {
    unsigned char reg[16];
    unsigned char mem[64];
    void (*trap)(struct asp *);
};

void win(struct asp *v) { (void)v; system("/bin/cat flag.txt"); }
static void safe_trap(struct asp *v) { (void)v; puts("[asp] trap handler: nothing to do"); }

enum { OP_HALT = 0, OP_MOVI = 1, OP_LD = 2, OP_ST = 3, OP_TRAP = 4 };

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);

    struct asp v;
    memset(&v, 0, sizeof v);
    v.trap = safe_trap;

    unsigned char prog[1024];
    printf("AURA-7 ASP sandbox.\nprogram length: ");
    char line[32];
    if (!fgets(line, sizeof line, stdin)) return 0;
    long n = strtol(line, NULL, 0);
    if (n <= 0 || n > (long)sizeof prog) { puts("bad length"); return 1; }
    if (fread(prog, 1, (size_t)n, stdin) != (size_t)n) { puts("short read"); return 1; }

    for (long pc = 0; pc < n; ) {
        unsigned char op = prog[pc++];
        if (op == OP_HALT) break;
        else if (op == OP_MOVI) { unsigned char r = prog[pc++], imm = prog[pc++]; v.reg[r & 15] = imm; }
        else if (op == OP_LD)   { unsigned char d = prog[pc++], idx = prog[pc++];
                                  v.reg[d & 15] = v.mem[v.reg[idx & 15]]; }        /* OOB read  */
        else if (op == OP_ST)   { unsigned char idx = prog[pc++], s = prog[pc++];
                                  v.mem[v.reg[idx & 15]] = v.reg[s & 15]; }        /* OOB WRITE */
        else if (op == OP_TRAP) { v.trap(&v); }
        else { puts("bad opcode"); return 1; }
    }
    puts("[asp] program halted");
    return 0;
}
