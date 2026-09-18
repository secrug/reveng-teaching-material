/* aurad-parser : AURA-7 command front-end (pwn/aurad-parser)
 *
 * VULN (intended): the length field is a SIGNED 32-bit int, but the bounds
 * check `if (len > 64)` only rejects large POSITIVE lengths. A negative length
 * passes the check and is then passed to fread() as a size_t, becoming enormous
 * -> classic signedness bug -> stack buffer overflow -> ret2win (unlock()).
 *
 * Build (see Dockerfile / healthcheck.sh):
 *     gcc -O0 -fno-stack-protector -no-pie -o aurad-parser aurad-parser.c
 *   - no stack canary  -> return address is overwritable
 *   - no PIE           -> unlock() lives at a fixed address (ret2win)
 *
 * The service reads from stdin / writes stdout; the jail (see HOSTING.md) wires
 * that to the socket. flag.txt sits in the CWD, readable only after you divert
 * control into unlock().
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

/* ret2win target — never called on the normal path */
void unlock(void) {
    char flag[128];
    FILE *f = fopen("flag.txt", "r");
    if (!f) { puts("[local build: no flag.txt]"); fflush(stdout); return; }
    if (fgets(flag, sizeof flag, f)) {
        printf("Maintenance override accepted.\n%s\n", flag);
        fflush(stdout);
    }
    fclose(f);
}

/* read a big-endian 32-bit length — deliberately SIGNED */
static int read_len_be32(void) {
    unsigned char b[4];
    if (fread(b, 1, 4, stdin) != 4) exit(0);
    return (int)(((unsigned)b[0] << 24) | ((unsigned)b[1] << 16)
               | ((unsigned)b[2] << 8)  |  (unsigned)b[3]);
}

void handle(void) {
    char buf[64];
    printf("AURA-7 aurad ready.\ncommand length: ");
    fflush(stdout);

    int len = read_len_be32();
    if (len > 64) {                 /* signed compare: negative lengths slip past */
        puts("command too long");
        return;
    }
    printf("reading %d bytes...\n", len);
    fflush(stdout);

    fread(buf, 1, (size_t)len, stdin);   /* (size_t)(-1) == huge -> overflow */
    printf("command received: %.*s\n", (len > 0 ? len : 0), buf);
    fflush(stdout);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);
    handle();
    puts("bye");
    return 0;
}
