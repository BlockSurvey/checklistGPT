INSERT_EMBEDDING_DOCUMENT_MUTATION = """
    mutation InsertEmbeddingDocument($embeddingDocuments: [embeddings_document_insert_input!]!, $embeddings: [embeddings_insert_input!]!) {
        insert_embeddings_document(objects: $embeddingDocuments) {
            affected_rows
        }
        insert_embeddings(objects: $embeddings) {
            affected_rows
        }
    }
"""

QUERY_EMBEDDINGS_DOCUMENT_BY_HASH = """
    query QueryEmbeddingsDocumentByHash($md5_hash: String!, $orgId: uuid!) {
        embeddings_document(where: {md5_hash: {_eq: $md5_hash}, org_id: {_eq: $orgId}}) {
            embeddings {
            text
            embedding
            }
        }
    }
"""
