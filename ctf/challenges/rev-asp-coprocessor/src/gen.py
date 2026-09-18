#!/usr/bin/env python3
"""rev/asp-coprocessor ("The Coprocessor") — Hard/450.

The full AURA Signal Processor: a transport-triggered architecture (only MOV /
MOVI / HALT) extended with FUNCTION UNITS (ADD/XOR/ROL/AND/CMP) and CONTROL FLOW
via a program-counter port. Unlike `signal-lock` (a straight-line unrolled
pipeline), the flag checker here is a COMPACT LOOP with a conditional branch on
end-of-input. The solver must recover:
  * that writes to unit ports trigger computation (transport-triggered),
  * that writes to the PC ports (0xF0 unconditional, 0xF2 if-equal) are jumps,
  * the loop body's per-byte transform and its position-dependent terms.

Transform per byte i:  t = ( rol8(c ^ K1, i&7) + (K2 + i*K4) ) & 0xFF ^ K3
(position term is an arithmetic progression the loop maintains in a register).

AI target: novel machine model + control-flow recovery + long inference chain.
No familiar interpreter-loop silhouette; recall actively misleads.
Emits src/asp-coprocessor.c ; --selftest fully validates.
"""
import argparse, sys
MASK=0xFF
K1,K2,K3,K4 = 0x5A,0x1B,0x3C,0x11
OP_HALT,OP_MOV,OP_MOVI = 0x00,0x01,0x02
# ports
INPUT,CHECK,EOF = 0x10,0x11,0x13
ADD_A,ADD_B,ADD_R = 0xA0,0xA1,0xA2
XOR_A,XOR_B,XOR_R = 0xB0,0xB1,0xB2
ROL_V,ROL_N,ROL_R = 0xC0,0xC1,0xC2
AND_A,AND_B,AND_R = 0xE0,0xE1,0xE2
CMP_A,CMP_B,FLG   = 0xD0,0xD1,0xD2
JMP,JZF           = 0xF0,0xF2
def rol8(v,n): n&=7; return ((v<<n)|(v>>(8-n)))&MASK
def ror8(v,n): n&=7; return ((v>>n)|(v<<(8-n)))&MASK
def transform(c,i): return ((rol8(c^K1, i&7) + (K2 + i*K4)) & MASK) ^ K3
def invert(t,i):
    u = t ^ K3
    u = (u - (K2 + i*K4)) & MASK
    u = ror8(u, i&7)
    return u ^ K1

# ---------- assembler with labels ----------
def assemble():
    ins=[]  # list of ('MOV'|'MOVI'|'HALT', dst, src, maybe label-ref)
    labels={}
    prog=bytearray(); fixups=[]  # (byte_index_of_operand, label)
    def emit(op,dst=0,src=0,lref=None):
        idx=len(prog)
        prog.append(op); prog.append(dst)
        if lref is not None: fixups.append((len(prog),lref)); prog.append(0)
        else: prog.append(src)
    def label(name): labels[name]=len(prog)
    R0,R1,R2 = 0x00,0x01,0x02
    emit(OP_MOVI,R2,K2)                 # R2 = K2
    label("loop")
    emit(OP_MOV, CMP_A, EOF)            # CMP.A = eof
    emit(OP_MOVI,CMP_B,1)               # FLG = (eof==1)
    emit(OP_MOVI,JZF,0,lref="done")     # if FLG -> done
    emit(OP_MOV, R0, INPUT)             # c
    emit(OP_MOV, XOR_A,R0); emit(OP_MOVI,XOR_B,K1); emit(OP_MOV,R0,XOR_R)   # c ^= K1
    emit(OP_MOV, AND_A,R1); emit(OP_MOVI,AND_B,7)                            # AND.R = R1&7
    emit(OP_MOV, ROL_V,R0); emit(OP_MOV,ROL_N,AND_R); emit(OP_MOV,R0,ROL_R)  # rol8(R0,R1&7)
    emit(OP_MOV, ADD_A,R0); emit(OP_MOV,ADD_B,R2);  emit(OP_MOV,R0,ADD_R)    # + R2
    emit(OP_MOV, XOR_A,R0); emit(OP_MOVI,XOR_B,K3); emit(OP_MOV,R0,XOR_R)    # ^ K3
    emit(OP_MOV, CHECK,R0)                                                   # compare
    emit(OP_MOV, ADD_A,R2); emit(OP_MOVI,ADD_B,K4); emit(OP_MOV,R2,ADD_R)    # R2 += K4
    emit(OP_MOV, ADD_A,R1); emit(OP_MOVI,ADD_B,1);  emit(OP_MOV,R1,ADD_R)    # R1 += 1
    emit(OP_MOVI,JMP,0,lref="loop")                                          # goto loop
    label("done"); emit(OP_HALT)
    for pos,name in fixups:
        assert labels[name] < 256, "program too big for single-byte targets"
        prog[pos]=labels[name]
    return bytes(prog)

# ---------- interpreter ----------
def run_vm(prog, inp, expected):
    reg=[0]*256
    aA=aX=aR=aAn=aC=0; rA=rX=rR=rAn=0; flg=0
    incur=[0]; outcur=[0]; fail=[False]
    def rd(p):
        nonlocal flg
        if p==INPUT:
            if incur[0]>=len(inp): fail[0]=True; return 0
            v=inp[incur[0]]; incur[0]+=1; return v
        if p==EOF: return 1 if incur[0]>=len(inp) else 0
        if p==ADD_R: return rA
        if p==XOR_R: return rX
        if p==ROL_R: return rR
        if p==AND_R: return rAn
        if p==FLG:   return flg
        return reg[p]
    pc=0; steps=0
    while pc < len(prog):
        steps+=1
        if steps>1_000_000: raise RuntimeError("runaway")
        op=prog[pc]
        if op==OP_HALT: break
        dst=prog[pc+1]; src=prog[pc+2]
        val = rd(src) if op==OP_MOV else src   # MOVI: src field is immediate
        # writes
        if dst==JMP: pc=val; continue
        if dst==JZF:
            if flg!=0: pc=val; continue
            pc+=3; continue
        if dst==CHECK:
            if outcur[0]>=len(expected) or val!=expected[outcur[0]]: fail[0]=True
            outcur[0]+=1
        elif dst==ADD_A: aA=val
        elif dst==ADD_B: rA=(aA+val)&MASK
        elif dst==XOR_A: aX=val
        elif dst==XOR_B: rX=(aX^val)&MASK
        elif dst==ROL_V: aR=val
        elif dst==ROL_N: rR=rol8(aR,val)
        elif dst==AND_A: aAn=val
        elif dst==AND_B: rAn=(aAn & val)&MASK
        elif dst==CMP_A: aC=val
        elif dst==CMP_B: flg=1 if aC==val else 0
        else: reg[dst]=val
        pc+=3
    return (not fail[0]) and incur[0]==len(inp) and outcur[0]==len(expected)

def carr(name,data): return f"static const unsigned char {name}[] = {{{','.join(map(str,data))}}};\n"

C_TEMPLATE=r'''/* asp-coprocessor : full AURA Signal Processor verifier (auto-generated) */
#include <stdio.h>
#include <string.h>
%PROG%
%EXPECTED%
static unsigned char rol8(unsigned char v,int n){n&=7;return (unsigned char)((v<<n)|(v>>(8-n)));}
int main(void){
    unsigned char reg[256]; memset(reg,0,sizeof reg);
    unsigned char aA=0,aX=0,aR=0,aAn=0,aC=0, rA=0,rX=0,rR=0,rAn=0, flg=0;
    unsigned char in[256];
    if(!fgets((char*)in,sizeof in,stdin)){puts("nope.");return 1;}
    size_t n=strlen((char*)in);
    while(n && (in[n-1]=='\n'||in[n-1]=='\r')) in[--n]=0;
    size_t incur=0,outcur=0,pc=0; long steps=0; int fail=0;
    const size_t proglen=sizeof prog, explen=sizeof expected;
    while(pc<proglen){
        if(++steps>1000000){fail=1;break;}
        unsigned char op=prog[pc];
        if(op==0x00) break;
        unsigned char dst=prog[pc+1], src=prog[pc+2], val;
        if(op==0x01){
            if(src==0x10){ if(incur>=n){fail=1;val=0;} else val=in[incur++]; }
            else if(src==0x13) val=(incur>=n)?1:0;
            else if(src==0xA2) val=rA; else if(src==0xB2) val=rX;
            else if(src==0xC2) val=rR; else if(src==0xE2) val=rAn;
            else if(src==0xD2) val=flg; else val=reg[src];
        } else if(op==0x02){ val=src; } else { puts("nope."); return 1; }
        if(dst==0xF0){ pc=val; continue; }
        if(dst==0xF2){ if(flg){ pc=val; continue; } pc+=3; continue; }
        if(dst==0x11){ if(outcur>=explen || val!=expected[outcur]) fail=1; outcur++; }
        else if(dst==0xA0) aA=val; else if(dst==0xA1) rA=(unsigned char)(aA+val);
        else if(dst==0xB0) aX=val; else if(dst==0xB1) rX=(unsigned char)(aX^val);
        else if(dst==0xC0) aR=val; else if(dst==0xC1) rR=rol8(aR,val);
        else if(dst==0xE0) aAn=val; else if(dst==0xE1) rAn=(unsigned char)(aAn & val);
        else if(dst==0xD0) aC=val; else if(dst==0xD1) flg=(aC==val)?1:0;
        else reg[dst]=val;
        pc+=3;
    }
    if(!fail && incur==n && outcur==explen){
        puts("Coprocessor unlocked. The input you entered is the flag.");
        return 0;
    }
    puts("nope."); return 1;
}
'''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--flag", default="AURA{a_transport_triggered_l00p_w1th_branches}")
    ap.add_argument("--selftest", action="store_true")
    a=ap.parse_args()
    fb=a.flag.encode()
    prog=assemble()
    expected=bytes(transform(c,i) for i,c in enumerate(fb))
    if a.selftest:
        assert all(invert(transform(c,i),i)==c for i in range(64) for c in range(256))
        assert run_vm(prog,fb,expected) is True, "correct flag rejected"
        bad=bytearray(fb); bad[9]^=1
        assert run_vm(prog,bytes(bad),expected) is False, "mutation accepted"
        assert run_vm(prog,fb+b"z",expected) is False, "too-long accepted"
        assert run_vm(prog,fb[:-1],expected) is False, "too-short accepted"
        assert bytes(invert(expected[i],i) for i in range(len(expected)))==fb, "solver failed"
        print(f"asp-coprocessor OK: {a.flag}")
        print(f"  prog={len(prog)}B ({len(prog)//3} instrs)  expected={expected.hex()}")
        return
    c=(C_TEMPLATE.replace("%PROG%",carr("prog",prog)).replace("%EXPECTED%",carr("expected",expected)))
    sys.stdout.write(c)
    sys.stderr.write(f"[gen] flag={a.flag!r} prog={len(prog)}B expected={expected.hex()}\n")

if __name__=="__main__":
    main()
