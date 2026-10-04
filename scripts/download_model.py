"""Download a pinned public model, checking its exact size and SHA-256."""
import argparse
import hashlib
import urllib.request
from pathlib import Path

MODEL_REPO = 'Qwen/Qwen2.5-1.5B-Instruct-GGUF'
MODEL_REVISION = '91cad51170dc346986eccefdc2dd33a9da36ead9'
MODEL_FILE = 'qwen2.5-1.5b-instruct-q4_k_m.gguf'
MODEL_SHA256 = '6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e'
MODEL_SIZE = 1_117_320_736
DEFAULT_PATH = Path(__file__).resolve().parents[1]/'.models'/MODEL_FILE


def download_verified(url: str, destination: Path, sha256: str, size: int, opener=urllib.request.urlopen) -> Path:
    destination = Path(destination)
    if destination.is_file() and destination.stat().st_size == size:
        with destination.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() == sha256:
                print('Existing model checksum verified.')
                return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix+'.part')
    digest = hashlib.sha256(); received = 0
    try:
        with opener(url, timeout=60) as response, partial.open('wb') as stream:
            while block := response.read(1024*1024):
                received += len(block)
                if received > size:
                    raise ValueError('Download exceeds the pinned model size.')
                digest.update(block); stream.write(block)
        if received != size or digest.hexdigest() != sha256:
            raise ValueError('Model size or SHA-256 verification failed.')
        partial.replace(destination)
        print(f'Verified {received:,} bytes. Model ready at {destination}.')
        return destination
    finally:
        partial.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    url = f'https://huggingface.co/{MODEL_REPO}/resolve/{MODEL_REVISION}/{MODEL_FILE}'
    try:
        download_verified(url, args.output, MODEL_SHA256, MODEL_SIZE)
    except Exception as exc:
        print(f'Download failed ({type(exc).__name__}). Check network access and disk space, then retry. Existing files were preserved.')
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
