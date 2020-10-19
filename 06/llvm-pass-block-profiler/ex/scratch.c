#include <stdio.h>

int fun(int x, int y) {
    while (x < y) {
        x++;
    }

    return x;
}

int main(int argc, char **argv)
{
    int x = 7;
    int a[5] = {0, 1, 2, 3, 4};

    int b = fun(a[2], a[0]);
    int c = fun(a[0], a[4]);

    printf("%d\n", b + c);

    return 0;
}
