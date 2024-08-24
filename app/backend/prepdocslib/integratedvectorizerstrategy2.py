import logging
from typing import Optional

from azure.search.documents.indexes._generated.models import (
    NativeBlobSoftDeleteDeletionDetectionPolicy,
)
from azure.search.documents.indexes.models import (
    AzureOpenAIEmbeddingSkill,
    AzureOpenAIParameters,
    AzureOpenAIVectorizer,
    FieldMapping,
    IndexProjectionMode,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    SearchIndexer,
    SearchIndexerDataContainer,
    SearchIndexerDataSourceConnection,
    SearchIndexerIndexProjections,
    SearchIndexerIndexProjectionSelector,
    SearchIndexerIndexProjectionsParameters,
    SearchIndexerSkillset,
    SplitSkill,
)

from .blobmanager import BlobManager
from .embeddings import AzureOpenAIEmbeddingService
from .listfilestrategy import ListFileStrategy
from .searchmanager import SearchManager
from .strategy import DocumentAction, SearchInfo, Strategy

logger = logging.getLogger("ingester")


class IntegratedVectorizerStrategy(Strategy):
    """
    Strategy for ingesting and vectorizing documents into a search service from files stored storage account
    """

    def __init__(
        self,
        list_file_strategy: ListFileStrategy,
        blob_manager: BlobManager,
        search_info: SearchInfo,
        embeddings: Optional[AzureOpenAIEmbeddingService],
        subscription_id: str,
        search_service_user_assigned_id: str,
        document_action: DocumentAction = DocumentAction.Add,
        search_analyzer_name: Optional[str] = None,
        use_acls: bool = False,
        category: Optional[str] = None,
    ):
        if not embeddings or not isinstance(embeddings, AzureOpenAIEmbeddingService):
            raise Exception("Expecting AzureOpenAI embedding service")

        self.list_file_strategy = list_file_strategy
        self.blob_manager = blob_manager
        self.document_action = document_action
        self.embeddings = embeddings
        self.subscription_id = subscription_id
        self.search_user_assigned_identity = search_service_user_assigned_id
        self.search_analyzer_name = search_analyzer_name
        self.use_acls = use_acls
        self.category = category
        self.search_info = search_info

    async def create_embedding_skill(self, index_name: str):
        skillset_name = f"{index_name}-skillset"

        # See: https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.indexes.models.splitskill?view=azure-python
        split_skill = SplitSkill(
            # See: https://learn.microsoft.com/en-us/azure/search/cognitive-search-skill-textsplit#example-for-chunking-and-vectorization
            description="Split skill to chunk documents",
            # See: https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.indexes.models.textsplitmode?view=azure-python
            text_split_mode="pages",  # or sentences
            context="/document/content",  # the path to the field to split
            maximum_page_length=5000,
            page_overlap_length=200,  # number of characters/tokens
            # See: https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.indexes.models.inputfieldmappingentry?view=azure-python
            # InputFieldMapping
            inputs=[InputFieldMappingEntry(name="text", source="/document/content")],
            # See: https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.indexes.models.outputfieldmappingentry?view=azure-python
            # OutputFieldMapping
            outputs=[OutputFieldMappingEntry(name="textItems", target_name="pages")],
        )

        if self.embeddings is None:
            raise ValueError("Expecting Azure Open AI instance")

        embedding_skill = AzureOpenAIEmbeddingSkill(
                description="Skill to generate embeddings via Azure OpenAI",
                context="/document/content/pages/*",
                resource_uri=f"https://{self.embeddings.open_ai_service}.openai.azure.com",
                deployment_id=self.embeddings.open_ai_deployment,
                inputs=[InputFieldMappingEntry(name="text", source="/document/content/pages/*")],
                outputs=[OutputFieldMappingEntry(name="embedding", target_name="vector")],
        )

        index_projections = SearchIndexerIndexProjections(
                selectors=[
                    SearchIndexerIndexProjectionSelector(
                        target_index_name=index_name,
                        parent_key_field_name="parent_id",
                        source_context="/document/content/pages/*",
                        mappings=[
                            # Maps the outputs from the indexer to the fields in the index (this is where the data is populated in the index, you must have a field in the index for it to match, the "name" is the name of the input field in the index)
                            # InputFieldMappingEntry(name="id", source="/document/id"), # the parent_id field in the index which is needed for the indexing process will prevent this field from being mapped
                            InputFieldMappingEntry(name="title", source="/document/title"),
                            InputFieldMappingEntry(name="cover_image_url", source="/document/cover_image_url"),
                            InputFieldMappingEntry(name="full_url", source="/document/full_url"),
                            InputFieldMappingEntry(name="content_category", source="/document/content_category"),
                            InputFieldMappingEntry(name="category_description", source="/document/category_description"),
                            # InputFieldMappingEntry(name="content", source="/document/content"), # only the parent document will have this field, we took it out to prevent content overlap in the search
                            InputFieldMappingEntry(name="chunks", source="/document/content/pages/*"),
                            InputFieldMappingEntry(name="embedding", source="/document/content/pages/*/vector"),
                        ],
                    )
                ],
                parameters=SearchIndexerIndexProjectionsParameters(
                    # Source document will be skipped from writing into the indexer's target index
                    projection_mode=IndexProjectionMode.SKIP_INDEXING_PARENT_DOCUMENTS  # or INCLUDE_INDEXING_PARENT_DOCUMENTS
                ),
            )

        skillset = SearchIndexerSkillset(
            name=skillset_name,
            description="Skillset to chunk documents and generate embeddings",
            skills=[split_skill, embedding_skill],
            index_projections=index_projections,
        )

        return skillset

    async def setup(self):
        search_manager = SearchManager(
            search_info=self.search_info,
            search_analyzer_name=self.search_analyzer_name,
            use_acls=self.use_acls,
            use_int_vectorization=True,
            embeddings=self.embeddings,
            search_images=False,
        )

        if self.embeddings is None:
            raise ValueError("Expecting Azure Open AI instance")

        await search_manager.create_index(
            vectorizers=[
                AzureOpenAIVectorizer(
                    name=f"{self.search_info.index_name}-vectorizer",
                    kind="azureOpenAI",
                    azure_open_ai_parameters=AzureOpenAIParameters(
                        resource_uri=f"https://{self.embeddings.open_ai_service}.openai.azure.com",
                        deployment_id=self.embeddings.open_ai_deployment,
                    ),
                ),
            ]
        )

        # create indexer client
        ds_client = self.search_info.create_search_indexer_client()
        ds_container = SearchIndexerDataContainer(name=self.blob_manager.container)
        data_source_connection = SearchIndexerDataSourceConnection(
            name=f"{self.search_info.index_name}-blob",
            type="azureblob",
            connection_string=self.blob_manager.get_managedidentity_connectionstring(),
            container=ds_container,
            data_deletion_detection_policy=NativeBlobSoftDeleteDeletionDetectionPolicy(),
        )

        await ds_client.create_or_update_data_source_connection(data_source_connection)
        logger.info("Search indexer data source connection updated.")

        embedding_skillset = await self.create_embedding_skill(self.search_info.index_name)
        await ds_client.create_or_update_skillset(embedding_skillset)
        await ds_client.close()

    async def run(self):
        if self.document_action == DocumentAction.Add:
            files = self.list_file_strategy.list()
            async for file in files:
                try:
                    await self.blob_manager.upload_blob(file)
                finally:
                    if file:
                        file.close()
        elif self.document_action == DocumentAction.Remove:
            paths = self.list_file_strategy.list_paths()
            async for path in paths:
                await self.blob_manager.remove_blob(path)
        elif self.document_action == DocumentAction.RemoveAll:
            await self.blob_manager.remove_blob()

        # Create an indexer
        indexer_name = f"{self.search_info.index_name}-indexer"

        indexer = SearchIndexer(
            name=indexer_name,
            description="Indexer to index documents and generate embeddings",
            skillset_name=f"{self.search_info.index_name}-skillset",
            target_index_name=self.search_info.index_name,
            data_source_name=f"{self.search_info.index_name}-blob",
            # Map the metadata_storage_name field to the title field in the index to display the PDF title in the search results
            field_mappings=[FieldMapping(source_field_name="metadata_storage_name", target_field_name="title")],
        )

        indexer_client = self.search_info.create_search_indexer_client()
        indexer_result = await indexer_client.create_or_update_indexer(indexer)

        # Run the indexer
        await indexer_client.run_indexer(indexer_name)
        await indexer_client.close()

        logger.info(
            f"Successfully created index, indexer: {indexer_result.name}, and skillset. Please navigate to search service in Azure Portal to view the status of the indexer."
        )
