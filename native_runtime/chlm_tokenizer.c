#include "chlm_tokenizer.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHTK_HEADER_BYTES 40u
#define CHTK_VERSION 1u
#define CHTK_ENDIAN 0x1234u
#define CHTK_SPECIAL_COUNT 13u

#pragma pack(push, 1)
typedef struct {
    char magic[4];
    uint16_t version, endian;
    uint32_t file_bytes, vocab, merge_count, merge_offset, offsets_offset;
    uint32_t pieces_offset, payload_crc32, reserved;
} ChtkHeader;
typedef struct { uint16_t left, right, token; } ChtkMerge;
#pragma pack(pop)

struct chlm_tokenizer {
    const uint8_t *image;
    size_t image_bytes;
    ChtkHeader header;
    const ChtkMerge *merges;
    const uint32_t *offsets;
    const uint8_t *pieces;
    char error[128];
};

static const char *const SPECIALS[CHTK_SPECIAL_COUNT] = {
    "<pad>", "<bos>", "<eos>", "<fact>", "<ask>", "<answer>", "<unknown>",
    "<copy_name>", "<copy_family>", "<copy_purpose>", "<copy_symbol>",
    "<copy_behavior>", "<copy_constraint>"
};

static uint32_t crc32_bytes(const uint8_t *data, size_t length) {
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t index = 0; index < length; ++index) {
        crc ^= data[index];
        for (int bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ (0xEDB88320u & (uint32_t)-(int32_t)(crc & 1u));
    }
    return ~crc;
}

static int fail(chlm_tokenizer *tokenizer, const char *message) {
    if (tokenizer) snprintf(tokenizer->error, sizeof(tokenizer->error), "%s", message);
    return -1;
}

int chlm_tokenizer_create(chlm_tokenizer **output, const void *image, size_t image_bytes) {
    if (!output || !image || image_bytes < CHTK_HEADER_BYTES) return -1;
    *output = NULL;
    chlm_tokenizer *tokenizer = (chlm_tokenizer *)calloc(1, sizeof(*tokenizer));
    if (!tokenizer) return -1;
    tokenizer->image = (const uint8_t *)image;
    memcpy(&tokenizer->header, image, sizeof(tokenizer->header));
    const ChtkHeader *header = &tokenizer->header;
    if (memcmp(header->magic, "CHTK", 4) || header->version != CHTK_VERSION ||
        header->endian != CHTK_ENDIAN || header->reserved != 0 ||
        header->file_bytes < CHTK_HEADER_BYTES || header->file_bytes > image_bytes ||
        header->vocab < CHTK_SPECIAL_COUNT + 256u || header->vocab > 65535u ||
        header->merge_count != header->vocab - CHTK_SPECIAL_COUNT - 256u ||
        header->merge_offset != CHTK_HEADER_BYTES) {
        fail(tokenizer, "invalid CHTK header"); goto error;
    }
    tokenizer->image_bytes = header->file_bytes;
    size_t merge_end = (size_t)header->merge_offset + (size_t)header->merge_count * sizeof(ChtkMerge);
    size_t offsets_end = (size_t)header->offsets_offset + ((size_t)header->vocab + 1u) * sizeof(uint32_t);
    if (merge_end > header->offsets_offset || header->offsets_offset > tokenizer->image_bytes ||
        offsets_end > header->pieces_offset || header->pieces_offset > tokenizer->image_bytes ||
        (header->offsets_offset & 3u) != 0u ||
        crc32_bytes(tokenizer->image + header->merge_offset,
                    tokenizer->image_bytes - header->merge_offset) != header->payload_crc32) {
        fail(tokenizer, "invalid CHTK layout or CRC"); goto error;
    }
    tokenizer->merges = (const ChtkMerge *)(tokenizer->image + header->merge_offset);
    tokenizer->offsets = (const uint32_t *)(tokenizer->image + header->offsets_offset);
    tokenizer->pieces = tokenizer->image + header->pieces_offset;
    uint32_t pieces_bytes = (uint32_t)(tokenizer->image_bytes - header->pieces_offset);
    if (tokenizer->offsets[0] != 0 || tokenizer->offsets[header->vocab] != pieces_bytes)
        { fail(tokenizer, "invalid CHTK piece bounds"); goto error; }
    for (uint32_t token = 0; token < header->vocab; ++token) {
        if (tokenizer->offsets[token] > tokenizer->offsets[token + 1u] ||
            tokenizer->offsets[token + 1u] > pieces_bytes)
            { fail(tokenizer, "invalid CHTK piece offset"); goto error; }
    }
    for (uint32_t index = 0; index < header->merge_count; ++index) {
        const ChtkMerge *merge = &tokenizer->merges[index];
        uint32_t expected = CHTK_SPECIAL_COUNT + 256u + index;
        if (merge->token != expected || merge->left >= expected || merge->right >= expected)
            { fail(tokenizer, "invalid CHTK merge order"); goto error; }
    }
    *output = tokenizer;
    return 0;
error:
    *output = tokenizer;
    return -1;
}

void chlm_tokenizer_destroy(chlm_tokenizer *tokenizer) { free(tokenizer); }
const char *chlm_tokenizer_last_error(const chlm_tokenizer *tokenizer) {
    return tokenizer ? tokenizer->error : "no tokenizer";
}
uint32_t chlm_tokenizer_vocab_size(const chlm_tokenizer *tokenizer) {
    return tokenizer ? tokenizer->header.vocab : 0;
}

int chlm_tokenizer_piece(const chlm_tokenizer *tokenizer, uint16_t token,
                         const uint8_t **piece, size_t *piece_bytes) {
    if (!tokenizer || !piece || !piece_bytes || token >= tokenizer->header.vocab) return -1;
    uint32_t begin = tokenizer->offsets[token], end = tokenizer->offsets[token + 1u];
    *piece = tokenizer->pieces + begin;
    *piece_bytes = end - begin;
    return 0;
}

int chlm_tokenizer_encode(const chlm_tokenizer *tokenizer, const char *text,
                          uint16_t *tokens, size_t capacity, size_t *token_count) {
    if (!tokenizer || !text || !tokens || !token_count) return -1;
    size_t count = 0;
    const uint8_t *cursor = (const uint8_t *)text;
    while (*cursor) {
        int special = -1;
        size_t special_bytes = 0;
        if (*cursor == '<') {
            for (uint32_t index = 0; index < CHTK_SPECIAL_COUNT; ++index) {
                size_t length = strlen(SPECIALS[index]);
                if (strncmp((const char *)cursor, SPECIALS[index], length) == 0) {
                    special = (int)index; special_bytes = length; break;
                }
            }
        }
        if (count >= capacity) return -1;
        if (special >= 0) {
            tokens[count++] = (uint16_t)special;
            cursor += special_bytes;
        } else {
            tokens[count++] = (uint16_t)(CHTK_SPECIAL_COUNT + *cursor++);
        }
    }
    for (uint32_t merge_index = 0; merge_index < tokenizer->header.merge_count; ++merge_index) {
        const ChtkMerge *merge = &tokenizer->merges[merge_index];
        size_t read = 0, write = 0;
        while (read < count) {
            if (read + 1u < count && tokens[read] == merge->left && tokens[read + 1u] == merge->right) {
                tokens[write++] = merge->token;
                read += 2u;
            } else {
                tokens[write++] = tokens[read++];
            }
        }
        count = write;
    }
    *token_count = count;
    return 0;
}
