import hashlib


def generate_md5_for_uploaded_file(file):
    md5_hash = hashlib.md5()
    for chunk in iter(lambda: file.read(4096), b""):
        md5_hash.update(chunk)
    return md5_hash.hexdigest()


def generate_md5_for_text(text):
    # Encode the text to convert it into bytes
    text_bytes = text.encode('utf-8')

    # Create an MD5 hash object
    md5 = hashlib.md5()

    # Update the hash object with the bytes-like object
    md5.update(text_bytes)

    # Return the hexadecimal representation of the MD5 hash
    return md5.hexdigest()
