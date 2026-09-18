/* one-way-gate : AURA-7 hardened unlock (auto-generated) */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

static const uint32_t TABLE[] = {0x32775a35u,0x29fed997u,0x8a551fbdu,0xb10184d0u,0x91fe9bf2u,0x10e3a7bdu,0x42852e78u,0xf25b74c7u,0xaa936662u,0x6d1572aau,0x7892f00fu,0xab920360u,0x44f81b15u,0x1c6ecd3au,0x65938384u,0xc890a016u,0xdb60f649u,0x90f4f026u};

static const uint32_t IV = 305441741u;
static const uint32_t ACC_TARGET = 5523u;
#define NCHUNK (sizeof TABLE / sizeof TABLE[0])

static uint32_t mix(uint16_t c, uint32_t h, uint32_t i){
    uint32_t x = (uint32_t)(c ^ (uint16_t)(h & 0xFFFF));
    uint32_t y = x * 2246822507u;
    y ^= y >> 13;
    y = y * 3266489909u;
    y ^= y >> 16;
    y = y + h + i * 2135587861u;
    return y;
}
int main(void){
    unsigned char in[256];
    if(!fgets((char*)in,sizeof in,stdin)){puts("nope.");return 1;}
    size_t n=strlen((char*)in);
    while(n && (in[n-1]=='\n'||in[n-1]=='\r')) in[--n]=0;
    if(n != NCHUNK*2){puts("nope.");return 1;}

    /* gate 1: chained one-way avalanche, 2 bytes at a time */
    uint32_t h = IV;
    for(size_t i=0;i<NCHUNK;i++){
        uint16_t c = (uint16_t)(in[2*i] | ((uint16_t)in[2*i+1] << 8));
        uint32_t v = mix(c, h, (uint32_t)i);
        if(v != TABLE[i]){puts("nope.");return 1;}
        h = v;
    }
    /* gate 2: path-explosion checksum — one data-dependent branch per byte */
    uint32_t acc = 0;
    for(size_t i=0;i<n;i++){
        unsigned char b = in[i];
        if(b & 1) acc = acc + (uint32_t)b * 3u;
        else      acc = acc ^ ((uint32_t)b * 5u);
    }
    if(acc != ACC_TARGET){puts("nope.");return 1;}

    puts("Gate open. That input is the flag.");
    return 0;
}
