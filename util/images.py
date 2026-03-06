import base64


def get_b64_image(image_bytes: bytes | None) -> str:
    """Converts bytes to base64 data URI."""
    if not image_bytes:
        return ""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"
