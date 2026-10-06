"""Local MiniLM mean pooling and normalized FAISS similarity search."""
import hashlib
import importlib.util
import threading
from scripts.download_embeddings import MODEL_DIR, ARTIFACTS


class MiniLM:
    def __init__(self):
        self._lock = threading.Lock()
        self._session = None
        self._catalogue_key = None

    @property
    def available(self):
        return all((MODEL_DIR / item[1]).is_file() for item in ARTIFACTS) and all(importlib.util.find_spec(p) for p in ['onnxruntime', 'tokenizers', 'faiss'])

    def _load(self):
        if self._session is not None:
            return
        if not self.available:
            raise ValueError('Install requirements-membership.txt and run python -m scripts.download_embeddings.')
        for _, name, size, sha in ARTIFACTS:
            path = MODEL_DIR / name
            if path.stat().st_size != size or hashlib.sha256(path.read_bytes()).hexdigest() != sha:
                raise ValueError('Embedding artifact checksum failed. Download the pinned files again.')
        import onnxruntime as ort
        from tokenizers import Tokenizer
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        self._tokenizer = Tokenizer.from_file(str(MODEL_DIR / 'tokenizer.json'))
        self._session = ort.InferenceSession(str(MODEL_DIR / 'model.onnx'), sess_options=options, providers=['CPUExecutionProvider'])

    def _encode(self, texts):
        import numpy as np
        encoded = self._tokenizer.encode_batch(texts)
        if any(len(e.ids) > 256 for e in encoded):
            raise ValueError('Embedding input exceeds 256 tokens; shorten it rather than silently truncate.')
        length = max(len(e.ids) for e in encoded)
        ids = np.array([e.ids + [0] * (length - len(e.ids)) for e in encoded], dtype=np.int64)
        mask = np.array([[1] * len(e.ids) + [0] * (length - len(e.ids)) for e in encoded], dtype=np.int64)
        inputs = {'input_ids': ids, 'attention_mask': mask, 'token_type_ids': np.zeros_like(ids)}
        accepted = {entry.name for entry in self._session.get_inputs()}
        output = self._session.run(None, {k: v for k, v in inputs.items() if k in accepted})[0]
        vectors = (output * mask[..., None]).sum(axis=1) / mask.sum(axis=1)[:, None]
        vectors = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if not np.isfinite(vectors).all() or (norms == 0).any():
            raise ValueError('Embedding model returned invalid vectors.')
        return np.ascontiguousarray(vectors / norms)

    def similarities(self, query, plans):
        import faiss
        with self._lock:
            self._load()
            key = tuple((p['id'], p['benefits']) for p in plans)
            if key != self._catalogue_key:
                vectors = self._encode([p['benefits'] for p in plans])
                self._index = faiss.IndexFlatIP(vectors.shape[1])
                self._index.add(vectors)
                self._catalogue_key = key
            scores, indices = self._index.search(self._encode([query]), len(plans))
            ordered = [0.0] * len(plans)
            for score, index in zip(scores[0], indices[0]):
                ordered[int(index)] = float(score)
            return ordered
