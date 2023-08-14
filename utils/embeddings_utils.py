import uuid
import json
from typing import Dict, List
from services.hasura_service import HasuraService
from gql.embeddings import INSERT_EMBEDDING_DOCUMENT_MUTATION, QUERY_EMBEDDINGS_DOCUMENT_BY_HASH
from utils.utils import get_user_id
from langchain.schema import Document


def fetch_embeddings_from_database(md5_hash, orgId):
    embeddingsDocumentDetails = query_embeddings_document_by_md5_hash(
        md5_hash, orgId)
    if (embeddingsDocumentDetails.get("data", None) is None or embeddingsDocumentDetails["data"].get("embeddings_document", None) is None or
            len(embeddingsDocumentDetails["data"]["embeddings_document"]) == 0):
        return None

    embeddingsDocumentDetails = embeddingsDocumentDetails["data"]["embeddings_document"][0]
    embeddings = embeddingsDocumentDetails.get("embeddings", None)

    if embeddings is None or len(embeddings) == 0:
        return None

    result_docs = []
    result_embeddings = []
    for embedding in embeddings:
        result_docs.append(Document(page_content=embedding["text"]))
        result_embeddings.append(json.loads(embedding["embedding"]))

    result = {
        "splitted_docs": result_docs,
        "embeddings": result_embeddings
    }

    return result


def query_embeddings_document_by_md5_hash(md5_hash, orgId):
    hasura_service = HasuraService()
    result = hasura_service.execute(
        QUERY_EMBEDDINGS_DOCUMENT_BY_HASH,
        {
            "md5_hash": md5_hash,
            "orgId": orgId
        }
    )
    return result


def save_embeddings(documents: List[Dict], embeddings: List[Dict], name, md5_hash, org_id):
    insert_embeddings_document = {
        "id": str(uuid.uuid4()),
        "name": name,
        "md5_hash": md5_hash,
        "org_id": org_id,
        "created_by": get_user_id()
    }
    insert_embeddings_documents = [insert_embeddings_document]

    insert_embeddings = []
    for index, each_embedding in enumerate(embeddings):
        insert_embeddings.append({
            "text": documents[index].page_content,
            "embedding": json.dumps(each_embedding),
            "embeddings_document_id": insert_embeddings_document["id"],
            "created_by": get_user_id(),
            "order_number": index
        })

    execute_save_embeddings(insert_embeddings_documents, insert_embeddings)


def execute_save_embeddings(insert_embeddings_documents: List[Dict], insert_embeddings: List[Dict]):
    if (insert_embeddings_documents is None or len(insert_embeddings_documents) == 0):
        raise ValueError("Embeddings documents must present to insert.")

    if (insert_embeddings is None or len(insert_embeddings) == 0):
        raise ValueError("Embeddings must present to insert.")

    # get agent by id from database
    hasura_service = HasuraService()
    result = hasura_service.execute(INSERT_EMBEDDING_DOCUMENT_MUTATION, {
        "embeddingDocuments": insert_embeddings_documents,
        "embeddings": insert_embeddings
    })

    return result
