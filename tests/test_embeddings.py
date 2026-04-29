"""
Tests for the KB embedding model abstraction.

Tests cover:
    - Model initialization (minilm)
    - Single text embedding dimensions
    - Batch embedding (multiple texts)
    - Query embedding
    - Semantic similarity (related > unrelated Arabic texts)
    - Embedding normalization (L2 norm ≈ 1.0)
"""

import math

import numpy as np
import pytest

from al_furqan.kb.embeddings import EmbeddingModel

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="module")
def model() -> EmbeddingModel:
    """Load model once for all tests in this module."""
    return EmbeddingModel("minilm")


class TestModelInitialization:
    """Test embedding model loading and configuration."""

    def test_minilm_loads(self, model: EmbeddingModel) -> None:
        """Test minilm_loads."""
        assert model is not None
        assert model.model_name == "minilm"

    def test_dimension_positive(self, model: EmbeddingModel) -> None:
        """Test dimension_positive."""
        assert model.dimension > 0

    def test_minilm_dimension_is_384(self, model: EmbeddingModel) -> None:
        """Test minilm_dimension_is_384."""
        # MiniLM-L12-v2 produces 384-dim embeddings
        assert model.dimension == 384

    def test_available_models_registry(self) -> None:
        """Test available_models_registry."""
        assert "minilm" in EmbeddingModel.AVAILABLE_MODELS
        assert "camelbert" in EmbeddingModel.AVAILABLE_MODELS

    def test_model_path_resolved(self, model: EmbeddingModel) -> None:
        """Test model_path_resolved."""
        assert model.model_path == EmbeddingModel.AVAILABLE_MODELS["minilm"]


class TestSingleEmbedding:
    """Test embedding a single query."""

    def test_embed_query_returns_list(self, model: EmbeddingModel) -> None:
        """Test embed_query_returns_list."""
        result = model.embed_query("بسم الله الرحمن الرحيم")
        assert isinstance(result, list)

    def test_embed_query_correct_dimension(self, model: EmbeddingModel) -> None:
        """Test embed_query_correct_dimension."""
        result = model.embed_query("بسم الله الرحمن الرحيم")
        assert len(result) == model.dimension

    def test_embed_query_float_values(self, model: EmbeddingModel) -> None:
        """Test embed_query_float_values."""
        result = model.embed_query("test text")
        assert all(isinstance(v, float) for v in result)


class TestBatchEmbedding:
    """Test embedding multiple texts at once."""

    def test_batch_returns_correct_count(self, model: EmbeddingModel) -> None:
        """Test batch_returns_correct_count."""
        texts = ["الحمد لله", "سبحان الله", "لا إله إلا الله"]
        results = model.embed(texts)
        assert len(results) == 3

    def test_batch_correct_dimensions(self, model: EmbeddingModel) -> None:
        """Test batch_correct_dimensions."""
        texts = ["text one", "text two", "text three", "text four"]
        results = model.embed(texts)
        for emb in results:
            assert len(emb) == model.dimension

    def test_empty_list_returns_empty(self, model: EmbeddingModel) -> None:
        """Test empty_list_returns_empty."""
        results = model.embed([])
        assert results == []

    def test_single_item_batch(self, model: EmbeddingModel) -> None:
        """Test single_item_batch."""
        results = model.embed(["single text"])
        assert len(results) == 1
        assert len(results[0]) == model.dimension


class TestNormalization:
    """Test that embeddings are L2-normalized (unit vectors)."""

    def test_single_embedding_normalized(self, model: EmbeddingModel) -> None:
        """Test single_embedding_normalized."""
        vec = np.array(model.embed_query("بسم الله الرحمن الرحيم"))
        norm = np.linalg.norm(vec)
        assert math.isclose(norm, 1.0, abs_tol=1e-4), f"L2 norm = {norm}, expected ≈ 1.0"

    def test_batch_embeddings_normalized(self, model: EmbeddingModel) -> None:
        """Test batch_embeddings_normalized."""
        texts = [
            "قل هو الله أحد",
            "الله الصمد",
            "لم يلد ولم يولد",
        ]
        vecs = np.array(model.embed(texts))
        norms = np.linalg.norm(vecs, axis=1)
        for i, norm in enumerate(norms):
            assert math.isclose(norm, 1.0, abs_tol=1e-4), (
                f"Embedding {i} L2 norm = {norm}, expected ≈ 1.0"
            )


class TestSemanticSimilarity:
    """Test that semantically related texts have higher similarity."""

    def test_related_arabic_texts_more_similar(self, model: EmbeddingModel) -> None:
        """Test related_arabic_texts_more_similar."""
        # Related: both about prayer (salah)
        text_a = "الصلاة عماد الدين وركن من أركان الإسلام"
        text_b = "أقيموا الصلاة وآتوا الزكاة واركعوا مع الراكعين"
        # Unrelated: about food/cooking
        text_c = "الطبخ فن من الفنون الجميلة في المطبخ العربي"

        sim_related = model.similarity(text_a, text_b)
        sim_unrelated = model.similarity(text_a, text_c)

        assert sim_related > sim_unrelated, (
            f"Related similarity ({sim_related:.4f}) should be > "
            f"unrelated similarity ({sim_unrelated:.4f})"
        )

    def test_identical_texts_high_similarity(self, model: EmbeddingModel) -> None:
        """Test identical_texts_high_similarity."""
        text = "إن الله مع الصابرين"
        sim = model.similarity(text, text)
        assert sim > 0.99, f"Self-similarity = {sim:.4f}, expected > 0.99"

    def test_quran_hadith_topic_similarity(self, model: EmbeddingModel) -> None:
        """Test quran_hadith_topic_similarity."""
        # Both about riba (usury/interest)
        quran_riba = "الذين يأكلون الربا لا يقومون إلا كما يقوم الذي يتخبطه الشيطان من المس"
        hadith_riba = "لعن رسول الله صلى الله عليه وسلم آكل الربا ومؤكله وكاتبه وشاهديه"
        # Unrelated: about travel
        unrelated = "السفر قطعة من العذاب يمنع أحدكم طعامه وشرابه ونومه"

        sim_riba = model.similarity(quran_riba, hadith_riba)
        sim_unrel = model.similarity(quran_riba, unrelated)

        assert sim_riba > sim_unrel, (
            f"Topic similarity ({sim_riba:.4f}) should be > "
            f"unrelated similarity ({sim_unrel:.4f})"
        )
