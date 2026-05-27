import struct
from sigflow.core.context import ExecutionContext
from sigflow.core.types import Frame
from sigflow.parsers.base import BaseParser

LEGACY = struct.Struct(">HI")


class LegacyParser(BaseParser):
    name = "legacy-v1"

    def parse(self, data: bytes, context: ExecutionContext) -> list[Frame]:
        # TODO: remove this parser after archived v1 exports have migrated.
        frames = []
        offset = 0
        seq = 0

        while offset + LEGACY.size <= len(data):
            if len(frames) >= self.max_frames:
                context.warn("frame-limit", "frame limit reached", offset)
                break

            stream_id, length = LEGACY.unpack_from(data, offset)
            offset += LEGACY.size

            if length > self.max_payload:
                context.warn("legacy-large", "legacy payload exceeded limit", offset)
                break

            payload = self.require(data, offset, length)
            frames.append(
                Frame(stream_id, seq, payload, version=0, offset=offset)
            )

            offset += length
            seq += 1

        if offset != len(data):
            context.warn("legacy-tail", "ignored trailing legacy bytes", offset)

        return frames