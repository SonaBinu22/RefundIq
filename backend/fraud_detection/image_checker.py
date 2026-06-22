import cv2
import numpy as np
import os
import hashlib


# In-memory store for image hashes to detect duplicates within a session
# In production, persist this to the database
_image_hash_store = {}


def _compute_phash(image):
    """Perceptual hash for duplicate detection."""
    resized = cv2.resize(image, (32, 32))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    mean = gray.mean()
    bits = (gray > mean).flatten()
    return ''.join(['1' if b else '0' for b in bits])


def _hamming_distance(h1, h2):
    return sum(c1 != c2 for c1, c2 in zip(h1, h2))


def _check_blur(image):
    """Laplacian variance — low value means blurry."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance, variance < 100.0


def _check_manipulation(image):
    """Detect JPEG compression artifacts as manipulation indicator."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.count_nonzero(edges) / edges.size
    # Very high edge density with specific patterns can indicate tampering
    return edge_density > 0.35


def analyze_image(file_path):
    """
    Analyze an image file for quality, duplicates, and manipulation.
    Returns a dict with analysis results and risk_points.
    """
    result = {
        "image_quality": "good",
        "blur_score": 0.0,
        "duplicate_found": False,
        "manipulation_detected": False,
        "risk_points": 0,
        "details": []
    }

    if not file_path or not os.path.exists(file_path):
        result["image_quality"] = "missing"
        result["risk_points"] = 25
        result["details"].append("Image file not found")
        return result

    try:
        image = cv2.imread(file_path)
        if image is None:
            result["image_quality"] = "unreadable"
            result["risk_points"] = 20
            result["details"].append("Could not read image file")
            return result

        # Blur check
        variance, is_blurry = _check_blur(image)
        result["blur_score"] = round(variance, 2)
        if is_blurry:
            result["image_quality"] = "blurry"
            result["risk_points"] += 15
            result["details"].append(f"Image appears blurry (sharpness score: {variance:.1f})")

        # Duplicate check
        phash = _compute_phash(image)
        file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()

        for stored_path, (stored_phash, stored_md5) in _image_hash_store.items():
            if stored_path == file_path:
                continue
            if stored_md5 == file_hash:
                result["duplicate_found"] = True
                result["risk_points"] += 30
                result["details"].append(f"Exact duplicate of previously submitted image")
                break
            if _hamming_distance(phash, stored_phash) < 10:
                result["duplicate_found"] = True
                result["risk_points"] += 25
                result["details"].append("Very similar image to a previous submission detected")
                break

        _image_hash_store[file_path] = (phash, file_hash)

        # Manipulation check
        if _check_manipulation(image):
            result["manipulation_detected"] = True
            result["risk_points"] += 10
            result["details"].append("Possible image manipulation indicators found")

        if not result["details"]:
            result["details"].append("Image passed all quality checks")

    except Exception as e:
        result["image_quality"] = "error"
        result["risk_points"] = 10
        result["details"].append(f"Analysis error: {str(e)}")

    return result
