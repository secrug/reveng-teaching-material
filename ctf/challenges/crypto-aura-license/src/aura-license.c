/* aura-license : AURA-7 licence validator (ALC-64) — auto-generated */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

static const unsigned char SBOX[] = {230,141,112,22,25,216,194,114,211,82,81,69,16,7,170,65,80,108,74,110,5,11,47,165,253,151,159,111,163,68,183,190,238,23,203,191,26,105,90,137,227,175,234,37,148,189,118,91,242,109,161,29,95,39,96,41,239,18,251,210,153,144,186,60,8,139,61,121,173,188,42,136,147,155,245,51,215,88,17,213,129,124,102,58,34,20,146,237,28,219,152,172,197,46,77,64,193,6,187,226,185,101,244,204,255,248,104,44,4,164,158,250,120,52,171,55,132,122,9,150,181,168,79,92,125,157,78,143,97,214,70,131,2,225,149,76,134,176,10,228,178,12,40,179,241,236,240,83,75,145,1,67,200,243,15,63,195,209,54,140,247,177,233,3,35,249,113,232,231,128,208,142,103,73,24,138,169,174,130,62,133,49,180,135,56,50,86,30,198,160,93,254,166,36,107,85,100,220,212,84,126,202,207,119,59,116,184,38,45,0,115,229,217,33,218,123,252,14,72,206,106,199,201,89,192,99,48,71,43,205,19,246,31,117,154,32,66,57,167,127,27,224,21,222,182,13,221,53,87,196,235,223,156,94,98,162};

static const unsigned char MAGIC[] = {65,85,82,65,45,76,73,67};

static const unsigned char KEY[] = {15,30,45,60,75,90,105,120};

#define ROUNDS 16
static const uint64_t LCG_A = 6364136223846793005ULL, LCG_C = 1442695040888963407ULL;

static uint32_t rotl32(uint32_t v,int n){n&=31; return n? ((v<<n)|(v>>(32-n))) : v;}
static uint32_t sbox_bytes(uint32_t x){
    return (uint32_t)SBOX[x & 0xFF]
         | ((uint32_t)SBOX[(x>>8)&0xFF]<<8)
         | ((uint32_t)SBOX[(x>>16)&0xFF]<<16)
         | ((uint32_t)SBOX[(x>>24)&0xFF]<<24);
}
static uint32_t F(uint32_t R, uint32_t k){
    uint32_t x = R ^ k;
    x = rotl32(x,7);
    x = sbox_bytes(x);
    return x + rotl32(k,11);
}
static void schedule(const unsigned char *m, uint32_t *ks){
    uint64_t st = 0;
    for(int i=7;i>=0;i--) st = (st<<8) | m[i];      /* little-endian load */
    for(int i=0;i<ROUNDS;i++){ st = st*LCG_A + LCG_C; ks[i] = (uint32_t)(st>>32); }
}
static uint32_t ld32(const unsigned char *p){
    return (uint32_t)p[0] | ((uint32_t)p[1]<<8) | ((uint32_t)p[2]<<16) | ((uint32_t)p[3]<<24);
}
static void st32(unsigned char *p, uint32_t v){
    p[0]=(unsigned char)v; p[1]=(unsigned char)(v>>8);
    p[2]=(unsigned char)(v>>16); p[3]=(unsigned char)(v>>24);
}
static void alc_decrypt(unsigned char *b, const uint32_t *ks){
    uint32_t L = ld32(b), R = ld32(b+4), t;
    for(int i=ROUNDS-1;i>=0;i--){ t = R ^ F(L, ks[i]); R = L; L = t; }
    st32(b, L); st32(b+4, R);
}
static int unhex(int c){
    if(c>='0'&&c<='9') return c-'0';
    if(c>='a'&&c<='f') return c-'a'+10;
    if(c>='A'&&c<='F') return c-'A'+10;
    return -1;
}
int main(void){
    char line[128];
    printf("AURA-7 licence: ");
    fflush(stdout);
    if(!fgets(line,sizeof line,stdin)){puts("nope.");return 1;}
    size_t n=strlen(line);
    while(n && (line[n-1]=='\n'||line[n-1]=='\r')) line[--n]=0;
    if(n!=16){puts("Malformed licence.");return 1;}
    unsigned char c[8];
    for(int i=0;i<8;i++){
        int hi=unhex((unsigned char)line[2*i]), lo=unhex((unsigned char)line[2*i+1]);
        if(hi<0||lo<0){puts("Malformed licence.");return 1;}
        c[i]=(unsigned char)((hi<<4)|lo);
    }
    unsigned char keep[8]; memcpy(keep,c,8);
    uint32_t ks[ROUNDS]; schedule(KEY, ks);
    alc_decrypt(c, ks);
    if(memcmp(c, MAGIC, 8)!=0){puts("Licence rejected.");return 1;}
    printf("Licence valid. AURA{");
    for(int i=0;i<8;i++) printf("%02x", keep[i]);
    printf("}\n");
    return 0;
}
