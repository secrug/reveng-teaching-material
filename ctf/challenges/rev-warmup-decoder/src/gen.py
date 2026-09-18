#!/usr/bin/env python3
"""rev/warmup-decoder ("Signal Primer") — Intro/100.

DELIBERATELY AI-solvable. This is the calibration challenge: a standard,
recall-friendly transform with a visible key. Its job is to show the team what
AI is genuinely good at (recognizable shapes with public precedent) so they
don't waste effort hand-doing what the machine one-shots. The writeup says so.

Transform (per byte i): t = rol8(flag[i], 3) ^ KEY[i % len(KEY)]
KEY is an ASCII string left in .rodata on purpose (strings finds it).
Every step is invertible: flag[i] = ror8(t ^ KEY[i%kl], 3).

Emits src/warmup-decoder.c ; self-tests when run with --selftest.
"""
import argparse, sys
MASK = 0xFF
KEY = b"AURA-SIGNAL-KEY"
def rol8(v, n): n &= 7; return ((v << n) | (v >> (8 - n))) & MASK
def ror8(v, n): n &= 7; return ((v >> n) | (v << (8 - n))) & MASK
def transform(c, i): return rol8(c, 3) ^ KEY[i % len(KEY)]
def invert(t, i):   return ror8(t ^ KEY[i % len(KEY)], 3)

def carr(name, data): return f"static const unsigned char {name}[] = {{{','.join(map(str,data))}}};\n"

C_TEMPLATE = r'''/* warmup-decoder : AURA-7 signal primer (auto-generated) */
#include <stdio.h>
#include <string.h>
static const char *KEY = "%KEY%";      /* left visible on purpose */
%EXPECTED%
static unsigned char ror8(unsigned char v,int n){n&=7;return (unsigned char)((v>>n)|(v<<(8-n)));}
static unsigned char rol8(unsigned char v,int n){n&=7;return (unsigned char)((v<<n)|(v>>(8-n)));}
int main(void){
    unsigned char in[256];
    if(!fgets((char*)in,sizeof in,stdin)){puts("nope.");return 1;}
    size_t n=strlen((char*)in);
    while(n && (in[n-1]=='\n'||in[n-1]=='\r')) in[--n]=0;
    size_t kl=strlen(KEY), en=sizeof expected;
    if(n!=en){puts("nope.");return 1;}
    for(size_t i=0;i<n;i++){
        unsigned char t=(unsigned char)(rol8(in[i],3) ^ (unsigned char)KEY[i%kl]);
        if(t!=expected[i]){puts("nope.");return 1;}
    }
    puts("Primer accepted. That input is the flag.");
    return 0;
}
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flag", default="AURA{w4rmup_the_machine_is_good_at_this}")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    fb = a.flag.encode()
    expected = bytes(transform(c, i) for i, c in enumerate(fb))
    if a.selftest:
        assert all(invert(transform(c, i), i) == c for i in range(len(KEY)) for c in range(256))
        assert bytes(invert(expected[i], i) for i in range(len(expected))) == fb
        print("warmup-decoder OK:", a.flag, "expected=", expected.hex()); return
    c = C_TEMPLATE.replace("%KEY%", KEY.decode()).replace("%EXPECTED%", carr("expected", expected))
    sys.stdout.write(c)
    sys.stderr.write(f"[gen] flag={a.flag!r} expected={expected.hex()}\n")

if __name__ == "__main__":
    main()
