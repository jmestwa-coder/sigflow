from pathlib import Path
from sigflow.core.engine import Engine
from sigflow.core.exceptions import ParseError
from sigflow.serializers.wire import dumps
from sigflow.utils.formatting import table


def parse_command(args) -> int:
    data = Path(args.path).read_bytes()

    try:
        result = Engine().process(data)
    except ParseError as exc:
        print(f"error: {exc}")
        return 1

    if args.format == "json":
        print(dumps(result.frames))
    else:
        rows = [("stream", "sequence", "size")] + [(f.stream_id, f.sequence, f.size) for f in result.frames]
        print(table(rows))

    return 0


def validate_command(args) -> int:
    data = Path(args.path).read_bytes()

    try:
        result = Engine().process(data)
    except ParseError as exc:
        print(f"error: {exc}")
        return 1

    for diag in result.diagnostics:
        print(f"{diag.severity}: {diag.code} at {diag.offset}: {diag.message}")

    print(f"frames={len(result.frames)} diagnostics={len(result.diagnostics)}")

    return 0 if not result.diagnostics else 1


def inspect_command(args) -> int:
    data = Path(args.path).read_bytes()
    print(f"path={args.path}")
    print(f"bytes={len(data)}")
    print(f"prefix={data[:32].hex()}")
    return 0


def replay_command(args) -> int:
    data = Path(args.path).read_bytes()
    result = Engine().process(data)
    for frame in result.frames:
        print(f"replay stream={frame.stream_id} sequence={frame.sequence} rate={args.rate}")
    return 0
