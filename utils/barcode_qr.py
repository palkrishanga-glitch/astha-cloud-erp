import io
import barcode
from barcode.writer import ImageWriter
import qrcode

def generate_barcode_png_bytes(data_str: str) -> bytes:
    """Generates Code128 Barcode PNG image bytes for products or invoices."""
    rv = io.BytesIO()
    code128 = barcode.get_barcode_class('code128')
    bc = code128(data_str, writer=ImageWriter())
    bc.write(rv)
    rv.seek(0)
    return rv.getvalue()

def generate_qr_code_png_bytes(data_str: str) -> bytes:
    """Generates QR Code PNG image bytes for UPI payments or invoice links."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=2,
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    rv = io.BytesIO()
    img.save(rv, format="PNG")
    rv.seek(0)
    return rv.getvalue()
