/* padded-struct : AURA-7 wire-format verifier (auto-generated) */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

/* The compiler pads this: sizeof(struct step)==8, k at offset 4, NOT 1. */
struct step { uint8_t op; uint32_t k; };
static const struct step STEPS[] = {
    { 0, 0x0000005A },
    { 3, 0x00000003 },
    { 1, 0x000000B7 },
    { 2, 0x00000029 }
};
#define NS (sizeof STEPS / sizeof STEPS[0])
static const unsigned char expected[] = {27,170,9,24,33,131,235,59,62,75,37,62,5,75,42,54,45,67,28,73,63,250,43,63,63,250,36,70,62,43,35,54,41,99,32,71,41,235};


static unsigned char rol8(unsigned char v,int n){n&=7;return (unsigned char)((v<<n)|(v>>(8-n)));}
static unsigned char step_apply(unsigned char c, struct step s){
    unsigned char k=(unsigned char)(s.k & 0xFF);
    switch(s.op){case 0:return c^k;case 1:return (unsigned char)(c+k);
                 case 2:return (unsigned char)(c-k);case 3:return rol8(c,k);}
    return c;
}
int main(void){
    unsigned char in[256];
    if(!fgets((char*)in,sizeof in,stdin)){puts("nope.");return 1;}
    size_t n=strlen((char*)in);
    while(n && (in[n-1]=='\n'||in[n-1]=='\r')) in[--n]=0;
    if(n!=sizeof expected){puts("nope.");return 1;}
    for(size_t i=0;i<n;i++)
        if(step_apply(in[i], STEPS[i%NS]) != expected[i]){puts("nope.");return 1;}
    puts("Wire format valid. That input is the flag.");
    return 0;
}
