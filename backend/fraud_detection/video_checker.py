import cv2
import numpy as np
import os


def _extract_frames(video_path, interval_sec=3):
    """Extract frames every `interval_sec` seconds from video."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_interval = int(fps * interval_sec)
    frames = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            frames.append(frame)
        frame_idx += 1

    cap.release()
    return frames


def _check_frame_quality(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def _frames_are_similar(f1, f2, threshold=0.98):
    """Compare two frames for near-identical content (repeated frames)."""
    f1_small = cv2.resize(f1, (64, 64))
    f2_small = cv2.resize(f2, (64, 64))
    diff = cv2.absdiff(f1_small, f2_small)
    similarity = 1 - (diff.mean() / 255.0)
    return similarity > threshold


def analyze_video(file_path):
    """
    Analyze a video for quality and validity.
    Returns dict with analysis results and risk_points.
    """
    result = {
        "video_validity": "valid",
        "frame_count": 0,
        "avg_quality_score": 0.0,
        "repeated_frames_detected": False,
        "product_evidence_found": True,
        "risk_points": 0,
        "details": []
    }

    if not file_path or not os.path.exists(file_path):
        result["video_validity"] = "missing"
        result["risk_points"] = 25
        result["details"].append("Video file not found")
        return result

    try:
        frames = _extract_frames(file_path, interval_sec=3)
        result["frame_count"] = len(frames)

        if len(frames) == 0:
            result["video_validity"] = "unreadable"
            result["risk_points"] = 20
            result["details"].append("Could not extract frames from video")
            return result

        quality_scores = [_check_frame_quality(f) for f in frames]
        avg_quality = np.mean(quality_scores)
        result["avg_quality_score"] = round(float(avg_quality), 2)

        # Quality check
        if avg_quality < 80:
            result["video_validity"] = "low_quality"
            result["risk_points"] += 15
            result["details"].append(f"Video quality is low (avg sharpness: {avg_quality:.1f})")

        # Repeated frames (slideshow detection)
        if len(frames) >= 2:
            similar_pairs = 0
            for i in range(len(frames) - 1):
                if _frames_are_similar(frames[i], frames[i + 1]):
                    similar_pairs += 1
            repeat_ratio = similar_pairs / (len(frames) - 1)
            if repeat_ratio > 0.7:
                result["repeated_frames_detected"] = True
                result["risk_points"] += 20
                result["details"].append("Suspicious: video appears to be a repeated/static image slideshow")

        if not result["details"]:
            result["details"].append("Video passed all quality checks")

    except Exception as e:
        result["video_validity"] = "error"
        result["risk_points"] = 10
        result["details"].append(f"Analysis error: {str(e)}")

    return result
