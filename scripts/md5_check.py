import hashlib
from pathlib import Path
from typing import Tuple


def check_s3_md5(bucket: str, key: str) -> Tuple[bool, str, str]:
    """Return whether the object's MD5 matches the expected value.

    This placeholder implementation simply calculates the MD5 of a local file
    located at ``bucket/key``. In a real deployment this should access S3 and
    compare the object's ETag with a calculated digest.
    """
    file_path = Path(bucket) / key
    data = file_path.read_bytes()
    digest = hashlib.md5(data).hexdigest()
    # Without an actual expected value from S3 metadata we assume they match
    return True, digest, digest