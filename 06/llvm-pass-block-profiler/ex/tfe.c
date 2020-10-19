#include <curses.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define SIZE 4
#define DEPTH 5

#define MIN(x, y) (x < y)? (x) : (y)
#define MAX(x, y) (x > y)? (x) : (y)

#define FOREACH(r, c) for (r = 0; r < SIZE; r++) for (c = 0; c < SIZE; c++)

typedef int** board;
typedef enum emove { UP, LEFT, RIGHT, DOWN } move_t;

/**
 * Location/value triple generated between player moves.
 */
typedef struct sgen {
    int val, row, col;
} gen;

void sdisplay(board, int, int);
gen *cgen(board b);
gen *cgen_r(board b, int d, double *s);

move_t cplay(board b);
move_t cplay_r(board b, int d, int*);

move_t eplay_r(board b, int d, double *score, int*);

void place(board b, gen* g);
int gameover(board b);
int shift(board b, move_t m, double *score);

void help_and_quit(int);

/**
 * Return a judgment of how ``good'' the board is, for leaves of expectimax
 */
double eval(board b)
{
    int r, c, count = 0, clear = 0;
    int collapse = 0;
    double tot = 0, score = 0;
    for (r = 0; r < SIZE - 1; r++) {
        for (c = 0; c < SIZE - 1; c++) {
            double row = b[r][c] - b[r+1][c];
            double col = b[r][c] - b[r][c+1];
            if (r == 0) {
                row *= 2;
                col *= 2;
            }

            if (row == 0 || col == 0)
                collapse = 1;

            score += row + col;
        }
    }

    FOREACH(r, c) {
        if (b[r][c]) {
            tot += b[r][c];
            count++;
        } else {
            clear++;
        }
    }

    score += tot / count;

    /* Near-death penalty */
    if (clear < 4) {
        score /= 5 - clear;
    }

    /* Avoid death at all cost */
    if (clear == 0 && collapse == 0)
        return 0;

    return score;
}

/**
 * Return a copy of the board.
 */
board clone(board b)
{
    int r, c;
    board copy = (board) calloc(SIZE, sizeof(int*));
    for (r = 0; r < SIZE; r++) {
        copy[r] = (int*) calloc(SIZE, sizeof(int));
        for (c = 0; c < SIZE; c++) {
            copy[r][c] = b[r][c];
        }
    }
    return copy;
}

/**
 * Free a board.
 */
void destruct(board b) {
    int r;
    for (r = 0; r < SIZE; r++) {
        free(b[r]);
    }
    free(b);
}

/**
 * Return 1 if the boards are different, 0 otherwise.
 */
int different(board a, board b) 
{
    int r, c, diff = 0;

    FOREACH(r, c) {
        if (a[r][c] != b[r][c])
            diff = 1;
    }

    return diff;
}

/**
 * Have the user select a location and value triple.
 * Use hjkl to navigate to the square, and hit enter to return 2 and space to
 * return 4.
 */
gen *hgen(board b)
{
    gen *g = (gen*) calloc(1, sizeof(gen));

    char in;
    g->row = 0;
    g->col = 0;
    g->val = 2;


    while (1) {
        clear();
        sdisplay(b, g->row, g->col);
        in = getch();
        switch (in) {
            case  65:
            case 'k': g->row--; break;
            case  66:
            case 'j': g->row++; break;
            case  68:
            case 'h': g->col--; break;
            case  67:
            case 'l': g->col++; break;
            case ' ': g->val = 4;  //fall through and return
            case  10: if (!b[g->row][g->col])
                          return g;
        }
        g->row = MIN(g->row, SIZE - 1);
        g->row = MAX(g->row, 0);
        g->col = MIN(g->col, SIZE - 1);
        g->col = MAX(g->col, 0);
    }
}

/**
 * Have the computer generate a location/value triple designed to put the player
 * in the worst position possible.
 * Alg: Minimax, corecursively with cplay().
 */
gen *cgen(board b)
{
    double score = 0;
    return cgen_r(b, DEPTH, &score);
}

/**
 * Recursive helper to cgen();
 */
gen *cgen_r(board b, int d, double *score)
{
    gen g, *best = (gen*) calloc(1, sizeof(gen));

    int r, c, min = INT_MAX, nullscore;
    double s;
    FOREACH(r, c) {
        s = nullscore = *score;
        

        if (!b[r][c]) {
            g.row = r;
            g.col = c;
            g.val = 2;
            board copy = clone(b);

            place(copy, &g);

            if (gameover(copy)) {
                *best = g;
                destruct(copy);
                return best;
            }

            if (d > 1) {
                shift(copy, cplay_r(copy, d - 1, &nullscore), &s);
            }

            if (s < min) {
                min = s;
                *best = g;
            }

            //Technically necessary for true minimax... but we can disregard:
            /* 
            s = nullscore = *score;
            g.val = 4;
            copy[r][c] = 4;

            if (gameover(copy)) {
                *best = g;
                destruct(copy);
                return best;
            }

            if (d > 1) {
                shift(copy, cplay_r(copy, d - 1, &s), &s);
            }

            if (s < min) {
                min = s;
                *best = g;
            }
            */

            destruct(copy);
        }
    }

    *score = s;
    return best;
}

/**
 * Generate a random board location. 
 */
gen *rgen(board b)
{
    gen *g = (gen*) calloc(1, sizeof(gen));
    g->val = 2;
    if (rand() % 10 == 0)
        g->val = 4;

    do {
        g->row = rand() % SIZE;
        g->col = rand() % SIZE;
    } while (b[g->row][g->col]);

    return g;
}

/**
 * Get a move from the computer. 
 * Alg: Minimax, corecursively with cgen().
 * */
move_t cplay(board b)
{
    int score = 0;
    return cplay_r(b, DEPTH, &score);
}

/**
 * Recursive helper to cplay().
 */
move_t cplay_r(board b, int d, int *score)
{
    move_t m, best = UP;
    int max = -1;
    double s;
    for (m = 0; m < 4; m++) {
        s = *score;
        board c = clone(b);

        shift(c, m, &s);

        if (!different(b, c)) {
            destruct(c);
            continue;
        }

        if (d > 1) {
            gen *g = cgen_r(b, d-1, &s);
            place(c, g);
            free(g);
        }

        if (s > max) {
            max = s;
            best = m;
        }
        destruct(c);
    }

    *score = s;
    return best;
}

/**
 * Get a move from the computer using Expectimax
 */
move_t eplay(board b)
{
    double score = 0;
    //int d = DEPTH, dd = DEPTH, leaves = 0, newleaves = 0; // DD for "depth decided"
    int d, leaves = 0;
    int r, c, clear = 0;

    FOREACH(r,c)
        if (!b[r][c])
            clear++;

    switch (clear) {
        case 0: d = 7; break;
        case 1:
        case 2:
        case 3:
        case 4:
        case 5: 
        case 6:
        case 7: d = 5;  break;
        case 8:
        default: d = 3;
    }

    move_t m = eplay_r(b, d, &score, &leaves);

    return m;
}

/**
 * Recursive helper to eplay().
 * b: the board to find the best move on
 * d: depth to search
 * score: output parameter; score of the best move.
 */
move_t eplay_r(board b, int d, double *score, int *leafcount)
{
    move_t m, best = -1;
    double max = 0;
    *score = 0;
    double junk;

    for (m = 0; m < 4; m++) {

        if (m == DOWN && max > 0)
            break;

        board copy = clone(b);

        if (!shift(copy, m, &junk)) {
            destruct(copy);
            continue;
        }

        /* At least this move is legal. Pick this for now. We still need to
         * compute its score to compare later. */
        if (best == -1)
            best = m;

        double s = 0;

        if (d <= 1) {
            s = eval(copy);
            (*leafcount)++;

        } else {
            int count = 0;
            int r, c;

            FOREACH(r, c) {
                gen g;

                if (!copy[r][c]) {
                    g.row = r;
                    g.col = c;
                    g.val = 2;
                    board copy2 = clone(copy);

                    double childscore;

                    place(copy2, &g);

                    if (!gameover(copy2)) {
                        eplay_r(copy2, d - 2, &childscore, leafcount);
                        count++;
                        s += childscore * 0.9;
                    }

                    g.val = 4;
                    place(copy2, &g);

                    if (!gameover(copy2)) {
                        eplay_r(copy2, d - 2, &childscore, leafcount);
                        count++;
                        s += childscore * 0.1;
                    }

                    destruct(copy2);
                }
            }

            if (count == 0)
                s = 0;
            else
                s /= count;
        } 

        if (s > max) {
            max = s;
            best = m;
        }
        destruct(copy);
    }

    *score = max;
    return best;
}

/**
 * Prefer the moves in this order:
 * UP LEFT RIGHT DOWN
 */
move_t splay(board b)
{
    double score;
    board c = clone(b);
    if (shift(c, UP, &score)) {
        free(c);
        return UP;
    }

    c = clone(b);
    if (shift(c, LEFT, &score)) {
        free(c);
        return LEFT;
    }

    c = clone(b);
    if (shift(c, RIGHT, &score)) {
        free(c);
        return RIGHT;
    }

    return DOWN;
}

move_t rotmove = UP;

/**
 * Play up down left right in that order. 
 */
move_t rotplay(board b)
{
    rotmove += 1;
    rotmove %= 4;

    return rotmove;
}



/**
 * Get a move from a human player for the given board and return it. 
 */
move_t hplay(board b)
{
    char in;

    while (1) {
        in = getch();
        switch (in) {
            case 65:
            case 'k': return UP;
            case 66:
            case 'j': return DOWN;
            case 68:
            case 'h': return LEFT;
            case 67:
            case 'l': return RIGHT;
        }
    }
}

/**
 * Return a random move.
 */
move_t rplay(board b)
{
    return rand() % 4;
}

/**
 * This macro, together with the appropriate inputs provided by the function
 * below, performs the ``2048 shift''.
 * The idea here to abstract away the small differences between the four
 * directions to avoid the repetition of a very similar code block.
 **/
#define SHIFT(R, C, RC, CC, MAJ, MIN) \
    for (MAJ = 0; MAJ < SIZE; MAJ++) { \
        int count = -1, last = -1; \
        for (MIN = 0; MIN < SIZE; MIN++) { \
            if (b[R][C]) { \
                if (last == b[R][C]) { \
                    b[RC][CC] *= 2; \
                    *score += b[RC][CC]; \
                    b[R][C] = 0; \
                    last = -1; \
                    moved = 1; \
                } else { \
                    last = b[R][C]; \
                    b[R][C] = 0; \
                    count++; \
                    b[RC][CC] = last; \
                    moved = (moved || RC != R || CC != C); \
                } \
            } \
        } \
    }


/**
 * Perform a shift on board b. Return 1 if any squares were actually moved,
 * 0 otherwise. Update the score accordingly.
 **/
int shift(board b, move_t m, double *score)
{
    int r, c, moved = 0;
    switch (m) {
        case UP:
            SHIFT(r, c, count, c, c, r);
            break;

        case DOWN:
            SHIFT(SIZE-r-1, c, SIZE-count-1, c, c, r);
            break;

        case LEFT:
            SHIFT(r, c, r, count, r, c);
            break;

        case RIGHT:
            SHIFT(r, SIZE-c-1, r, SIZE-count-1, r, c);
            break;
    }
    return moved;
}

/**
 * Place the generated value on the board. 
 */
void place(board b, gen* g)
{
    b[g->row][g->col] = g->val;
}

/** 
 * Returns 1 if the board is full and no moves exist, 0 otherwise. 
 */
int gameover(board b)
{
    // First of all, check if there are gaps
    // Start at bottom right since we know the expectimax player prefers to go
    // UP and LEFT.
    int r, c;
    for (r = SIZE-1; r >= 0; r--)
        for (c = SIZE-1; c >= 0; c--)
            if (!b[r][c])
                return 0;

    // Now check if any moves work.
    // (This would do it by itself, but doing the above first is faster on
    // average)
    move_t m;
    double nullscore;
    for (m = 0; m < 4; m++) {
        board c = clone(b);
        if (shift(c, m, &nullscore)) {
            destruct(c);
            return 0;
        }
        destruct(c);
    }
    return 1;
}


#define DISPLAY(print) \
    int r, c; \
    print("\n\n"); \
    for (r = 0; r < SIZE; r++) { \
        print("   "); \
        for (c = 0; c < SIZE; c++) { \
            if (b[r][c]) \
                print("[%4d]", b[r][c]); \
            else \
                print("[    ]"); \
        } \
        print("\n"); \
    } \

/**
 * Print a board to ncurses screen. 
 */
void display(board b, int score)
{
    DISPLAY(printw)
    printw("%d\n", score);
}

/**
 * Print the board to stdout. 
 */
void pdisplay(board b)
{
    DISPLAY(printf)
}

/**
 * Print the board with (r, c) highlighted in red.
 */
void sdisplay(board b, int row, int col)
{
    int r, c;
    printw("\n\n");
    for (r = 0; r < SIZE; r++) {
        printw("   ");
        for (c = 0; c < SIZE; c++) {
            if (r == row && c == col)
                attron(COLOR_PAIR(1));

            if (b[r][c])
                printw("[%4d]", b[r][c]);
            else
                printw("[    ]");

            attroff(COLOR_PAIR(1));
        }
        printw("\n");
    }
}

void help_and_quit(int status)
{
    printf("\
usage: tfe [OPTIONS] [-c <number of games>] \n\
\n\
To play, use arrow keys or hjkl to enter shifts. When playing as the tile\n\
generator, move to the desired square using arrow keys, then hit enter to\n\
generator a 2, and hit space to generate a 4.\n\
\n\
Options:\n\
\n\
    General:\n\
    -h      display this message and exit.\n\
    -p      print the final board to stdout.\n\
    -w      step through a game played by computer (note: if one of the ncurses\n\
            players is selected, this option has no effect)\n\
    -c <n>  play n games (default is 1)\n\
\n\
    Setting the player:\n\
    -r   random player\n\
    -n   ncurses interface / human (default)\n\
    -m   minimax player\n\
    -e   expectimax player\n\
    -s   simple player\n\
    -v   rotation player\n\
\n\
    Setting the new tile generator:\n\
    -R   random generation (default)\n\
    -N   ncurses interface / human\n\
    -M   minimax generator\n\
");

    exit(status);
}

int main(int argc, char *argv[])
{
    int c, ncurses, pn = 1, gn = 0, pd = 0, watch = 0;
    int expect_count = 0, count_to = 1;

    /* "Abstract" player and tile generator... assign based on options */
    gen *(*generator)(board) = rgen;
    move_t (*player)(board) = hplay;

    while (--argc > 0 && (*++argv)[0] == '-') { // Option parser from K&R p 117!
        while ((c = *++argv[0])) {
            switch (c) {
                case 'h':
                    help_and_quit(0);
                    break;

                case 'w':
                    watch = 1;
                    break;

                case 'r':
                    player = rplay;
                    pn = 0;
                    break;

                case 'n':
                    player = hplay;
                    pn = 1;
                    break;

                case 'm':
                    player = cplay;
                    pn = 0;
                    break;

                case 'e':
                    player = eplay;
                    pn = 0;
                    break;

                case 'c':
                    expect_count = 1;
                    break;

                case 's':
                    player = splay;
                    pn = 0;
                    break;

                case 'v':
                    player = rotplay;
                    pn = 0;
                    break;

                case 'R':
                    generator = rgen;
                    gn = 0;
                    break;

                case 'N':
                    generator = hgen;
                    gn = 1;
                    break;

                case 'M':
                    generator = cgen;
                    gn = 0;
                    break;

                case 'p':
                    pd = 1;
                    break;

                default:
                    fprintf(stderr, "Invalid option: %x\n\n", c);
                    help_and_quit(1);
            }
        }
    }

    if (expect_count && !argc) {
        help_and_quit(1);
    } else if (expect_count) {
        count_to = atoi(*argv);
    }
    
    ncurses = pn || gn || watch;

    struct timespec t;
    clock_gettime(CLOCK_REALTIME, &t);
    srand(t.tv_nsec);

    if (ncurses) {
        initscr();
        start_color();
        init_pair(1, COLOR_WHITE, COLOR_RED);
        cbreak();
        noecho();
    }

    //printf("DEPTH: %d\n", DEPTH);
    int count;
    for (count = 0; count < count_to; count++) {
        int r;
        double score = 0;

        board b = (board) calloc(SIZE, sizeof(int*));
        for (r = 0; r < SIZE; r++) {
            b[r] = (int*) calloc(SIZE, sizeof(int));
        }

        gen *g = (*generator)(b);
        place(b, g);
        free(g);

        g = (*generator)(b);
        place(b, g);
        free(g);

        while (!gameover(b)) {

            if (ncurses) {
                clear();
                display(b, score);
                if (watch && !pn && !gn)
                    getch();
            }

            move_t m = (*player)(b);
            if (shift(b, m, &score)) {
                g = (*generator)(b);
                place(b, g);
                free(g);
            }
        }


        if (ncurses) {
            endwin();
        }

        if (pd) {
            pdisplay(b);
        }

        printf("%f\n", score);
    }

    return 0;
}
