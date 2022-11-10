"""This module implements a method to compute a 16 bit hash of the given bytes."""

import crc16


def hash(data: bytes) -> bytes:
    """Returns a two bytes hash code for the given data"""
    checksum: int = crc16.crc16xmodem(data)
    return checksum.to_bytes(2, 'big')


if __name__ == "__main__":
    print(hash((b'323456789')))
