/* warmup-decoder : AURA-7 signal primer (auto-generated) */
#include <stdio.h>
#include <string.h>
static const char *KEY = "AURA-SIGNAL-KEY";      /* left visible on purpose */
static const unsigned char expected[] = {75,255,192,75,246,232,232,212,37,234,207,215,232,6,114,187,62,89,90,110,24,58,108,180,10,215,215,112,62,34,98,175,89,226,215,240,10,12,213,170};

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
