import { useMemo, useState } from "react";
import api from "../services/api";
import "./ChunkVisualization.css";

import {
    Card,
    Statistic,
    Tag,
    Collapse,
    Empty,
    Spin,
    Alert,
} from "antd";

import {
    FileText,
    Layers3,
    BarChart3,
    Hash,
    ChevronRight,
    Sparkles,
} from "lucide-react";

import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Tooltip,
    Legend,
} from "chart.js";

import { Bar } from "react-chartjs-2";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Tooltip,
    Legend
);

interface Chunk {
    chunk_id: number;
    chunk_number: number;
    page_number: number;
    text: string;
}

interface ChunkResponse {
    filename: string;
    document_id: number;
    strategy: string;
    chunk_count: number;
    chunks: Chunk[];
}

interface StrategyResult {
    strategy: string;
    data: ChunkResponse;
}

const strategyColors: Record<string, string> = {
    fixed: "#ff8a65",
    recursive: "#7c83fd",
    token: "#35c2a1",
};

const strategySoftColors: Record<string, string> = {
    fixed: "#fff0eb",
    recursive: "#efefff",
    token: "#e7faf5",
};

function ChunkVisualization() {
    const [filename, setFilename] = useState(
        "PLACEMENT_RESOURCES.pdf"
    );

    const [strategy, setStrategy] = useState(
        "recursive"
    );

    const [data, setData] =
        useState<ChunkResponse | null>(null);

    const [strategyResults, setStrategyResults] =
        useState<StrategyResult[]>([]);

    const [loading, setLoading] = useState(false);

    const [comparisonLoading, setComparisonLoading] =
        useState(false);

    const [error, setError] = useState("");

    const handleCreateChunks = async () => {
        if (!filename.trim()) {
            setError("Please enter a PDF filename.");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const response =
                await api.post<ChunkResponse>(
                    `/documents/${encodeURIComponent(
                        filename
                    )}/chunks?strategy=${encodeURIComponent(
                        strategy
                    )}`
                );

            setData(response.data);
        } catch (err: any) {
            console.error(err);

            setError(
                err.response?.data?.detail ||
                    "Failed to create chunks."
            );
        } finally {
            setLoading(false);
        }
    };

    const runAllStrategies = async () => {
        if (!filename.trim()) {
            setError("Please enter a PDF filename.");
            return;
        }

        setComparisonLoading(true);
        setError("");

        try {
            const strategies = [
                "fixed",
                "recursive",
                "token",
            ];

            const responses =
                await Promise.all(
                    strategies.map(
                        async (currentStrategy) => {
                            const response =
                                await api.post<ChunkResponse>(
                                    `/documents/${encodeURIComponent(
                                        filename
                                    )}/chunks?strategy=${encodeURIComponent(
                                        currentStrategy
                                    )}`
                                );

                            return {
                                strategy: currentStrategy,
                                data: response.data,
                            };
                        }
                    )
                );

            setStrategyResults(responses);

            const selectedResult =
                responses.find(
                    (item) =>
                        item.strategy === strategy
                );

            if (selectedResult) {
                setData(selectedResult.data);
            }
        } catch (err: any) {
            console.error(err);

            setError(
                err.response?.data?.detail ||
                    "Failed to compare chunking strategies."
            );
        } finally {
            setComparisonLoading(false);
        }
    };

    const currentChunks = data?.chunks ?? [];

    const pageCount = useMemo(() => {
        if (!currentChunks.length) {
            return 0;
        }

        return new Set(
            currentChunks.map(
                (chunk) => chunk.page_number
            )
        ).size;
    }, [currentChunks]);

    const averageCharacters = useMemo(() => {
        if (!currentChunks.length) {
            return 0;
        }

        const total = currentChunks.reduce(
            (sum, chunk) =>
                sum + chunk.text.length,
            0
        );

        return Math.round(
            total / currentChunks.length
        );
    }, [currentChunks]);

    const averageWords = useMemo(() => {
        if (!currentChunks.length) {
            return 0;
        }

        const total = currentChunks.reduce(
            (sum, chunk) =>
                sum +
                chunk.text
                    .split(/\s+/)
                    .filter(Boolean).length,
            0
        );

        return Math.round(
            total / currentChunks.length
        );
    }, [currentChunks]);

    const chartData = useMemo(() => {
        return {
            labels: strategyResults.map(
                (result) =>
                    result.strategy.charAt(0).toUpperCase() +
                    result.strategy.slice(1)
            ),
            datasets: [
                {
                    label: "Chunks",
                    data: strategyResults.map(
                        (result) =>
                            result.data.chunk_count
                    ),
                    backgroundColor:
                        strategyResults.map(
                            (result) =>
                                strategyColors[
                                    result.strategy
                                ]
                        ),
                    borderRadius: 10,
                    borderSkipped: false,
                },
            ],
        };
    }, [strategyResults]);

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
        },
        scales: {
            x: {
                grid: {
                    display: false,
                },
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: "#eceaf2",
                },
            },
        },
    };

    const pageGroups = useMemo(() => {
        const groups: Record<number, Chunk[]> =
            {};

        currentChunks.forEach((chunk) => {
            if (!groups[chunk.page_number]) {
                groups[chunk.page_number] = [];
            }

            groups[chunk.page_number].push(chunk);
        });

        return groups;
    }, [currentChunks]);

    return (
        <main className="chunk-page">

            {/* HERO */}

            <section className="chunk-hero">

                <div className="hero-icon">
                    <Layers3 size={24} />
                </div>

                <div>
                    <div className="hero-eyebrow">
                        RAGVIZ / FEATURE 14
                    </div>

                    <h1>
                        Chunk Intelligence
                    </h1>

                    <p>
                        Explore how your document is
                        segmented before embeddings,
                        retrieval, and generation.
                    </p>
                </div>

            </section>

            {/* CONTROLS */}

            <section className="control-card">

                <div className="field">
                    <label>
                        <FileText size={14} />
                        PDF filename
                    </label>

                    <input
                        value={filename}
                        onChange={(e) =>
                            setFilename(
                                e.target.value
                            )
                        }
                        placeholder="example.pdf"
                    />
                </div>

                <div className="field strategy-field">
                    <label>
                        <Layers3 size={14} />
                        Strategy
                    </label>

                    <select
                        value={strategy}
                        onChange={(e) =>
                            setStrategy(
                                e.target.value
                            )
                        }
                    >
                        <option value="fixed">
                            Fixed
                        </option>

                        <option value="recursive">
                            Recursive
                        </option>

                        <option value="token">
                            Token
                        </option>
                    </select>
                </div>

                <button
                    className="primary-action"
                    onClick={handleCreateChunks}
                    disabled={loading}
                >
                    {loading ? (
                        <>
                            <Spin size="small" />
                            Creating...
                        </>
                    ) : (
                        <>
                            <Sparkles size={17} />
                            Create Chunks
                        </>
                    )}
                </button>

                <button
                    className="secondary-action"
                    onClick={runAllStrategies}
                    disabled={
                        comparisonLoading
                    }
                >
                    {comparisonLoading ? (
                        <>
                            <Spin size="small" />
                            Comparing...
                        </>
                    ) : (
                        <>
                            <BarChart3 size={17} />
                            Compare Strategies
                        </>
                    )}
                </button>

            </section>

            {error && (
                <section className="message-wrapper">
                    <Alert
                        message={error}
                        type="error"
                        showIcon
                    />
                </section>
            )}

            {/* CURRENT RESULT */}

            {data && (
                <>
                    <section className="document-heading">

                        <div>
                            <div className="section-kicker">
                                CURRENT DOCUMENT
                            </div>

                            <h2>
                                {data.filename}
                            </h2>

                            <p>
                                Strategy:
                                <strong>
                                    {" "}
                                    {data.strategy}
                                </strong>
                            </p>
                        </div>

                        <Tag
                            color={
                                data.strategy ===
                                "fixed"
                                    ? "volcano"
                                    : data.strategy ===
                                        "recursive"
                                    ? "geekblue"
                                    : "cyan"
                            }
                        >
                            {data.strategy.toUpperCase()}
                        </Tag>

                    </section>

                    {/* STATISTICS */}

                    <section className="stats-grid">

                        <Card className="stat-card stat-orange">
                            <Statistic
                                title="Total chunks"
                                value={
                                    data.chunk_count
                                }
                                prefix={
                                    <Hash
                                        size={18}
                                    />
                                }
                            />
                        </Card>

                        <Card className="stat-card stat-violet">
                            <Statistic
                                title="Pages covered"
                                value={pageCount}
                                prefix={
                                    <FileText
                                        size={18}
                                    />
                                }
                            />
                        </Card>

                        <Card className="stat-card stat-teal">
                            <Statistic
                                title="Avg. characters"
                                value={
                                    averageCharacters
                                }
                            />
                        </Card>

                        <Card className="stat-card stat-pink">
                            <Statistic
                                title="Avg. words"
                                value={
                                    averageWords
                                }
                            />
                        </Card>

                    </section>

                    {/* STRATEGY COMPARISON */}

                    {strategyResults.length > 0 && (
                        <section className="visual-section">

                            <div className="section-title">
                                <div>
                                    <div className="section-kicker">
                                        STRATEGY COMPARISON
                                    </div>

                                    <h2>
                                        How each strategy
                                        changes the document
                                    </h2>
                                </div>
                            </div>

                            <div className="visual-grid">

                                <Card className="chart-card">

                                    <div className="chart-heading">
                                        <div>
                                            <strong>
                                                Chunks produced
                                            </strong>

                                            <span>
                                                Same document,
                                                different
                                                segmentation
                                            </span>
                                        </div>
                                    </div>

                                    <div className="chart-wrapper">
                                        <Bar
                                            data={
                                                chartData
                                            }
                                            options={
                                                chartOptions
                                            }
                                        />
                                    </div>

                                </Card>

                                <Card className="strategy-cards">

                                    <div className="chart-heading">
                                        <div>
                                            <strong>
                                                Strategy
                                                breakdown
                                            </strong>

                                            <span>
                                                Structural
                                                differences
                                            </span>
                                        </div>
                                    </div>

                                    <div className="strategy-list">

                                        {strategyResults.map(
                                            (result) => (
                                                <div
                                                    className="strategy-row"
                                                    key={
                                                        result.strategy
                                                    }
                                                >

                                                    <div
                                                        className="strategy-dot"
                                                        style={{
                                                            background:
                                                                strategyColors[
                                                                    result
                                                                        .strategy
                                                                ],
                                                        }}
                                                    />

                                                    <div className="strategy-name">
                                                        <strong>
                                                            {result
                                                                .strategy
                                                                .charAt(
                                                                    0
                                                                )
                                                                .toUpperCase() +
                                                                result
                                                                    .strategy
                                                                    .slice(
                                                                        1
                                                                    )}
                                                        </strong>

                                                        <span>
                                                            {
                                                                result
                                                                    .data
                                                                    .chunk_count
                                                            }{" "}
                                                            chunks
                                                        </span>
                                                    </div>

                                                    <Tag
                                                        style={{
                                                            background:
                                                                strategySoftColors[
                                                                    result
                                                                        .strategy
                                                                ],
                                                            border:
                                                                "none",
                                                            color:
                                                                strategyColors[
                                                                    result
                                                                        .strategy
                                                                ],
                                                        }}
                                                    >
                                                        {
                                                            result
                                                                .data
                                                                .chunk_count
                                                        }
                                                    </Tag>

                                                </div>
                                            )
                                        )}

                                    </div>

                                </Card>

                            </div>

                        </section>
                    )}

                    {/* DOCUMENT MAP */}

                    <section className="visual-section">

                        <div className="section-title">

                            <div>
                                <div className="section-kicker">
                                    DOCUMENT MAP
                                </div>

                                <h2>
                                    Chunk distribution
                                    across pages
                                </h2>
                            </div>

                            <Tag
                                icon={
                                    <Layers3
                                        size={13}
                                    />
                                }
                            >
                                {currentChunks.length} chunks
                            </Tag>

                        </div>

                        <Card className="map-card">

                            {Object.keys(
                                pageGroups
                            ).length === 0 ? (
                                <Empty description="No chunks available" />
                            ) : (
                                <div className="page-map">

                                    {Object.entries(
                                        pageGroups
                                    ).map(
                                        (
                                            [
                                                page,
                                                chunks,
                                            ]
                                        ) => (
                                            <div
                                                className="page-row"
                                                key={
                                                    page
                                                }
                                            >

                                                <div className="page-label">
                                                    <span>
                                                        PAGE
                                                    </span>

                                                    <strong>
                                                        {page}
                                                    </strong>
                                                </div>

                                                <div className="page-chunks">

                                                    {chunks.map(
                                                        (
                                                            chunk
                                                        ) => (
                                                            <div
                                                                className="map-chunk"
                                                                key={
                                                                    chunk.chunk_id
                                                                }
                                                                style={{
                                                                    background:
                                                                        strategySoftColors[
                                                                            data.strategy
                                                                        ],
                                                                    borderColor:
                                                                        strategyColors[
                                                                            data.strategy
                                                                        ],
                                                                }}
                                                                title={`Chunk ${
                                                                    chunk.chunk_number +
                                                                    1
                                                                }`}
                                                            >
                                                                C
                                                                {chunk.chunk_number +
                                                                    1}
                                                            </div>
                                                        )
                                                    )}

                                                </div>

                                            </div>
                                        )
                                    )}

                                </div>
                            )}

                        </Card>

                    </section>

                    {/* CHUNK EXPLORER */}

                    <section className="visual-section">

                        <div className="section-title">

                            <div>
                                <div className="section-kicker">
                                    CHUNK EXPLORER
                                </div>

                                <h2>
                                    Inspect the generated
                                    chunks
                                </h2>
                            </div>

                            <span className="muted-label">
                                Click a chunk to expand
                            </span>

                        </div>

                        <Card className="explorer-card">

                            <Collapse
                                accordion
                                bordered={false}
                                items={currentChunks.map(
                                    (chunk) => ({
                                        key: chunk.chunk_id,
                                        label: (
                                            <div className="chunk-collapse-title">

                                                <div className="chunk-index">
                                                    <span>
                                                        CHUNK
                                                    </span>

                                                    <strong>
                                                        {String(
                                                            chunk.chunk_number +
                                                                1
                                                        ).padStart(
                                                            2,
                                                            "0"
                                                        )}
                                                    </strong>
                                                </div>

                                                <div className="chunk-summary">
                                                    <Tag>
                                                        Page{" "}
                                                        {
                                                            chunk.page_number
                                                        }
                                                    </Tag>

                                                    <span>
                                                        {
                                                            chunk.text
                                                                .length
                                                        }{" "}
                                                        characters
                                                    </span>

                                                    <span>
                                                        {
                                                            chunk.text
                                                                .split(
                                                                    /\s+/
                                                                )
                                                                .filter(
                                                                    Boolean
                                                                ).length
                                                        }{" "}
                                                        words
                                                    </span>
                                                </div>

                                                <ChevronRight
                                                    size={
                                                        17
                                                    }
                                                    className="collapse-chevron"
                                                />

                                            </div>
                                        ),
                                        children: (
                                            <div className="chunk-content">

                                                <div className="chunk-content-meta">

                                                    <span>
                                                        ID #
                                                        {
                                                            chunk.chunk_id
                                                        }
                                                    </span>

                                                    <span>
                                                        Page{" "}
                                                        {
                                                            chunk.page_number
                                                        }
                                                    </span>

                                                    <span>
                                                        {
                                                            chunk.text
                                                                .length
                                                        }{" "}
                                                        characters
                                                    </span>

                                                </div>

                                                <p>
                                                    {
                                                        chunk.text
                                                    }
                                                </p>

                                            </div>
                                        ),
                                    })
                                )}
                            />

                        </Card>

                    </section>
                </>
            )}

        </main>
    );
}

export default ChunkVisualization;