#include <stddef.h>

void copy_bytes(unsigned char *buffer, const unsigned char *input, size_t count) {
    for (size_t i = 0; i < count; ++i) {
        buffer[i] = input[i];
    }
}

unsigned mask_bits(unsigned value, unsigned shift) {
    return (value >> shift) & 255u;
}
