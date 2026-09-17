import { useState } from "react";
import {
    BarChart3,
    ChevronDown,
    FlaskConical,
    Play,
    RotateCcw,
    Settings2,
} from "lucide-react";

import "./Experiment.css";

type ChunkingStrategy =
    | "fixed"
    | "recursive"
    | "sentence"
    | "token";

type EmbeddingModel =
    | "minilm"
    | "mpnet"
    | "distilroberta";

type RetrievalMethod =
    | "vector"
    | "bm25"
    | "hybrid"
    | "hybrid_reranker"
    | "rrf";

type ExperimentConfig = {
    chunking: {
        strategy: ChunkingStrategy;
        chunkSize: number;
        overlap: number;
    };

    embedding: {
        model: EmbeddingModel;
    };

    retrieval: {
        method: RetrievalMethod;
        topK: number;
        similarity: string;
        threshold: number;
    };

    generation: {
        llm: string;
        temperature: number;
        maxTokens: number;
        topP: number;
    };
};

const defaultConfig: ExperimentConfig = {
    chunking: {
        strategy: "recursive",
        chunkSize: 500,
        overlap: 50,
    },

    embedding: {
        model: "minilm",
    },

    retrieval: {
        method: "vector",
        topK: 5,
        similarity: "cosine",
        threshold: 0.0,
    },

    generation: {
        llm: "openai/gpt-oss-20b",
        temperature: 0.2,
        maxTokens: 500,
        topP: 0.9,
    },
};

function createDefaultConfig(): ExperimentConfig {
    return {
        chunking: {
            ...defaultConfig.chunking,
        },

        embedding: {
            ...defaultConfig.embedding,
        },

        retrieval: {
            ...defaultConfig.retrieval,
        },

        generation: {
            ...defaultConfig.generation,
        },
    };
}

function Experiment() {
    const [configA, setConfigA] = useState<ExperimentConfig>(
        createDefaultConfig()
    );

    const [configB, setConfigB] = useState<ExperimentConfig>({
        ...createDefaultConfig(),

        chunking: {
            strategy: "fixed",
            chunkSize: 500,
            overlap: 50,
        },
    });

    const [evaluationSet, setEvaluationSet] =
        useState("default");

    const [isRunning, setIsRunning] = useState(false);

    const [hasRun, setHasRun] = useState(false);

    const updateConfig = (
        side: "A" | "B",
        updates: Partial<ExperimentConfig>
    ) => {
        if (side === "A") {
            setConfigA((current) => ({
                ...current,
                ...updates,
            }));
        } else {
            setConfigB((current) => ({
                ...current,
                ...updates,
            }));
        }
    };

    const updateChunking = (
        side: "A" | "B",
        field: keyof ExperimentConfig["chunking"],
        value: string | number
    ) => {
        const config = side === "A" ? configA : configB;

        const nextChunking = {
            ...config.chunking,
            [field]: value,
        };

        updateConfig(side, {
            chunking: nextChunking,
        });
    };

    const updateEmbedding = (
        side: "A" | "B",
        model: EmbeddingModel
    ) => {
        const config = side === "A" ? configA : configB;

        updateConfig(side, {
            embedding: {
                ...config.embedding,
                model,
            },
        });
    };

    const updateRetrieval = (
        side: "A" | "B",
        field: keyof ExperimentConfig["retrieval"],
        value: string | number
    ) => {
        const config = side === "A" ? configA : configB;

        updateConfig(side, {
            retrieval: {
                ...config.retrieval,
                [field]: value,
            },
        });
    };

    const updateGeneration = (
        side: "A" | "B",
        field: keyof ExperimentConfig["generation"],
        value: string | number
    ) => {
        const config = side === "A" ? configA : configB;

        updateConfig(side, {
            generation: {
                ...config.generation,
                [field]: value,
            },
        });
    };

    const resetConfiguration = (side: "A" | "B") => {
        const freshConfig = createDefaultConfig();

        if (side === "A") {
            setConfigA(freshConfig);
        } else {
            setConfigB({
                ...freshConfig,

                chunking: {
                    strategy: "fixed",
                    chunkSize: 500,
                    overlap: 50,
                },
            });
        }
    };

    const runExperiment = async () => {
        setIsRunning(true);
        setHasRun(false);

        /*
         * Backend integration will be added in the next step.
         *
         * These are the exact objects that will eventually
         * be sent to the experiment API.
         */

        const experimentPayload = {
            evaluationSet,
            configA,
            configB,
        };

        console.log(
            "Experiment configuration:",
            experimentPayload
        );

        await new Promise((resolve) =>
            setTimeout(resolve, 800)
        );

        setIsRunning(false);
        setHasRun(true);
    };

    const renderConfiguration = (
        side: "A" | "B",
        config: ExperimentConfig
    ) => {
        return (
            <section className="experiment-config-card">

                <div className="config-card-header">

                    <div>
                        <div className="config-label">
                            CONFIGURATION {side}
                        </div>

                        <h2>
                            {side === "A"
                                ? "Baseline"
                                : "Alternative"}
                        </h2>
                    </div>

                    <button
                        className="reset-button"
                        onClick={() =>
                            resetConfiguration(side)
                        }
                        type="button"
                        title={`Reset configuration ${side}`}
                    >
                        <RotateCcw size={15} />
                    </button>

                </div>

                {/* CHUNKING */}

                <div className="config-section">

                    <div className="section-heading">
                        <Settings2 size={16} />
                        <span>Chunking</span>
                    </div>

                    <label className="field-label">
                        Strategy
                    </label>

                    <div className="select-wrapper">
                        <select
                            value={config.chunking.strategy}
                            onChange={(event) =>
                                updateChunking(
                                    side,
                                    "strategy",
                                    event.target.value as ChunkingStrategy
                                )
                            }
                        >
                            <option value="fixed">
                                Fixed
                            </option>

                            <option value="recursive">
                                Recursive
                            </option>

                            <option value="sentence">
                                Sentence
                            </option>

                            <option value="token">
                                Token
                            </option>
                        </select>

                        <ChevronDown size={15} />
                    </div>

                    <div className="two-column-fields">

                        <div>
                            <label className="field-label">
                                Chunk size
                            </label>

                            <input
                                type="number"
                                min="1"
                                value={config.chunking.chunkSize}
                                onChange={(event) =>
                                    updateChunking(
                                        side,
                                        "chunkSize",
                                        Number(event.target.value)
                                    )
                                }
                            />
                        </div>

                        <div>
                            <label className="field-label">
                                Overlap
                            </label>

                            <input
                                type="number"
                                min="0"
                                value={config.chunking.overlap}
                                onChange={(event) =>
                                    updateChunking(
                                        side,
                                        "overlap",
                                        Number(event.target.value)
                                    )
                                }
                            />
                        </div>

                    </div>

                </div>

                {/* EMBEDDING */}

                <div className="config-section">

                    <div className="section-heading">
                        <BarChart3 size={16} />
                        <span>Embedding</span>
                    </div>

                    <label className="field-label">
                        Model
                    </label>

                    <div className="select-wrapper">
                        <select
                            value={config.embedding.model}
                            onChange={(event) =>
                                updateEmbedding(
                                    side,
                                    event.target.value as EmbeddingModel
                                )
                            }
                        >
                            <option value="minilm">
                                all-MiniLM-L6-v2 · 384d
                            </option>

                            <option value="mpnet">
                                all-mpnet-base-v2 · 768d
                            </option>

                            <option value="distilroberta">
                                all-distilroberta-v1 · 768d
                            </option>
                        </select>

                        <ChevronDown size={15} />
                    </div>

                </div>

                {/* RETRIEVAL */}

                <div className="config-section">

                    <div className="section-heading">
                        <FlaskConical size={16} />
                        <span>Retrieval</span>
                    </div>

                    <label className="field-label">
                        Method
                    </label>

                    <div className="select-wrapper">
                        <select
                            value={config.retrieval.method}
                            onChange={(event) =>
                                updateRetrieval(
                                    side,
                                    "method",
                                    event.target.value as RetrievalMethod
                                )
                            }
                        >
                            <option value="vector">
                                Vector
                            </option>

                            <option value="bm25">
                                BM25
                            </option>

                            <option value="hybrid">
                                Hybrid
                            </option>

                            <option value="hybrid_reranker">
                                Hybrid + Reranker
                            </option>

                            <option value="rrf">
                                RRF
                            </option>
                        </select>

                        <ChevronDown size={15} />
                    </div>

                    <div className="two-column-fields">

                        <div>
                            <label className="field-label">
                                Top-K
                            </label>

                            <input
                                type="number"
                                min="1"
                                value={config.retrieval.topK}
                                onChange={(event) =>
                                    updateRetrieval(
                                        side,
                                        "topK",
                                        Number(event.target.value)
                                    )
                                }
                            />
                        </div>

                        <div>
                            <label className="field-label">
                                Similarity
                            </label>

                            <div className="select-wrapper">
                                <select
                                    value={config.retrieval.similarity}
                                    onChange={(event) =>
                                        updateRetrieval(
                                            side,
                                            "similarity",
                                            event.target.value
                                        )
                                    }
                                >
                                    <option value="cosine">
                                        Cosine
                                    </option>

                                    <option value="l2">
                                        L2
                                    </option>

                                    <option value="dot">
                                        Dot product
                                    </option>
                                </select>

                                <ChevronDown size={15} />
                            </div>
                        </div>

                    </div>

                    <label className="field-label">
                        Similarity threshold
                    </label>

                    <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.01"
                        value={config.retrieval.threshold}
                        onChange={(event) =>
                            updateRetrieval(
                                side,
                                "threshold",
                                Number(event.target.value)
                            )
                        }
                    />

                </div>

                {/* GENERATION */}

                <div className="config-section">

                    <div className="section-heading">
                        <Settings2 size={16} />
                        <span>Generation</span>
                    </div>

                    <label className="field-label">
                        LLM
                    </label>

                    <div className="select-wrapper">
                        <select
                            value={config.generation.llm}
                            onChange={(event) =>
                                updateGeneration(
                                    side,
                                    "llm",
                                    event.target.value
                                )
                            }
                        >
                            <option value="openai/gpt-oss-20b">
                                openai/gpt-oss-20b
                            </option>

                            <option value="llama-3.1-8b">
                                Llama 3.1 8B
                            </option>

                            <option value="llama-3.3-70b">
                                Llama 3.3 70B
                            </option>
                        </select>

                        <ChevronDown size={15} />
                    </div>

                    <div className="two-column-fields">

                        <div>
                            <label className="field-label">
                                Temperature
                            </label>

                            <input
                                type="number"
                                min="0"
                                max="2"
                                step="0.1"
                                value={
                                    config.generation.temperature
                                }
                                onChange={(event) =>
                                    updateGeneration(
                                        side,
                                        "temperature",
                                        Number(event.target.value)
                                    )
                                }
                            />
                        </div>

                        <div>
                            <label className="field-label">
                                Top-P
                            </label>

                            <input
                                type="number"
                                min="0"
                                max="1"
                                step="0.05"
                                value={config.generation.topP}
                                onChange={(event) =>
                                    updateGeneration(
                                        side,
                                        "topP",
                                        Number(event.target.value)
                                    )
                                }
                            />
                        </div>

                    </div>

                    <label className="field-label">
                        Max tokens
                    </label>

                    <input
                        type="number"
                        min="1"
                        value={config.generation.maxTokens}
                        onChange={(event) =>
                            updateGeneration(
                                side,
                                "maxTokens",
                                Number(event.target.value)
                            )
                        }
                    />

                </div>

            </section>
        );
    };

    return (
        <main className="experiment-page">

            {/* HEADER */}

            <section className="experiment-hero">

                <div className="experiment-title-row">

                    <div className="experiment-title-icon">
                        <FlaskConical size={22} />
                    </div>

                    <div>
                        <div className="experiment-eyebrow">
                            EXPERIMENTATION
                        </div>

                        <h1>
                            Compare RAG configurations.
                        </h1>
                    </div>

                </div>

                <p>
                    Change the pipeline parameters on both sides
                    and evaluate them against the same dataset.
                </p>

            </section>

            {/* EVALUATION DATASET */}

            <section className="evaluation-bar">

                <div className="evaluation-info">

                    <span className="evaluation-label">
                        EVALUATION DATASET
                    </span>

                    <strong>
                        Same dataset for A and B
                    </strong>

                </div>

                <div className="select-wrapper evaluation-select">

                    <select
                        value={evaluationSet}
                        onChange={(event) =>
                            setEvaluationSet(
                                event.target.value
                            )
                        }
                    >
                        <option value="default">
                            Default evaluation set
                        </option>

                        <option value="rag-basics">
                            RAG Basics
                        </option>

                        <option value="retrieval-quality">
                            Retrieval Quality
                        </option>

                        <option value="custom">
                            Custom evaluation set
                        </option>
                    </select>

                    <ChevronDown size={15} />

                </div>

            </section>

            {/* A / B CONFIGURATION */}

            <section className="configuration-grid">

                {renderConfiguration(
                    "A",
                    configA
                )}

                {renderConfiguration(
                    "B",
                    configB
                )}

            </section>

            {/* RUN */}

            <section className="run-section">

                <button
                    className="run-experiment-button"
                    type="button"
                    onClick={runExperiment}
                    disabled={isRunning}
                >
                    <Play size={17} fill="currentColor" />

                    {isRunning
                        ? "Running experiment..."
                        : "Run experiment"}
                </button>

                <p>
                    Both configurations will run against the
                    same evaluation questions.
                </p>

            </section>

            {/* RESULTS PLACEHOLDER */}

            {hasRun && (
                <section className="results-preview">

                    <div className="results-preview-header">

                        <div>
                            <span className="evaluation-label">
                                EXPERIMENT COMPLETE
                            </span>

                            <h2>
                                Results will appear here
                            </h2>
                        </div>

                        <BarChart3 size={22} />

                    </div>

                    <div className="metric-preview-grid">

                        <div className="metric-preview-card">
                            <span>
                                Recall@5
                            </span>

                            <strong>
                                —
                            </strong>
                        </div>

                        <div className="metric-preview-card">
                            <span>
                                MRR
                            </span>

                            <strong>
                                —
                            </strong>
                        </div>

                        <div className="metric-preview-card">
                            <span>
                                Faithfulness
                            </span>

                            <strong>
                                —
                            </strong>
                        </div>

                        <div className="metric-preview-card">
                            <span>
                                Avg latency
                            </span>

                            <strong>
                                —
                            </strong>
                        </div>

                        <div className="metric-preview-card">
                            <span>
                                Tokens
                            </span>

                            <strong>
                                —
                            </strong>
                        </div>

                    </div>

                </section>
            )}

        </main>
    );
}

export default Experiment;