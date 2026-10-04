"""Optional CPU generation; never substitutes preview content for inference."""
import hashlib
import os
import threading
from pathlib import Path

from .pipeline import SelectedDraft
from scripts.download_model import MODEL_SHA256, DEFAULT_PATH


class LocalModel:
    def __init__(self, path: Path | None = None):
        self.path = path or Path(os.environ.get('STUDIO_MODEL_PATH', DEFAULT_PATH))
        self._model = None
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        return self.path.is_file()

    def call(self, prompt: str, max_tokens: int = 1500) -> str:
        with self._lock:
            if self._model is None:
                if not self.available:
                    raise ValueError('Model unavailable. Run scripts/download_model.py first.')
                with self.path.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                if digest != MODEL_SHA256:
                    raise ValueError('Model checksum failed. Download the pinned model again.')
                from llama_cpp import Llama
                self._model = Llama(model_path=str(self.path), n_ctx=8192, n_threads=min(4, os.cpu_count() or 1), n_batch=256, verbose=False)
            response = self._model.create_chat_completion(
                messages=[{'role': 'system', 'content': 'You extract business instructions faithfully. Return only the requested JSON; do not invent facts.'}, {'role': 'user', 'content': prompt}],
                response_format={'type': 'json_object', 'schema': SelectedDraft.model_json_schema()},
                temperature=0, max_tokens=min(max_tokens, 1500),
            )
            content = response['choices'][0]['message'].get('content')
            if not content:
                raise ValueError('The model returned no draft.')
            return content
