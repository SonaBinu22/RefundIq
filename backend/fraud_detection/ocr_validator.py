import os
import re

# Try to import pytesseract; gracefully degrade if not installed
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def _extract_text_from_image(file_path):
    """Extract text from image using Tesseract OCR."""
    if not OCR_AVAILABLE:
        return ""
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        return text.lower()
    except Exception:
        return ""


def _extract_text_from_pdf(file_path):
    """Basic PDF text extraction (reads raw bytes for simple PDFs)."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read().decode('latin-1', errors='ignore')
        # Extract printable text
        text = re.sub(r'[^\x20-\x7E\n]', ' ', content)
        return text.lower()
    except Exception:
        return ""


def _normalize_amount(text):
    """Find dollar/rupee amounts in text."""
    matches = re.findall(r'[\$₹]?\s*(\d{1,6}(?:[.,]\d{2})?)', text)
    amounts = []
    for m in matches:
        try:
            amounts.append(float(m.replace(',', '')))
        except ValueError:
            continue
    return amounts


def validate_invoice(file_path, claimed_order_id=None, claimed_amount=None, claimed_product=None):
    """
    Perform OCR on invoice file and validate against claimed data.
    Returns dict with validation result and risk_points.
    """
    result = {
        "invoice_match": True,
        "order_id_found": False,
        "amount_match": False,
        "product_found": False,
        "ocr_available": OCR_AVAILABLE,
        "risk_points": 0,
        "details": []
    }

    if not file_path or not os.path.exists(file_path):
        result["invoice_match"] = False
        result["risk_points"] = 25
        result["details"].append("Invoice file not found")
        return result

    # Extract text
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        text = _extract_text_from_pdf(file_path)
    else:
        text = _extract_text_from_image(file_path)

    if not text.strip():
        if not OCR_AVAILABLE:
            result["details"].append("OCR not available — install pytesseract for invoice validation")
            result["risk_points"] = 5
        else:
            result["invoice_match"] = False
            result["risk_points"] = 15
            result["details"].append("Could not extract text from invoice")
        return result

    mismatches = 0

    # Check order ID
    if claimed_order_id:
        order_norm = str(claimed_order_id).lower().replace('-', '').replace(' ', '')
        text_norm = text.replace('-', '').replace(' ', '')
        if order_norm in text_norm:
            result["order_id_found"] = True
            result["details"].append(f"Order ID '{claimed_order_id}' found in invoice")
        else:
            mismatches += 1
            result["details"].append(f"Order ID '{claimed_order_id}' NOT found in invoice")

    # Check amount
    if claimed_amount:
        extracted_amounts = _normalize_amount(text)
        claimed_float = float(claimed_amount)
        amount_found = any(abs(a - claimed_float) < claimed_float * 0.1 for a in extracted_amounts)
        result["amount_match"] = amount_found
        if not amount_found:
            mismatches += 1
            result["details"].append(f"Claimed amount {claimed_amount} not matched in invoice")
        else:
            result["details"].append(f"Claimed amount {claimed_amount} matched in invoice")

    # Check product name
    if claimed_product:
        product_words = claimed_product.lower().split()
        found_words = sum(1 for w in product_words if w in text and len(w) > 3)
        result["product_found"] = found_words >= max(1, len(product_words) // 2)
        if not result["product_found"]:
            mismatches += 1
            result["details"].append(f"Product '{claimed_product}' not found in invoice")
        else:
            result["details"].append(f"Product '{claimed_product}' found in invoice")

    # Scoring
    if mismatches >= 2:
        result["invoice_match"] = False
        result["risk_points"] = 25
    elif mismatches == 1:
        result["invoice_match"] = False
        result["risk_points"] = 12

    if not result["details"]:
        result["details"].append("Invoice validation passed")

    return result
