/* asp-coprocessor : full AURA Signal Processor verifier (auto-generated) */
#include <stdio.h>
#include <string.h>
static const unsigned char prog[] = {2,2,27,1,208,19,2,209,1,2,242,81,1,0,16,1,176,0,2,177,90,1,0,178,1,224,1,2,225,7,1,192,0,1,193,226,1,0,194,1,160,0,1,161,2,1,0,162,1,176,0,2,177,60,1,0,178,1,17,0,1,160,2,2,161,17,1,2,162,1,160,1,2,161,1,1,1,162,2,240,3,0,0,0};

static const unsigned char expected[] = {10,118,97,26,77,235,254,149,247,22,169,35,181,162,47,13,12,164,209,203,126,27,92,138,206,124,213,171,161,105,159,144,84,30,41,195,243,171,151,115,203,122,145,211,165,192};

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
