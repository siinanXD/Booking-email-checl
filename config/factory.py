"""Zentrale Verdrahtung: Settings → Services → Workflow."""

from __future__ import annotations

from dataclasses import dataclass

from config.settings import Settings, get_settings
from observability.alerts import AlertService
from observability.langfuse_setup import configure_langfuse_env, tracing_enabled
from observability.mail_cost import MailCostTracker
from repositories.email_repository import EmailRepository
from repositories.embedding_repository import EmbeddingRepository
from repositories.entity_repository import EntityRepository
from repositories.extraction_repository import ExtractionRepository
from repositories.mongo import get_database
from routers.ingestion import IngestionRouter
from routers.review import ReviewRouter
from services.classification import ClassificationService, LLMClient
from services.extraction import ExtractionService
from services.grounding import GroundingService
from services.indexing import EmbeddingClient, EmbeddingFn, IndexingService
from services.ingestion import IngestionService
from services.openai_client import OpenAIClient
from services.response_generation import ResponseGenerationService
from services.retrieval import RetrievalService
from services.similarity_search import SimilaritySearchService
from services.triage import TriageService
from services.validation import ValidationService
from workflows.email_workflow import EmailWorkflow


@dataclass
class AppContext:
    """Alle verdrahteten Komponenten für API/CLI/Tests."""

    settings: Settings
    ingestion_router: IngestionRouter
    review_router: ReviewRouter
    workflow: EmailWorkflow
    email_repo: EmailRepository


def build_app_context(settings: Settings | None = None) -> AppContext:
    """Erzeugt den Anwendungskontext aus Settings."""
    cfg = settings or get_settings()
    db = get_database(cfg)

    email_repo = EmailRepository(db)
    entity_repo = EntityRepository(db)
    extraction_repo = ExtractionRepository(db)
    embedding_repo = EmbeddingRepository(db)

    alerts = AlertService(webhook_url=cfg.webhook_alert_url)
    tracing = configure_langfuse_env(cfg) and tracing_enabled(cfg)

    llm_mode = cfg.llm_mode.strip().lower()
    # Raw mail prompts must not be auto-captured by provider wrappers.
    use_langfuse_openai = False
    llm: LLMClient
    embed_client: EmbeddingFn
    if llm_mode == "mock":
        from services.mock_llm import MockEmbeddingClient, MockLLM

        llm = MockLLM()
        embed_client = MockEmbeddingClient()
    elif llm_mode == "live":
        llm = OpenAIClient(cfg.openai_api_key, use_langfuse=use_langfuse_openai)
        embed_client = EmbeddingClient(
            cfg.openai_api_key,
            cfg.embedding_model,
            use_langfuse=use_langfuse_openai,
            tracing=tracing,
        )
    else:
        msg = f"Unsupported LLM_MODE: {cfg.llm_mode!r} (use live or mock)"
        raise ValueError(msg)
    mail_cost = MailCostTracker(alerts=alerts, tracing=tracing)
    ingestion = IngestionService(email_repo, TriageService())
    classification = ClassificationService(
        llm,
        cfg.openai_model_classify,
        tracing=tracing,
        alerts=alerts,
        mail_cost=mail_cost,
    )
    extraction = ExtractionService(
        llm,
        cfg.openai_model_extract,
        tracing=tracing,
        alerts=alerts,
        mail_cost=mail_cost,
    )
    validation = ValidationService()
    similarity = SimilaritySearchService(embedding_repo, embed_client)
    retrieval = RetrievalService(entity_repo, email_repo, similarity=similarity)
    response_gen = ResponseGenerationService(
        llm,
        cfg.openai_model_draft,
        retrieval,
        GroundingService(),
        tracing=tracing,
        alerts=alerts,
        mail_cost=mail_cost,
    )
    indexing = IndexingService(embedding_repo, embed_client)

    workflow = EmailWorkflow(
        ingestion=ingestion,
        classification=classification,
        extraction=extraction,
        validation=validation,
        retrieval=retrieval,
        response_gen=response_gen,
        email_repo=email_repo,
        extraction_repo=extraction_repo,
        indexing=indexing,
        alerts=alerts,
        mail_cost=mail_cost,
        tracing=tracing,
    )

    return AppContext(
        settings=cfg,
        ingestion_router=IngestionRouter(ingestion),
        review_router=ReviewRouter(workflow),
        workflow=workflow,
        email_repo=email_repo,
    )
