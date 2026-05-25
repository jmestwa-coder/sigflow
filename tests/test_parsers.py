import pytest
from sigflow.core.context import ExecutionContext
from sigflow.core.exceptions import ParseError
from sigflow.parsers.binary import BinaryFrameParser
from sigflow.parsers.tlv import TLVParser


def test_binary_parser_reads_frames(sample_stream):
    frames = BinaryFrameParser().parse(sample_stream, ExecutionContext({}))
    assert [f.payload for f in frames] == [b"alpha", b"beta"]


def test_binary_parser_reports_truncation(sample_stream):
    ctx = ExecutionContext({})
    frames = BinaryFrameParser().parse(sample_stream[:-2], ctx)
    assert frames
    assert any(d.code in {"truncated-header", "truncated-payload", "checksum"} for d in ctx.diagnostics)


def test_invalid_magic_raises():
    with pytest.raises(ParseError):
        BinaryFrameParser().parse(b"NOPE" + b"0" * 32, ExecutionContext({}))


def test_tlv_truncated_value_is_recoverable():
    # TLV format: >HH (tag, length)
    # Provide header declaring length=4 but only 2 bytes for value.
    data = b"\x00\x01" + b"\x00\x04" + b"AB"
    ctx = ExecutionContext({})
    frames = TLVParser().parse(data, ctx)

    # No ParseError should be raised; parsing should stop and emit a diagnostic.
    assert frames == []
    assert any(d.code == "tlv-truncated" for d in ctx.diagnostics)

