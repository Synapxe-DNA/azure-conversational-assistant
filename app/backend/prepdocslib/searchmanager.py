import asyncio
import logging
import os
from typing import List, Optional

from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
    VectorSearchVectorizer,
)

from .embeddings import OpenAIEmbeddings
from .listfilestrategy import File
from .strategy import SearchInfo
from .textsplitter import SplitPage

logger = logging.getLogger("ingester")


class Section:
    """
    A section of a page that is stored in a search service. These sections are used as context by Azure OpenAI service
    """

    def __init__(self, split_page: SplitPage, content: File, category: Optional[str] = None):
        self.split_page = split_page
        self.content = content
        self.category = category


class SearchManager:
    """
    Class to manage a search service. It can create indexes, and update or remove sections stored in these indexes
    To learn more, please visit https://learn.microsoft.com/azure/search/search-what-is-azure-search
    """

    def __init__(
        self,
        search_info: SearchInfo,
        search_analyzer_name: Optional[str] = None,
        use_acls: bool = False,
        use_int_vectorization: bool = False,
        embeddings: Optional[OpenAIEmbeddings] = None,
        search_images: bool = False,
    ):
        self.search_info = search_info
        self.search_analyzer_name = search_analyzer_name
        self.use_acls = use_acls
        self.use_int_vectorization = use_int_vectorization
        self.embeddings = embeddings
        # Integrated vectorization uses the ada-002 model with 1536 dimensions
        self.embedding_dimensions = self.embeddings.open_ai_dimensions if self.embeddings else 1536
        self.search_images = search_images

    async def create_index(self, vectorizers: Optional[List[VectorSearchVectorizer]] = None):
        logger.info("Ensuring search index %s exists", self.search_info.index_name)

        async with self.search_info.create_search_index_client() as search_index_client:
            fields = []

            if self.use_int_vectorization:
                fields.append(SearchableField(name="parent_id", type=SearchFieldDataType.String, filterable=True))
                fields.append(
                    SearchField(
                        name="id",
                        type=SearchFieldDataType.String,
                        key=True,
                        sortable=True,
                        filterable=True,
                        facetable=True,
                        analyzer_name="keyword",
                    )
                )
            else:
                fields.append(SimpleField(name="id", type=SearchFieldDataType.String, key=True))

            fields.extend(
                [
                    SearchableField(
                        name="title",
                        type=SearchFieldDataType.String,
                        analyzer_name="en.lucene" if self.search_analyzer_name is None else self.search_analyzer_name,
                    ),
                    SimpleField(name="cover_image_url", type=SearchFieldDataType.String),
                    SimpleField(name="full_url", type=SearchFieldDataType.String),
                    SearchableField(
                        name="content_category",
                        type=SearchFieldDataType.String,
                        analyzer_name="en.lucene" if self.search_analyzer_name is None else self.search_analyzer_name,
                        filterable=True,
                    ),
                    SearchableField(
                        name="category_description",
                        type=SearchFieldDataType.String,
                        analyzer_name="en.lucene" if self.search_analyzer_name is None else self.search_analyzer_name,
                    ),
                    SimpleField(name="pr_name", type=SearchFieldDataType.String),
                    SimpleField(name="date_modified", type=SearchFieldDataType.String),
                    # SearchableField(
                    #     name="content",
                    #     type=SearchFieldDataType.String,
                    #     analyzer_name="en.lucene" if self.search_analyzer_name is None else self.search_analyzer_name
                    #     ),
                    SearchableField(
                        name="chunks",
                        type=SearchFieldDataType.String,
                        analyzer_name="en.lucene" if self.search_analyzer_name is None else self.search_analyzer_name,
                    ),
                    SearchField(
                        name="embedding",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        hidden=False,
                        searchable=True,
                        filterable=False,
                        sortable=False,
                        facetable=False,
                        vector_search_dimensions=self.embedding_dimensions,
                        vector_search_profile_name="embedding_config",
                    ),
                ]
            )

            if self.use_acls:
                fields.extend(
                    [
                        SimpleField(
                            name="oids",
                            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                            filterable=True,
                        ),
                        SimpleField(
                            name="groups",
                            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                            filterable=True,
                        ),
                    ]
                )

            if self.search_images:
                fields.append(
                    SearchField(
                        name="imageEmbedding",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        hidden=False,
                        searchable=True,
                        filterable=False,
                        sortable=False,
                        facetable=False,
                        vector_search_dimensions=1024,
                        vector_search_profile_name="embedding_config",
                    ),
                )

            index = SearchIndex(
                name=self.search_info.index_name,
                fields=fields,
                semantic_search=SemanticSearch(
                    configurations=[
                        SemanticConfiguration(
                            name="default",
                            prioritized_fields=SemanticPrioritizedFields(
                                title_field=SemanticField(field_name="title"),
                                content_fields=[
                                    SemanticField(field_name="chunks"),
                                ],  # This is where the caption is, can create a new metadata field for this. The order of the field indicates the priority of the search.
                            ),
                        )
                    ]
                ),
                vector_search=VectorSearch(
                    # See: https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.indexes.models.vectorsearchalgorithmconfiguration?view=azure-python
                    # Algorithm used for vector search
                    algorithms=[
                        HnswAlgorithmConfiguration(name="hnsw_config", parameters=HnswParameters(metric="cosine"))
                    ],
                    # See: https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.indexes.models.vectorsearchprofile?view=azure-python
                    # Specify the profiles for the vector search and computing the embeddings
                    profiles=[
                        VectorSearchProfile(
                            name="embedding_config",
                            algorithm_configuration_name="hnsw_config",
                            vectorizer=(
                                f"{self.search_info.index_name}-vectorizer" if self.use_int_vectorization else None
                            ),
                        ),
                    ],
                    # See: https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.indexes.models.vectorsearchvectorizer?view=azure-python
                    # See: https://learn.microsoft.com/en-us/azure/search/vector-search-vectorizer-azure-open-ai
                    vectorizers=vectorizers,
                ),
            )

            if self.search_info.index_name not in [name async for name in search_index_client.list_index_names()]:
                logger.info("Creating %s search index", self.search_info.index_name)
                await search_index_client.create_index(index)
            else:
                logger.info("Search index %s already exists", self.search_info.index_name)
                index_definition = await search_index_client.get_index(self.search_info.index_name)
                await search_index_client.create_or_update_index(index_definition)

    async def update_content(
        self, sections: List[Section], image_embeddings: Optional[List[List[float]]] = None, url: Optional[str] = None
    ):
        MAX_BATCH_SIZE = 1000
        section_batches = [sections[i : i + MAX_BATCH_SIZE] for i in range(0, len(sections), MAX_BATCH_SIZE)]

        async with self.search_info.create_search_client() as search_client:
            for batch_index, batch in enumerate(section_batches):
                documents = [
                    {
                        "id": f"{section.content.filename_to_id()}-page-{section_index + batch_index * MAX_BATCH_SIZE}",
                        "title": section.title,  # Using 'title' for the title
                        "cover_image_url": section.cover_image_url,  # Adding a placeholder for cover image URL
                        "full_url": section.full_url,  # Adding a placeholder for the full URL
                        "content_category": section.category,  # Using 'content_category' for the section category
                        "category_description": section.category_description,  # Adding a placeholder for category description
                        "pr_name": section.category_description,  # Adding a placeholder for category description
                        "date_modified": section.category_description,  # Adding a placeholder for category description
                        "chunks": section.split_page.text,  # Using 'chunks' for the split page text content
                    }
                    for section_index, section in enumerate(batch)
                ]
                if url:
                    for document in documents:
                        document["storageUrl"] = url
                if self.embeddings:
                    embeddings = await self.embeddings.create_embeddings(
                        texts=[section.split_page.text for section in batch]
                    )
                    for i, document in enumerate(documents):
                        document["embedding"] = embeddings[i]
                if image_embeddings:
                    for i, (document, section) in enumerate(zip(documents, batch)):
                        document["imageEmbedding"] = image_embeddings[section.split_page.page_num]

                await search_client.upload_documents(documents)

    async def remove_content(self, path: Optional[str] = None, only_oid: Optional[str] = None):
        logger.info(
            "Removing sections from '{%s or '<all>'}' from search index '%s'", path, self.search_info.index_name
        )
        async with self.search_info.create_search_client() as search_client:
            while True:
                filter = None
                if path is not None:
                    # Replace ' with '' to escape the single quote for the filter
                    # https://learn.microsoft.com/azure/search/query-odata-filter-orderby-syntax#escaping-special-characters-in-string-constants
                    path_for_filter = os.path.basename(path).replace("'", "''")
                    filter = f"sourcefile eq '{path_for_filter}'"
                max_results = 1000
                result = await search_client.search(
                    search_text="", filter=filter, top=max_results, include_total_count=True
                )
                result_count = await result.get_count()
                if result_count == 0:
                    break
                documents_to_remove = []
                async for document in result:
                    # If only_oid is set, only remove documents that have only this oid
                    if not only_oid or document.get("oids") == [only_oid]:
                        documents_to_remove.append({"id": document["id"]})
                if len(documents_to_remove) == 0:
                    if result_count < max_results:
                        break
                    else:
                        continue
                removed_docs = await search_client.delete_documents(documents_to_remove)
                logger.info("Removed %d sections from index", len(removed_docs))
                # It can take a few seconds for search results to reflect changes, so wait a bit
                await asyncio.sleep(2)
