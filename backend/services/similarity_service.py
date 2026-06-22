"""
Semantic Similarity Fraud Detection (Feature 2)
Uses sentence-transformers to detect duplicate/near-duplicate refund descriptions.
Falls back to TF-IDF cosine similarity if transformers unavailable.
"""
import json
import numpy as np

SIMILARITY_THRESHOLD = 0.82   # configurable

# Try to load sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer('all-MiniLM-L6-v2')
    TRANSFORMER_AVAILABLE = True
except Exception:
    TRANSFORMER_AVAILABLE = False

# Fallback: TF-IDF
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as sk_cosine
    TFIDF_AVAILABLE = True
except ImportError:
    TFIDF_AVAILABLE = False


def _cosine(a, b):
    a, b = np.array(a), np.array(b)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def get_embedding(text: str) -> list:
    if TRANSFORMER_AVAILABLE:
        return _model.encode(text).tolist()
    # Fallback: return None (will use TF-IDF at comparison time)
    return []


def compare_descriptions(new_text: str, existing_refunds: list) -> dict:
    """
    Compare new_text against list of {'refund_id', 'description', 'embedding'}.
    Returns best match result.
    """
    if not existing_refunds:
        return {'flagged': False, 'similarity_score': 0.0, 'matched_refund_id': None, 'fraud_probability': 0.0}

    if TRANSFORMER_AVAILABLE:
        new_emb = _model.encode(new_text).tolist()
        best_score = 0.0
        best_id = None

        for ref in existing_refunds:
            emb = ref.get('embedding')
            if not emb:
                continue
            score = _cosine(new_emb, emb)
            if score > best_score:
                best_score = score
                best_id = ref['refund_id']

        flagged = best_score >= SIMILARITY_THRESHOLD
        fraud_prob = min(best_score * 1.1, 1.0) if flagged else best_score * 0.5
        return {
            'flagged': flagged,
            'similarity_score': round(best_score, 4),
            'matched_refund_id': best_id if flagged else None,
            'fraud_probability': round(fraud_prob, 4),
            'embedding': new_emb
        }

    elif TFIDF_AVAILABLE:
        # TF-IDF fallback
        texts = [new_text] + [r['description'] for r in existing_refunds if r.get('description')]
        if len(texts) < 2:
            return {'flagged': False, 'similarity_score': 0.0, 'matched_refund_id': None, 'fraud_probability': 0.0}

        vec = TfidfVectorizer().fit_transform(texts)
        sims = sk_cosine(vec[0:1], vec[1:]).flatten()
        best_idx = int(np.argmax(sims))
        best_score = float(sims[best_idx])
        best_id = existing_refunds[best_idx]['refund_id'] if best_idx < len(existing_refunds) else None
        flagged = best_score >= SIMILARITY_THRESHOLD
        return {
            'flagged': flagged,
            'similarity_score': round(best_score, 4),
            'matched_refund_id': best_id if flagged else None,
            'fraud_probability': round(min(best_score * 1.1, 1.0) if flagged else best_score * 0.4, 4),
            'embedding': []
        }

    return {'flagged': False, 'similarity_score': 0.0, 'matched_refund_id': None, 'fraud_probability': 0.0}
