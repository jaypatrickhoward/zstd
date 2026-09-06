/* Deterministic corpus generator: identical bytes on every platform, so
 * dictionaries can be compared across runners. Writes 4 KB sample files plus
 * one filelist per corpus size (LF-only: zstd's --filelist splits on '\n' and
 * does not strip '\r'). C90, no dependencies. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 32-bit LCG: pure C90, no extensions, identical output on every target
 * including 32-bit and big-endian ones. */
static unsigned g_s = 2463534242u;
static unsigned nxt(void)
{
    g_s = (g_s * 1103515245u + 12345u) & 0x7FFFFFFFu;
    return g_s;
}

#define CHUNK 4096
#define MAXFILES 8192

int main(void)
{
    static const char *tok[] = { "{\"id\":", "\"name\":", "\"ts\":", "\"val\":",
                                 "alpha", "bravo", "charlie", "delta",
                                 ",", "}", "\n", "\"host\":", "\"lvl\":" };
    static char buf[CHUNK];
    static const int sizes[] = { 256, 1024, 2048, 3072, 4096, 8192 };
    static const int mb[]    = {   1,    4,    8,   12,   16,   32 };
    char name[64];
    int i, s;
    FILE *f;

    for (i = 0; i < MAXFILES; ++i) {
        size_t n = 0;
        while (n < CHUNK) {
            const char *t = tok[nxt() % 13];
            size_t L = strlen(t);
            if (n + L > CHUNK) L = CHUNK - n;
            memcpy(buf + n, t, L);
            n += L;
        }
        sprintf(name, "corpus/f%05d.bin", i);
        f = fopen(name, "wb");
        if (!f) { fprintf(stderr, "gencorpus: cannot write %s\n", name); return 1; }
        if (fwrite(buf, 1, CHUNK, f) != CHUNK) { fprintf(stderr, "gencorpus: short write\n"); return 1; }
        fclose(f);
    }
    for (s = 0; s < 6; ++s) {
        sprintf(name, "list_%dmb.txt", mb[s]);
        f = fopen(name, "wb");            /* binary: LF only, never CRLF */
        if (!f) { fprintf(stderr, "gencorpus: cannot write %s\n", name); return 1; }
        for (i = 0; i < sizes[s]; ++i) fprintf(f, "corpus/f%05d.bin\n", i);
        fclose(f);
        printf("gencorpus: %s -> %d files (%d MB)\n", name, sizes[s], mb[s]);
    }
    return 0;
}
