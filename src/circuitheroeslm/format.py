"""Native CHLM v1 binary model format and reference quantization."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import struct
import zlib

import numpy as np
import torch

MAGIC = b"CHLM"
VERSION = 1
ENDIAN_MARKER = 0x1234
HEADER_BYTES = 64
ENTRY_BYTES = 64
DTYPE_FLOAT32 = 1
DTYPE_ROW_INT8 = 2


def name_hash(name: str) -> int:
    value = 2166136261
    for byte in name.encode("utf-8"):
        value = ((value ^ byte) * 16777619) & 0xFFFFFFFF
    return value


def align16(value: int) -> int:
    return (value + 15) & ~15


@dataclass
class PackedTensor:
    name: str
    name_hash: int
    dtype: int
    shape: tuple[int, ...]
    data: bytes
    scales: bytes = b""


def quantize_tensor(name: str, tensor: torch.Tensor) -> tuple[PackedTensor, torch.Tensor]:
    source = tensor.detach().cpu().float().contiguous()
    if source.ndim < 2:
        raw = source.numpy().astype("<f4", copy=False).tobytes()
        return PackedTensor(name, name_hash(name), DTYPE_FLOAT32, tuple(source.shape), raw), source
    rows = int(np.prod(source.shape[:-1]))
    columns = source.shape[-1]
    matrix = source.reshape(rows, columns)
    scales = (matrix.abs().amax(dim=1) / 127.0).clamp_min(1e-12).float()
    codes = torch.clamp(torch.round(matrix / scales[:, None]), -127, 127).to(torch.int8)
    restored = (codes.float() * scales[:, None]).reshape(source.shape)
    packed = PackedTensor(name, name_hash(name), DTYPE_ROW_INT8, tuple(source.shape),
                          codes.numpy().tobytes(), scales.numpy().astype("<f4", copy=False).tobytes())
    return packed, restored


def quantized_state_dict(state_dict: dict[str, torch.Tensor]) -> tuple[list[PackedTensor], dict[str, torch.Tensor]]:
    packed, restored = [], {}
    hashes: dict[int, str] = {}
    for name in sorted(state_dict):
        item, dequantized = quantize_tensor(name, state_dict[name])
        if item.name_hash in hashes:
            raise ValueError(f"tensor hash collision: {name} and {hashes[item.name_hash]}")
        hashes[item.name_hash] = name
        packed.append(item)
        restored[name] = dequantized
    return packed, restored


def write_chlm(path: str | Path, config, state_dict: dict[str, torch.Tensor]) -> dict:
    tensors, _ = quantized_state_dict(state_dict)
    directory_offset = HEADER_BYTES
    data_offset = align16(directory_offset + ENTRY_BYTES * len(tensors))
    cursor = data_offset
    placements = []
    for tensor in tensors:
        payload_offset = cursor
        cursor = align16(cursor + len(tensor.data))
        scale_offset = cursor if tensor.scales else 0
        if tensor.scales:
            cursor = align16(cursor + len(tensor.scales))
        placements.append((tensor, payload_offset, scale_offset))
    image = bytearray(cursor)
    entries = []
    for tensor, payload_offset, scale_offset in placements:
        image[payload_offset:payload_offset + len(tensor.data)] = tensor.data
        if tensor.scales:
            image[scale_offset:scale_offset + len(tensor.scales)] = tensor.scales
        dims = list(tensor.shape) + [1] * (4 - len(tensor.shape))
        if len(tensor.shape) > 4:
            raise ValueError(f"tensor rank above four is unsupported: {tensor.name}")
        entry = struct.pack("<IBBH4I10I", tensor.name_hash, tensor.dtype, len(tensor.shape), 0,
                            *dims, payload_offset, len(tensor.data), scale_offset, len(tensor.scales),
                            zlib.crc32(tensor.data), zlib.crc32(tensor.scales), 0, 0, 0, 0)
        if len(entry) != ENTRY_BYTES:
            raise AssertionError("CHLM directory entry size mismatch")
        entries.append(entry)
    for index, entry in enumerate(entries):
        start = directory_offset + index * ENTRY_BYTES
        image[start:start + ENTRY_BYTES] = entry
    payload_crc = zlib.crc32(image[data_offset:])
    header = struct.pack("<4sHH3I7If3I", MAGIC, VERSION, ENDIAN_MARKER, HEADER_BYTES, ENTRY_BYTES,
                         len(tensors), config.vocab_size, config.width, config.layers, config.lanes,
                         config.state_width, config.mixer_width, config.context, config.norm_epsilon,
                         directory_offset, data_offset, payload_crc)
    if len(header) != HEADER_BYTES:
        raise AssertionError("CHLM header size mismatch")
    image[:HEADER_BYTES] = header
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image)
    manifest = {"schema": "circuitheroeslm-chlm-v1-manifest", "format": "CHLM", "version": VERSION,
                "bytes": len(image), "payload_crc32": f"{payload_crc:08x}",
                "config": config.to_dict(), "tensors": [
                    {"name": item.name, "hash": f"{item.name_hash:08x}", "dtype": item.dtype,
                     "shape": list(item.shape), "data_bytes": len(item.data), "scale_bytes": len(item.scales)}
                    for item in tensors]}
    output.with_suffix(output.suffix + ".json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
