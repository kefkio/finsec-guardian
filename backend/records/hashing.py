import hashlib


def sha256(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def compute_content_hash(content: str) -> str:
    return sha256(content)


def compute_chain_hash(content_hash: str, previous_hash: str) -> str:
    return sha256(content_hash + previous_hash)
