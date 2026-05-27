import struct
import pytest
from sigflow.core.context import ExecutionContext
from sigflow.core.exceptions import ParseError
from sigflow.parsers.binary import BinaryFrameParser
from sigflow.parsers.tlv import TLVParser
from sigflow.parsers.legacy import LegacyParser

TLV = struct.Struct(">HH")
LEGACY = struct.Struct(">HI")


def test_binary_parser_reads_frames(sample_stream):
    frames = BinaryFrameParser().parse(sample_stream, ExecutionContext({}))
    assert [f.payload for f in frames] == [b"alpha", b"beta"]


def test_binary_parser_reports_truncation(sample_stream):
    ctx = ExecutionContext({})
    frames = BinaryFrameParser().parse(sample_stream[:-2], ctx)

    assert frames
    assert any(
        d.code in {"truncated-header", "truncated-payload", "checksum"}
        for d in ctx.diagnostics
    )


def test_invalid_magic_raises():
    with pytest.raises(ParseError):
        BinaryFrameParser().parse(
            b"NOPE" + b"0" * 32,
            ExecutionContext({})
        )


def test_tlv_parser_stops_at_max_frames():
    data = (
        TLV.pack(1, 1) + b"a" +
        TLV.pack(2, 1) + b"b" +
        TLV.pack(3, 1) + b"c"
    )

    parser = TLVParser()
    parser.max_frames = 2

    ctx = ExecutionContext({})
    frames = parser.parse(data, ctx)

    assert len(frames) == 2
    assert any(d.code == "frame-limit" for d in ctx.diagnostics)


def test_legacy_parser_stops_at_max_frames():
    data = (
        LEGACY.pack(1, 1) + b"a" +
        LEGACY.pack(2, 1) + b"b" +
        LEGACY.pack(3, 1) + b"c"
    )

    parser = LegacyParser()
    parser.max_frames = 2

    ctx = ExecutionContext({})
    frames = parser.parse(data, ctx)

    assert len(frames) == 2
    assert any(d.code == "frame-limit" for d in ctx.diagnostics)


def test_tlv_truncated_value_is_recoverable():
   
    data = b"\x00\x01" + b"\x00\x04" + b"AB"
    ctx = ExecutionContext({})
    frames = TLVParser().parse(data, ctx)

    assert frames == []
    assert any(d.code == "tlv-truncated" for d in ctx.diagnostics)