import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings


def generate_embeddings_from_text(text):
    # Text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "\t"], chunk_size=10000, chunk_overlap=3000)
    splitted_docs = text_splitter.create_documents([text])

    embeddings_model = OpenAIEmbeddings()

    embeddings = embeddings_model.embed_documents(
        [doc.page_content for doc in splitted_docs])

    return {
        "splitted_docs": splitted_docs,
        "embeddings": embeddings
    }


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
