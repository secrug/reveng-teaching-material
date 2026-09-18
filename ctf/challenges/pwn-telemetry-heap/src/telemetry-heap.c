/* telemetry-heap : AURA-7 telemetry channel manager (pwn/telemetry-heap)
 *
 * VULN (intended): USE-AFTER-FREE into a function pointer.
 *   - `del` frees a channel but does NOT clear chans[i] (dangling pointer).
 *   - `note` performs malloc(sizeof(chan)) and reads 32 attacker bytes into it.
 *     Same size as a channel, so tcache hands back the just-freed channel chunk,
 *     and the first 8 bytes the attacker writes land exactly on `fmt`.
 *   - `show` calls chans[i]->fmt(chans[i]) on the dangling index -> control flow.
 *
 * Exploit path: new(0); del(0); note(p64(&win)); show(0)  ->  win() -> flag.
 *
 * Build (see Dockerfile / healthcheck.sh):
 *     gcc -O0 -fno-stack-protector -no-pie -o telemetry-heap telemetry-heap.c
 *   non-PIE so win() is at a fixed address. glibc tcache (>=2.26) gives the
 *   deterministic same-size free->malloc reuse the exploit relies on.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

struct chan {
    void (*fmt)(struct chan *);   /* offset 0 : the hijack target */
    char data[24];
};

static struct chan *chans[16];

/* win — never reached on the normal path */
void win(struct chan *c) {
    (void)c;
    system("/bin/cat flag.txt");
}

static void default_fmt(struct chan *c) {
    printf("chan: %.24s\n", c->data);
}

static long readlong(void) {
    char b[32];
    if (!fgets(b, sizeof b, stdin)) exit(0);
    return strtol(b, NULL, 0);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);
    for (;;) {
        printf("1) new  2) del  3) note  4) show  5) quit\n> ");
        long op = readlong();
        if (op == 1) {
            printf("index: ");  long i = readlong();
            if (i < 0 || i >= 16) continue;
            chans[i] = malloc(sizeof(struct chan));
            if (!chans[i]) exit(1);
            chans[i]->fmt = default_fmt;
            memset(chans[i]->data, 0, sizeof chans[i]->data);
            puts("channel created");
        } else if (op == 2) {
            printf("index: ");  long i = readlong();
            if (i < 0 || i >= 16) continue;
            free(chans[i]);            /* BUG: chans[i] left dangling */
            puts("channel deleted");
        } else if (op == 3) {
            char *n = malloc(sizeof(struct chan));   /* reuses a freed chan chunk */
            if (!n) exit(1);
            printf("note bytes (32): ");
            read(0, n, sizeof(struct chan));         /* first 8 bytes overwrite fmt */
            puts("note stored");
        } else if (op == 4) {
            printf("index: ");  long i = readlong();
            if (i < 0 || i >= 16 || !chans[i]) continue;
            chans[i]->fmt(chans[i]);                 /* calls hijacked pointer */
        } else {
            break;
        }
    }
    return 0;
}
