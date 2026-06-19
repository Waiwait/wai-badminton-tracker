def sse_event(data: str, event: str | None = None) -> str:
    lines = []

    if event:
        lines.append(f"event: {event}")
    
    for line in data.splitlines():
        lines.append(f"data: {line}")

    return "\n".join(lines) + "\n\n"