/*
 * seriate_core.c
 *
 * Compiled search engine for exact_seriation.py. Same algorithm as the
 * Python Search class: depth-first branch and bound over assemblages, each
 * new assemblage inserted at every position where it creates no dip.
 *
 * Speed-up relative to the Python version: when assemblage x is inserted,
 * the valid positions of each remaining candidate y are updated
 * incrementally. By heredity, y can go at a position in the new ordering
 * only if it could go at the matching position in the parent ordering, so
 * only triples that contain both x and y need to be checked (O(k) per
 * position instead of O(k^2)).
 *
 * Input file (binary, little-endian):
 *   int32 n
 *   int32 order[n]          search order (assemblage indices)
 *   uint8 bad[n*n*n]        bad[i*n*n + j*n + k] = 1 if j between i and k is a dip
 * Arguments: input_file output_file max_store time_limit_seconds [verbose 0/1]
 * Output file (text):
 *   line 1: best n_orderings n_subsets nodes truncated timed_out seconds
 *   then one line per largest subset: S <n_orderings> <indices...>
 *   then one stored ordering per line (space-separated indices)
 *
 * Limits: n <= 64.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define MAXN 64

static int n;
static uint8_t *bad;
static int best = 0;
static long long n_orderings = 0, nodes = 0;
static long long max_store;
static int *store;              /* max_store * MAXN */
static long long n_store = 0;
static int truncated = 0, timed_out = 0;
static double t_limit, t_start;
static int verbose = 1;

/* subset hash set (uint64 bitmasks) */
static uint64_t *hset;
static long long *hcnt;
static long long hcap = 0, hcount = 0;

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

#define BAD(i, j, k) bad[(size_t)(i) * n * n + (size_t)(j) * n + (k)]

static void hset_clear(void) {
    if (hset) memset(hset, 0, hcap * sizeof(uint64_t));
    if (hcnt) memset(hcnt, 0, hcap * sizeof(long long));
    hcount = 0;
}

static void hset_add_n(uint64_t key, long long inc) {
    /* key never 0 for subsets of size >= 1 */
    if ((hcount + 1) * 2 > hcap) {
        long long oldcap = hcap;
        uint64_t *old = hset;
        long long *oldc = hcnt;
        hcap = oldcap ? oldcap * 2 : 1024;
        hset = calloc(hcap, sizeof(uint64_t));
        hcnt = calloc(hcap, sizeof(long long));
        hcount = 0;
        for (long long i = 0; i < oldcap; i++)
            if (old[i]) hset_add_n(old[i], oldc[i]);
        free(old);
        free(oldc);
    }
    uint64_t h = key * 0x9E3779B97F4A7C15ULL;
    long long i = (long long)(h % (uint64_t)hcap);
    while (hset[i]) {
        if (hset[i] == key) { hcnt[i] += inc; return; }
        i = (i + 1) % hcap;
    }
    hset[i] = key;
    hcnt[i] = inc;
    hcount++;
}

static void hset_add(uint64_t key) { hset_add_n(key, 1); }

static void record(const int *order, int k) {
    uint64_t mask = 0;
    for (int i = 0; i < k; i++) mask |= 1ULL << order[i];
    if (k > best) {
        best = k;
        n_orderings = 0;
        n_store = 0;
        truncated = 0;
        hset_clear();
        if (verbose) fprintf(stderr, "  [%8.1fs] new best size %d\n", now() - t_start, k);
    }
    if (k == best) {
        n_orderings++;
        hset_add(mask);
        if (n_store < max_store) {
            memcpy(store + n_store * MAXN, order, k * sizeof(int));
            n_store++;
        } else {
            truncated = 1;
        }
    }
}

/* Valid insertion positions (bitmask over 0..k) of y into order[0..k-1],
 * full check. Used only for the root candidates (k < 2 there anyway). */
static uint64_t full_positions(const int *order, int k, int y) {
    uint64_t m = 0;
    for (int p = 0; p <= k; p++) {
        int ok = 1;
        for (int a = 0; a < k && ok; a++)
            for (int b = a + 1; b < k && ok; b++) {
                int i = order[a], j = order[b];
                if (b < p) { if (BAD(i, j, y)) ok = 0; }          /* i j y */
                else if (a < p) { if (BAD(i, y, j)) ok = 0; }     /* i y j */
                else { if (BAD(y, i, j)) ok = 0; }                /* y i j */
            }
        if (ok) m |= 1ULL << p;
    }
    return m;
}

/* Given parent ordering O (length k) with valid positions mask_y for y, and
 * new ordering O' = O with x inserted at p (length k+1), return the valid
 * positions of y in O' (mask over 0..k+1). Only triples containing both x
 * and y need checking. */
static uint64_t update_positions(const int *newo, int k1, int p, int x, int y,
                                 uint64_t mask_y) {
    uint64_t m = 0;
    for (int q = 0; q <= k1; q++) {
        int qo = (q <= p) ? q : q - 1;      /* matching position in parent */
        if (!((mask_y >> qo) & 1ULL)) continue;
        int first, second, fpos, spos;      /* positions in the combined order */
        /* In the combined sequence, y sits just before newo[q]. */
        if (q <= p) { first = y; second = x; }
        else        { first = x; second = y; }
        int ok = 1;
        /* walk elements of newo other than x; z position relative to x and y */
        for (int t = 0; t < k1 && ok; t++) {
            if (t == p) continue;
            int z = newo[t];
            /* z is before y iff t < q ; z is before x iff t < p */
            int before_y = (t < q), before_x = (t < p);
            int nb = before_y + before_x;   /* how many of {x,y} z precedes... */
            /* nb counts how many of x,y come AFTER z */
            if (nb == 2)      { if (BAD(z, first, second)) ok = 0; }
            else if (nb == 1) { if (BAD(first, z, second)) ok = 0; }
            else              { if (BAD(first, second, z)) ok = 0; }
        }
        (void)fpos; (void)spos;
        if (ok) m |= 1ULL << q;
    }
    return m;
}

static void dfs(int *order, int k, const int *cand, const uint64_t *cmask, int nc) {
    nodes++;
    if ((nodes & 0xFFFF) == 0) {
        double t = now() - t_start;
        if (t_limit > 0 && t > t_limit) timed_out = 1;
        if (verbose && (nodes & 0x3FFFFF) == 0)
            fprintf(stderr, "  [%8.1fs] nodes=%lld best=%d orderings=%lld\n",
                    t, nodes, best, n_orderings);
    }
    if (timed_out) return;
    record(order, k);

    int newo[MAXN];
    int ncand[MAXN];
    uint64_t nmask[MAXN];

    for (int idx = 0; idx < nc; idx++) {
        if (k + (nc - idx) < best) return;
        int x = cand[idx];
        uint64_t pos = cmask[idx];
        if (k == 1) pos = 2ULL;             /* mirror symmetry: second goes right */
        for (int p = 0; p <= k; p++) {
            if (!((pos >> p) & 1ULL)) continue;
            /* build new ordering */
            for (int t = 0; t < p; t++) newo[t] = order[t];
            newo[p] = x;
            for (int t = p; t < k; t++) newo[t + 1] = order[t];
            int m = 0;
            int remaining = nc - idx - 1;
            for (int r = idx + 1; r < nc; r++) {
                /* early bound: even if all the rest survive */
                if (k + 1 + m + (nc - r) < best) break;
                uint64_t nm = update_positions(newo, k + 1, p, x, cand[r], cmask[r]);
                if (nm) { ncand[m] = cand[r]; nmask[m] = nm; m++; }
            }
            (void)remaining;
            if (k + 1 + m < best) continue;
            dfs(newo, k + 1, ncand, nmask, m);
            if (timed_out) return;
        }
    }
}

int main(int argc, char **argv) {
    if (argc < 5) {
        fprintf(stderr, "usage: %s input output max_store time_limit\n", argv[0]);
        return 2;
    }
    FILE *fi = fopen(argv[1], "rb");
    if (!fi) { perror("input"); return 2; }
    int32_t nn;
    if (fread(&nn, 4, 1, fi) != 1) return 2;
    n = nn;
    if (n < 1 || n > MAXN) { fprintf(stderr, "n must be 1..64\n"); return 2; }
    int32_t ord[MAXN];
    if (fread(ord, 4, n, fi) != (size_t)n) return 2;
    bad = malloc((size_t)n * n * n);
    if (fread(bad, 1, (size_t)n * n * n, fi) != (size_t)n * n * n) return 2;
    fclose(fi);
    max_store = atoll(argv[3]);
    t_limit = atof(argv[4]);
    if (argc > 5) verbose = atoi(argv[5]);
    store = malloc((size_t)(max_store > 0 ? max_store : 1) * MAXN * sizeof(int));

    int cand[MAXN];
    uint64_t cmask[MAXN];
    int empty[1];
    for (int i = 0; i < n; i++) { cand[i] = ord[i]; cmask[i] = full_positions(empty, 0, ord[i]); }

    t_start = now();
    int order[MAXN];
    dfs(order, 0, cand, cmask, n);
    double elapsed = now() - t_start;

    FILE *fo = fopen(argv[2], "w");
    fprintf(fo, "%d %lld %lld %lld %d %d %.3f\n", best, n_orderings, hcount, nodes,
            truncated, timed_out, elapsed);
    /* subsets: "S count i1 i2 ..." */
    for (long long i = 0; i < hcap; i++) {
        if (!hset[i]) continue;
        fprintf(fo, "S %lld", hcnt[i]);
        for (int b = 0; b < n; b++)
            if ((hset[i] >> b) & 1ULL) fprintf(fo, " %d", b);
        fprintf(fo, "\n");
    }
    for (long long s = 0; s < n_store; s++) {
        for (int t = 0; t < best; t++)
            fprintf(fo, t ? " %d" : "%d", store[s * MAXN + t]);
        fprintf(fo, "\n");
    }
    fclose(fo);
    return 0;
}
