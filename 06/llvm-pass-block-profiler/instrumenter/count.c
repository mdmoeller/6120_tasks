#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int num_fun;
char **names;
int *num_blocks;
int **counts;

int next_fun = 0;

int initialized = 0;

void print_results();
void free_counts();

void init_counter(int n)
{
    if (!initialized) {
        initialized = 1;
        num_fun = n;
        counts = calloc(n, sizeof(int*));
        num_blocks = calloc(n, sizeof(int));
        names = calloc(n, sizeof(char*));

        atexit(free_counts);
        atexit(print_results);
    }
}

void add_function(char *name, int blockcount)
{
    names[next_fun] = strdup(name);
    num_blocks[next_fun] = blockcount;
    counts[next_fun++] = calloc(blockcount, sizeof(int));
}


void free_counts()
{
    for (int i = 0; i < num_fun; i++) {
        free(names[i]);
        free(counts[i]);
    }
    free(names);
    free(counts);
    free(num_blocks);
}


void log_block(int fn_idx, int block_idx)
{
    counts[fn_idx][block_idx]++;
}

void print_results()
{
    printf("Count of dynamic executions, by block index:\n");
    for (int i = 0; i < num_fun; i++) {
        for (int j = 0; j < num_blocks[i]; j++) {
            printf("%s.block[%d]: %d\n", names[i], j, counts[i][j]);
        }
    }
}
