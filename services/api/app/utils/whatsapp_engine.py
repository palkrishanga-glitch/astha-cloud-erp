import urllib.parse

def generate_whatsapp_invoice_link(
    mobile: str,
    customer_name: str,
    invoice_no: str,
    invoice_date: str,
    grand_total: float,
    pdf_download_url: str = ""
) -> str:
    """
    Part 16 WhatsApp Sharing Engine:
    Generates click-to-chat WhatsApp link with pre-formatted invoice summary text.
    """
    # Sanitize mobile number (remove non-digits, ensure country code)
    clean_mobile = ''.join(filter(str.isdigit, mobile))
    if len(clean_mobile) == 10:
        clean_mobile = "91" + clean_mobile

    msg = (
        f"Hello {customer_name},\n\n"
        f"Thank you for doing business with *Astha Builders & Hardware*!\n\n"
        f"🧾 *Invoice No:* {invoice_no}\n"
        f"📅 *Date:* {invoice_date}\n"
        f"💰 *Total Amount:* Rs {grand_total:,.2f}\n\n"
    )

    if pdf_download_url:
        msg += f"📥 *Download Invoice PDF:* {pdf_download_url}\n\n"

    msg += "For any queries, please contact our support team."

    encoded_text = urllib.parse.quote(msg)
    return f"https://wa.me/{clean_mobile}?text={encoded_text}"
