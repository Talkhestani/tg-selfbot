"""Image generation helpers: QR codes and barcodes."""

from __future__ import annotations

import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MediaToolError(Exception):
    """Raised when an image cannot be generated."""


def generate_qr(data: str, output: Path, *, box_size: int = 10) -> Path:
    import qrcode

    if not data.strip():
        raise MediaToolError("متن یا لینک خالی است")
    try:
        qr = qrcode.QRCode(
            version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=box_size, border=4
        )
        qr.add_data(data)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white")
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output)
    except Exception as exc:  # noqa: BLE001
        raise MediaToolError("ساخت کد QR انجام نشد") from exc
    return output


def generate_barcode(data: str, output: Path) -> Path:
    import barcode
    from barcode.writer import ImageWriter

    if not data.isdigit():
        raise MediaToolError("محتوای بارکد باید عددی باشد")
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        code = barcode.get("code128", data, writer=ImageWriter())
        full_path = code.save(str(output.with_suffix("")))
    except Exception as exc:  # noqa: BLE001
        raise MediaToolError("ساخت بارکد انجام نشد") from exc
    return Path(full_path)


def qr_as_bytes(data: str) -> bytes:
    """Return QR PNG bytes for a text payload."""
    import qrcode

    buffer = io.BytesIO()
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(buffer, format="PNG")
    return buffer.getvalue()
