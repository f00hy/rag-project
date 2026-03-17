"""Tests for the text chunking service.

Note: the sparse tokenizer treats long repetitive text as short (few unique
tokens), so test fixtures use diverse vocabulary to produce representative
chunk counts.
"""

from app.services.chunking import chunk

DIVERSE_MARKDOWN = """\
# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that focuses on developing
systems capable of learning from data. Unlike traditional programming where explicit
rules are defined, machine learning algorithms identify patterns autonomously through
statistical inference and mathematical optimization.

## Supervised Learning Paradigm

In supervised learning, models are trained using labeled datasets with known outcomes.
The algorithm learns a mapping function from input features to desired outputs through
iterative optimization of a loss function. Common approaches include classification
tasks like spam detection and sentiment analysis, and regression tasks such as
predicting housing prices based on square footage, location, and neighborhood amenities.

## Unsupervised Discovery Methods

Unsupervised methods operate on unlabeled data to discover hidden structures and
natural groupings. Clustering algorithms like k-means and DBSCAN group similar
observations together, while dimensionality reduction techniques like principal
component analysis and t-SNE compress high-dimensional feature spaces without
significant information loss, enabling visualization and downstream processing.

## Neural Networks and Deep Learning Architectures

Deep learning architectures stack multiple layers of interconnected artificial neurons
to extract hierarchical representations from raw data. Convolutional networks excel
at image recognition and spatial pattern detection, while recurrent architectures
including LSTM and GRU handle sequential dependencies. Transformer models dominate
modern natural language processing tasks including machine translation, text
summarization, and question answering through self-attention mechanisms.

## Evaluation Metrics and Model Selection

Model performance is assessed through metrics carefully tailored to the problem
type and business objectives. Classification tasks commonly rely on precision,
recall, and the F1 harmonic mean, along with area under the receiver operating
characteristic curve. Regression problems use root mean squared error and
coefficient of determination. Cross-validation provides robust performance estimates
by partitioning data into training and validation folds across multiple iterations,
reducing the variance of evaluation results.
"""


async def test_chunk_produces_parents_and_children():
    """Diverse text yields non-empty parent and child chunk lists."""
    parents, children = await chunk(DIVERSE_MARKDOWN)
    assert len(parents) > 0
    assert len(children) > 0


async def test_parent_child_relationships_coherent():
    """Every child references a valid parent and parents track their children."""
    parents, children = await chunk(DIVERSE_MARKDOWN)
    parent_ids = {p.id for p in parents}

    for child in children:
        assert child.parent_id in parent_ids

    child_ids = {c.id for c in children}
    for parent in parents:
        for cid in parent.child_ids:
            assert cid in child_ids


async def test_parent_ids_are_sequential():
    """Parent IDs follow the p_0, p_1, ... naming pattern."""
    parents, _ = await chunk(DIVERSE_MARKDOWN)
    for idx, parent in enumerate(parents):
        assert parent.id == f"p_{idx}"


async def test_child_ids_are_sequential():
    """Child IDs follow the c_0, c_1, ... naming pattern."""
    _, children = await chunk(DIVERSE_MARKDOWN)
    for idx, child in enumerate(children):
        assert child.id == f"c_{idx}"


async def test_short_diverse_input_produces_chunks():
    """Even a short paragraph with diverse vocabulary produces chunks."""
    short_text = (
        "Quantum computing leverages superposition and entanglement "
        "to perform certain computations exponentially faster than "
        "classical computers, with promising applications in cryptography, "
        "drug discovery, and molecular simulation of complex chemical systems."
    )
    parents, children = await chunk(short_text)
    assert len(parents) >= 1
    assert len(children) >= 1


async def test_repetitive_input_treated_as_short():
    """Repetitive text produces fewer chunks than diverse text of equal length."""
    repetitive = "data processing pipeline framework. " * 50
    diverse = DIVERSE_MARKDOWN

    rep_parents, _ = await chunk(repetitive)
    div_parents, _ = await chunk(diverse)

    assert len(rep_parents) <= len(div_parents)
