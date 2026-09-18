/* mirror : AURA-7 keystream verifier (auto-generated) */
#include <stdio.h>
#include <string.h>
#include <stdint.h>
static const unsigned char CT[] = {11,48,85,122,159,196,233,14,51,88,125,162,199,236,17,54,91,128,165,202,239,20,57,94,131,168,205,242,23,60,97,134,171,208,245,26};

static const unsigned char expected[] = {206,87,61,79,174,11,142,34,164,35,56,51,114,141,131,52,27,141,238,113,153,97,208,13,150,120,50,68,227,136,193,121,78,214,206,238};

static unsigned char rol8(unsigned char v,int n){n%=8;return (unsigned char)((v<<n)|(v>>(8-n)));}
int main(void){
    unsigned char in[256];
    if(!fgets((char*)in,sizeof in,stdin)){puts("nope.");return 1;}
    size_t n=strlen((char*)in);
    while(n && (in[n-1]=='\n'||in[n-1]=='\r')) in[--n]=0;
    if(n!=sizeof expected){puts("nope.");return 1;}
    uint32_t s=99u;
    for(size_t i=0;i<n;i++){
        s=(uint32_t)(s*1103515245u + 12345u);
        unsigned char kb=(unsigned char)((s>>8)&0xFF);
        unsigned char ks=(unsigned char)(CT[i]^kb);
        unsigned char t=(unsigned char)(rol8(in[i], (int)(i%7)) ^ ks);
        if(t!=expected[i]){puts("nope.");return 1;}
    }
    puts("Reflection matched. That input is the flag.");
    return 0;
}
