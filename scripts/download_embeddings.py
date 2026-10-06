"""Verified, pinned MiniLM download. No model weights are committed."""
from pathlib import Path
from scripts.download_model import download_verified

REVISION = '751bff37182d3f1213fa05d7196b954e230abad9'
MODEL_DIR = Path(__file__).resolve().parents[1] / '.models' / 'minilm'
ARTIFACTS = [
    ('onnx/model_quantized.onnx', 'model.onnx', 22972370, 'afdb6f1a0e45b715d0bb9b11772f032c399babd23bfc31fed1c170afc848bdb1'),
    ('tokenizer.json', 'tokenizer.json', 711661, 'da0e79933b9ed51798a3ae27893d3c5fa4a201126cef75586296df9b4d2c62a0'),
]


def main():
    for source, name, size, sha in ARTIFACTS:
        url = f'https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/{REVISION}/{source}'
        download_verified(url, MODEL_DIR / name, sha, size)
    print('MiniLM ready. Files verify again on first use.')


if __name__ == '__main__':
    main()
