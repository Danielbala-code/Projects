"""Download the official UCI source with the checksum verified in this build."""
from pathlib import Path
from scripts.download_model import download_verified
URL='https://archive.ics.uci.edu/static/public/352/data.csv'
SHA256='a2f79bbdd4463df6db8a3f5a50b9c980ae8f645a370bf5e2c0d6097f9e817b05'
SIZE=45_038_760
DEST=Path(__file__).resolve().parents[1]/'.runtime/audience/online-retail.csv'
if __name__=='__main__':download_verified(URL,DEST,SHA256,SIZE)
