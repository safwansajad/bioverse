from reedsolo import RSCodec, ReedSolomonError

# 32 parity bytes (can correct up to 16 byte errors)
ECC_SYMBOLS = 32
rsc = RSCodec(ECC_SYMBOLS)


def ecc_encode(data: bytes) -> bytes:
    """Apply Reed-Solomon error correction encoding."""
    if not data:
        raise ValueError("Cannot ECC-encode empty data")
    return bytes(rsc.encode(data))


def ecc_decode(data: bytes) -> bytes:
    """
    Decode Reed-Solomon encoded data, correcting errors if possible.
    Raises ReedSolomonError if data is too corrupted.
    """
    if not data:
        raise ValueError("Cannot ECC-decode empty data")
    try:
        decoded = rsc.decode(data)
        return bytes(decoded[0])
    except ReedSolomonError as e:
        raise ValueError(f"ECC decoding failed — data may be corrupted: {e}")
