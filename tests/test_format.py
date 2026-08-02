import struct

import torch

from circuitheroeslm.format import ENDIAN_MARKER, HEADER_BYTES, MAGIC, VERSION, name_hash, quantize_tensor, write_chlm
from circuitheroeslm.model import ESRConfig, EngineeringStateRouterLM


def test_name_hash_is_stable():
    assert name_hash("embedding.weight") == 0x93227924


def test_row_int8_error_is_bounded():
    torch.manual_seed(5)
    source = torch.randn(17, 31) * 0.2
    _, restored = quantize_tensor("test", source)
    assert (source - restored).abs().max().item() < 0.005


def test_chlm_header_contract(tmp_path=None):
    import tempfile
    from pathlib import Path
    config = ESRConfig(vocab_size=64, width=24, layers=2, lanes=4, state_width=8, mixer_width=40, context=16)
    model = EngineeringStateRouterLM(config)
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "model.chlm"
        write_chlm(path, config, model.state_dict())
        raw = path.read_bytes()
        magic, version, endian = struct.unpack_from("<4sHH", raw)
        assert magic == MAGIC
        assert version == VERSION
        assert endian == ENDIAN_MARKER
        assert len(raw) > HEADER_BYTES
