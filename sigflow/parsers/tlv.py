import struct
from sigflow.core.context import ExecutionContext
from sigflow.core.types import Frame
from sigflow.parsers.base import BaseParser

TLV = struct.Struct(">HH")


class TLVParser(BaseParser):
    name = "tlv"

    def parse(self, data: bytes, context: ExecutionContext) -> list[Frame]:
        frames = []
        offset = 0
        seq = 0
        while offset < len(data):
            # Need at least the TLV header (tag + length)
            if len(data) - offset < TLV.size:
                context.warn("tlv-truncated", "partial tlv header", offset)
                break

            tag, length = TLV.unpack_from(data, offset)
            offset += TLV.size

            if length > self.max_payload:
                context.warn("tlv-large", f"tag {tag} exceeds max payload", offset)
                break

            # If the TLV header is present, but the declared value bytes are truncated,
            # downgrade to a recoverable diagnostic (consistent with BinaryFrameParser).
            if offset + length > len(data):
                context.warn("tlv-truncated", "truncated tlv value", offset)
                break

            value = self.require(data, offset, length)
            frames.append(Frame(tag, seq, value, metadata={"tag": tag}))
            seq += 1
            offset += length
        return frames

