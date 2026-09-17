import {
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";

import Plotly from "plotly.js-dist-min";

import api from "../services/api";

import {
    ArrowDown,
    Check,
    CircleDot,
    FileText,
    Layers3,
    MessageCircle,
    Search,
    Sparkles,
    UploadCloud,
} from "lucide-react";

import {
    Alert,
    Card,
    Collapse,
    Select,
    Spin,
    Tag,
} from "antd";

import "./Visualization.css";

interface PageData {
    page: number;
    text: string;
    character_count?: number;
    word_count?: number;
    has_text?: boolean;
}

interface ExtractionResponse {
    filename: string;
    page_count: number;
    total_characters: number;
    total_words: number;
    pages: PageData[];
}

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

interface VisualizationPoint {
    type?: "chunk" | "query";
    chunk_number?: number;
    page_number?: number;
    x?: number;
    y?: number;
    z?: number;
    text?: string;
    distance?: number;
    retrieved?: boolean;
}

interface VisualizationResponse {
    document_id: number;
    filename?: string;
    model_name: string;
    method: string;
    dimensions: number;
    points?: VisualizationPoint[];
    embeddings?: VisualizationPoint[];
    query?: VisualizationPoint;
    retrieved_chunks?: VisualizationPoint[];
}

interface RetrievalResult {
    chunk_index?: number;
    chunk_number?: number;
    page_number?: number;
    distance?: number;
    score?: number;
    text?: string;
}

interface Source {
    chunk_index?: number;
    chunk_number?: number;
    page_number?: number;
    distance?: number;
    text: string;
}

interface AskResponse {
    question: string;
    document_id: number;
    answer: string;
    sources: Source[];
    metrics?: {
        retrieval_latency_ms?: number;
        context_latency_ms?: number;
        llm_latency_ms?: number;
        total_latency_ms?: number;
        chunks_retrieved?: number;
    };
    retrieval_metrics?: {
        top_k?: number;
        retrieved_chunks?: number;
        best_distance?: number | null;
        average_distance?: number | null;
    };
}

type Stage =
    | "document"
    | "extraction"
    | "chunking"
    | "embedding"
    | "query"
    | "retrieval"
    | "answer";

const stages: {
    id: Stage;
    label: string;
}[] = [
    {
        id: "document",
        label: "Document",
    },
    {
        id: "extraction",
        label: "Extraction",
    },
    {
        id: "chunking",
        label: "Chunking",
    },
    {
        id: "embedding",
        label: "Embeddings",
    },
    {
        id: "query",
        label: "Query",
    },
    {
        id: "retrieval",
        label: "Retrieval",
    },
    {
        id: "answer",
        label: "Answer",
    },
];

const strategyColors: Record<
    string,
    string
> = {
    fixed: "#f28b63",
    recursive: "#7b68ee",
    token: "#32b89a",
};

function normalizeText(text: string) {
    return text
        .replace(/\s+/g, " ")
        .trim()
        .toLowerCase();
}

function Visualization() {
    const [filename, setFilename] = useState(
        "PLACEMENT_RESOURCES.pdf"
    );

    const [stage, setStage] =
        useState<Stage>("document");

    const [extraction, setExtraction] =
        useState<ExtractionResponse | null>(null);

    const [chunkData, setChunkData] =
        useState<ChunkResponse | null>(null);

    const [selectedStrategy, setSelectedStrategy] =
        useState("recursive");

    const [embeddingModel, setEmbeddingModel] =
        useState("minilm");

    const [visualization, setVisualization] =
        useState<VisualizationResponse | null>(
            null
        );

    const [query, setQuery] = useState("");

    const [retrievalResults, setRetrievalResults] =
        useState<RetrievalResult[]>([]);

    const [answerData, setAnswerData] =
        useState<AskResponse | null>(null);

    const [loadingStage, setLoadingStage] =
        useState<Stage | null>(null);

    const [error, setError] = useState("");

    const plotRef =
        useRef<HTMLDivElement | null>(null);

    const currentStageIndex =
        stages.findIndex(
            (item) => item.id === stage
        );

    /*
     * EXTRACTION
     */

    const runExtraction = async () => {
        if (!filename.trim()) {
            setError("Enter a PDF filename.");
            return;
        }

        setLoadingStage("extraction");
        setError("");

        try {
            const response =
                await api.post<ExtractionResponse>(
                    `/documents/${encodeURIComponent(
                        filename
                    )}/extract`
                );

            setExtraction(response.data);
            setStage("extraction");
        } catch (err: any) {
            setError(
                err.response?.data?.detail ||
                    "Could not extract the PDF."
            );
        } finally {
            setLoadingStage(null);
        }
    };

    /*
     * CHUNKING
     */

    const runChunking = async () => {
        if (!filename.trim()) {
            setError("Enter a PDF filename.");
            return;
        }

        setLoadingStage("chunking");
        setError("");

        try {
            const response =
                await api.post<ChunkResponse>(
                    `/documents/${encodeURIComponent(
                        filename
                    )}/chunks`,
                    null,
                    {
                        params: {
                            strategy:
                                selectedStrategy,
                        },
                    }
                );

            setChunkData(response.data);

            setVisualization(null);
            setRetrievalResults([]);
            setAnswerData(null);

            setStage("chunking");
        } catch (err: any) {
            setError(
                err.response?.data?.detail ||
                    "Could not create chunks."
            );
        } finally {
            setLoadingStage(null);
        }
    };

    /*
     * EMBEDDINGS
     */

    const runEmbeddings = async () => {
        if (!chunkData) {
            setError(
                "Create chunks before generating embeddings."
            );
            return;
        }

        setLoadingStage("embedding");
        setError("");

        try {
            await api.post(
                `/documents/${encodeURIComponent(
                    filename
                )}/embeddings`,
                null,
                {
                    params: {
                        model_name:
                            embeddingModel,
                    },
                }
            );

            const response =
                await api.get<VisualizationResponse>(
                    `/documents/${chunkData.document_id}/visualization`,
                    {
                        params: {
                            model_name:
                                embeddingModel,
                            method: "umap",
                            dimensions: 3,
                        },
                    }
                );

            const cleanPoints =
                (
                    response.data.points ||
                    []
                ).map((point, index) => ({
                    ...point,
                    chunk_number:
                        point.chunk_number ??
                        index,
                    retrieved: false,
                }));

            setVisualization({
                ...response.data,
                points: cleanPoints,
            });

            setRetrievalResults([]);
            setAnswerData(null);

            setStage("embedding");
        } catch (err: any) {
            setError(
                err.response?.data?.detail ||
                    "Could not generate embeddings."
            );
        } finally {
            setLoadingStage(null);
        }
    };

    /*
     * QUERY
     */

    const runQuery = async () => {
        if (!query.trim()) {
            setError("Enter a query first.");
            return;
        }

        if (!chunkData) {
            setError(
                "Create chunks before querying."
            );
            return;
        }

        setLoadingStage("query");
        setError("");

        try {
            const response =
                await api.get<VisualizationResponse>(
                    `/documents/${chunkData.document_id}/visualization`,
                    {
                        params: {
                            model_name:
                                embeddingModel,
                            method: "umap",
                            dimensions: 3,
                            query: query.trim(),
                        },
                    }
                );

            /*
             * Query stage:
             * only purple chunks + green query.
             */

            const cleanPoints =
                (
                    response.data.points ||
                    []
                ).map((point, index) => ({
                    ...point,
                    chunk_number:
                        point.chunk_number ??
                        index,
                    retrieved: false,
                }));

            setVisualization({
                ...response.data,
                points: cleanPoints,
            });

            setRetrievalResults([]);

            setStage("query");
        } catch (err: any) {
            setError(
                err.response?.data?.detail ||
                    "Could not visualize the query."
            );
        } finally {
            setLoadingStage(null);
        }
    };

    /*
     * RETRIEVAL
     *
     * Match retrieved results primarily by
     * normalized chunk text.
     */

    const runRetrieval = async () => {
        if (!query.trim()) {
            setError("Enter a query first.");
            return;
        }

        if (!chunkData) {
            setError(
                "Create chunks before retrieval."
            );
            return;
        }

        setLoadingStage("retrieval");
        setError("");

        try {
            const response = await api.post(
                `/documents/${chunkData.document_id}/search`,
                null,
                {
                    params: {
                        query: query.trim(),
                        model_name: embeddingModel,
                    },
                }
            );

            const data = response.data;

            console.log(
                "SEARCH RESPONSE:",
                data
            );

            const searchResults: RetrievalResult[] =
                Array.isArray(data)
                    ? data
                    : Array.isArray(
                          data?.results
                      )
                    ? data.results
                    : [];

            console.log(
                "SEARCH RESULTS:",
                searchResults
            );

            setRetrievalResults(
                searchResults
            );

            /*
             * ------------------------------------------------
             * Build a reliable lookup from retrieved results.
             * ------------------------------------------------
             */

            const retrievedTexts =
                new Set<string>();

            const retrievedIndexes =
                new Set<number>();

            searchResults.forEach(
                (result) => {
                    /*
                     * Text is the strongest identifier
                     * because it comes from the actual chunk.
                     */

                    if (
                        typeof result.text ===
                            "string" &&
                        result.text.trim()
                    ) {
                        retrievedTexts.add(
                            normalizeText(
                                result.text
                            )
                        );
                    }

                    if (
                        result.chunk_index !==
                            undefined &&
                        result.chunk_index !==
                            null &&
                        Number.isFinite(
                            Number(
                                result.chunk_index
                            )
                        )
                    ) {
                        retrievedIndexes.add(
                            Number(
                                result.chunk_index
                            )
                        );
                    }

                    if (
                        result.chunk_number !==
                            undefined &&
                        result.chunk_number !==
                            null &&
                        Number.isFinite(
                            Number(
                                result.chunk_number
                            )
                        )
                    ) {
                        retrievedIndexes.add(
                            Number(
                                result.chunk_number
                            )
                        );
                    }
                }
            );

            /*
             * ------------------------------------------------
             * Also create an authoritative map from chunkData.
             * ------------------------------------------------
             */

            const chunkNumberByText =
                new Map<string, number>();

            chunkData.chunks.forEach(
                (chunk) => {
                    chunkNumberByText.set(
                        normalizeText(
                            chunk.text
                        ),
                        chunk.chunk_number
                    );
                }
            );

            /*
             * Add chunk numbers derived from actual
             * chunk text.
             */

            searchResults.forEach(
                (result) => {
                    if (
                        typeof result.text ===
                            "string" &&
                        result.text.trim()
                    ) {
                        const chunkNumber =
                            chunkNumberByText.get(
                                normalizeText(
                                    result.text
                                )
                            );

                        if (
                            chunkNumber !==
                            undefined
                        ) {
                            retrievedIndexes.add(
                                chunkNumber
                            );
                        }
                    }
                }
            );

            console.log(
                "RETRIEVED INDEXES:",
                [...retrievedIndexes]
            );

            console.log(
                "RETRIEVED TEXTS:",
                [...retrievedTexts]
            );

            /*
             * ------------------------------------------------
             * Update current visualization.
             * ------------------------------------------------
             */

            setVisualization((current) => {
                if (
                    !current ||
                    !Array.isArray(
                        current.points
                    )
                ) {
                    console.log(
                        "NO VISUALIZATION POINTS"
                    );

                    return current;
                }

                const updatedPoints =
                    current.points.map(
                        (
                            point,
                            index
                        ) => {
                            /*
                             * Keep query point green.
                             */

                            if (
                                point.type ===
                                "query"
                            ) {
                                return {
                                    ...point,
                                    retrieved:
                                        false,
                                };
                            }

                            const pointNumber =
                                Number(
                                    point.chunk_number ??
                                        index
                                );

                            const pointText =
                                typeof point.text ===
                                "string"
                                    ? normalizeText(
                                          point.text
                                      )
                                    : "";

                            /*
                             * Match using:
                             *
                             * 1. exact chunk number
                             * 2. exact normalized text
                             */

                            const matchedByIndex =
                                retrievedIndexes.has(
                                    pointNumber
                                );

                            const matchedByText =
                                pointText.length >
                                    0 &&
                                retrievedTexts.has(
                                    pointText
                                );

                            const retrieved =
                                matchedByIndex ||
                                matchedByText;

                            console.log(
                                `Chunk ${pointNumber}:`,
                                {
                                    matchedByIndex,
                                    matchedByText,
                                    retrieved,
                                }
                            );

                            return {
                                ...point,

                                chunk_number:
                                    pointNumber,

                                retrieved,
                            };
                        }
                    );

                const orangeCount =
                    updatedPoints.filter(
                        (point) =>
                            point.type !==
                                "query" &&
                            point.retrieved ===
                                true
                    ).length;

                console.log(
                    "ORANGE POINT COUNT:",
                    orangeCount
                );

                return {
                    ...current,
                    points:
                        updatedPoints,
                };
            });

            setStage("retrieval");
        } catch (err: any) {
            console.error(
                "RETRIEVAL ERROR:",
                err
            );

            setError(
                err.response?.data?.detail ||
                    "Could not retrieve chunks."
            );
        } finally {
            setLoadingStage(null);
        }
    };

    /*
     * ANSWER
     */

    const runAnswer = async () => {
        if (!query.trim()) {
            setError("Enter a query first.");
            return;
        }

        if (!chunkData) {
            setError(
                "Create chunks before asking questions."
            );
            return;
        }

        setLoadingStage("answer");
        setError("");

        try {
            const response =
                await api.post<AskResponse>(
                    `/documents/${chunkData.document_id}/ask`,
                    null,
                    {
                        params: {
                            query: query.trim(),
                        },
                    }
                );

            setAnswerData(response.data);

            setStage("answer");
        } catch (err: any) {
            setError(
                err.response?.data?.detail ||
                    "Could not generate the answer."
            );
        } finally {
            setLoadingStage(null);
        }
    };

    /*
     * PLOT DATA
     */

    const plotPoints = useMemo(() => {
        if (!visualization) {
            return [];
        }

        if (
            Array.isArray(
                visualization.points
            )
        ) {
            return visualization.points;
        }

        if (
            Array.isArray(
                visualization.embeddings
            )
        ) {
            return visualization.embeddings;
        }

        return [];
    }, [visualization]);

    /*
     * DRAW 3D PLOT
     */

    const drawPlot = () => {
        if (!plotRef.current) {
            return;
        }

        if (!plotPoints.length) {
            return;
        }

        const chunkPoints =
            plotPoints.filter(
                (point) =>
                    point.type !== "query"
            );

        const normalChunks =
            chunkPoints.filter(
                (point) =>
                    !point.retrieved
            );

        const retrievedChunks =
            chunkPoints.filter(
                (point) =>
                    point.retrieved
            );

        const queryPoints =
            plotPoints.filter(
                (point) =>
                    point.type === "query"
            );

        const traces: any[] = [];

        /*
         * NORMAL CHUNKS
         */

        if (normalChunks.length > 0) {
            traces.push({
                x: normalChunks.map(
                    (point) =>
                        point.x ?? 0
                ),

                y: normalChunks.map(
                    (point) =>
                        point.y ?? 0
                ),

                z: normalChunks.map(
                    (point) =>
                        point.z ?? 0
                ),

                text: normalChunks.map(
                    (point) =>
                        `Chunk ${
                            (point.chunk_number ??
                                0) + 1
                        }<br>Page ${
                            point.page_number ??
                            "-"
                        }`
                ),

                mode: "markers",

                type: "scatter3d",

                name: "Document chunks",

                marker: {
                    size: 5,
                    color: "#7b68ee",
                    opacity: 0.72,
                },

                hovertemplate:
                    "%{text}<extra></extra>",
            });
        }

        /*
         * RETRIEVED CHUNKS
         */

        if (retrievedChunks.length > 0) {
            traces.push({
                x: retrievedChunks.map(
                    (point) =>
                        point.x ?? 0
                ),

                y: retrievedChunks.map(
                    (point) =>
                        point.y ?? 0
                ),

                z: retrievedChunks.map(
                    (point) =>
                        point.z ?? 0
                ),

                text: retrievedChunks.map(
                    (point) =>
                        `Retrieved chunk ${
                            (point.chunk_number ??
                                0) + 1
                        }<br>Page ${
                            point.page_number ??
                            "-"
                        }`
                ),

                mode: "markers",

                type: "scatter3d",

                name: "Retrieved chunks",

                marker: {
                    size: 8,
                    color: "#f59e0b",
                    opacity: 1,

                    line: {
                        color: "#ffffff",
                        width: 2,
                    },
                },

                hovertemplate:
                    "%{text}<extra></extra>",
            });
        }

        /*
         * QUERY
         */

        if (queryPoints.length > 0) {
            traces.push({
                x: queryPoints.map(
                    (point) =>
                        point.x ?? 0
                ),

                y: queryPoints.map(
                    (point) =>
                        point.y ?? 0
                ),

                z: queryPoints.map(
                    (point) =>
                        point.z ?? 0
                ),

                text: queryPoints.map(
                    () =>
                        `Query<br>"${query}"`
                ),

                mode: "markers",

                type: "scatter3d",

                name: "Query",

                marker: {
                    size: 5,
                    color: "#32b89a",
                    opacity: 1,
                    symbol: "diamond",

                    line: {
                        color: "#ffffff",
                        width: 2,
                    },
                },

                hovertemplate:
                    "%{text}<extra></extra>",
            });
        }

        Plotly.react(
            plotRef.current,
            traces,
            {
                paper_bgcolor:
                    "rgba(0,0,0,0)",

                plot_bgcolor:
                    "rgba(0,0,0,0)",

                margin: {
                    l: 0,
                    r: 0,
                    t: 0,
                    b: 0,
                },

                showlegend: true,

                legend: {
                    bgcolor:
                        "rgba(255,255,255,0.88)",

                    bordercolor:
                        "#e6e1ed",

                    borderwidth: 1,

                    font: {
                        color: "#5f596a",
                    },
                },

                scene: {
                    bgcolor:
                        "rgba(0,0,0,0)",

                    camera: {
                        eye: {
                            x: 1.55,
                            y: 1.55,
                            z: 1.25,
                        },
                    },

                    xaxis: {
                        title: {
                            text: "UMAP 1",
                        },

                        showgrid: true,

                        gridcolor:
                            "#ddd6e8",

                        zeroline: false,
                    },

                    yaxis: {
                        title: {
                            text: "UMAP 2",
                        },

                        showgrid: true,

                        gridcolor:
                            "#ddd6e8",

                        zeroline: false,
                    },

                    zaxis: {
                        title: {
                            text: "UMAP 3",
                        },

                        showgrid: true,

                        gridcolor:
                            "#ddd6e8",

                        zeroline: false,
                    },
                },
            },

            {
                responsive: true,
                displaylogo: false,
                scrollZoom: true,
            }
        );
    };

    useEffect(() => {
        if (!plotPoints.length) {
            return;
        }

        drawPlot();

        return () => {
            if (plotRef.current) {
                Plotly.purge(
                    plotRef.current
                );
            }
        };
    }, [plotPoints, query]);

    const extractionReady =
        Boolean(extraction);

    const chunkingReady =
        Boolean(chunkData);

    const embeddingReady =
        Boolean(visualization);

    /*
     * Find the real chunk number from the
     * authoritative chunkData using text.
     */

    const getSourceChunkNumber = (
        source: Source
    ) => {
        if (
            source.chunk_index !==
                undefined &&
            source.chunk_index !== null &&
            Number.isFinite(
                Number(
                    source.chunk_index
                )
            )
        ) {
            return Number(
                source.chunk_index
            );
        }

        if (
            source.chunk_number !==
                undefined &&
            source.chunk_number !== null &&
            Number.isFinite(
                Number(
                    source.chunk_number
                )
            )
        ) {
            return Number(
                source.chunk_number
            );
        }

        const sourceText =
            normalizeText(source.text);

        if (chunkData) {
            const matchingChunk =
                chunkData.chunks.find(
                    (chunk) =>
                        normalizeText(
                            chunk.text
                        ) ===
                        sourceText
                );

            if (matchingChunk) {
                return matchingChunk.chunk_number;
            }
        }

        return null;
    };

    return (
        <main className="viz-page">

            {/* HERO */}

            <section className="viz-hero">

                <div>

                    <div className="viz-badge">

                        <Sparkles size={14} />

                        RAGVIZ / VISUALIZATION MODE

                    </div>

                    <h1>
                        See what happens
                        <span> inside RAG.</span>
                    </h1>

                    <p>
                        Trace your document from raw PDF
                        to grounded answer, and watch each
                        stage of the pipeline come alive.
                    </p>

                </div>

            </section>

            {/* PIPELINE */}

            <section className="pipeline-shell">

                {stages.map(
                    (item, index) => {

                        const complete =
                            index <
                            currentStageIndex;

                        const active =
                            index ===
                            currentStageIndex;

                        return (
                            <div
                                className="pipeline-item"
                                key={item.id}
                            >

                                <div
                                    className={[
                                        "pipeline-node",
                                        complete
                                            ? "complete"
                                            : "",
                                        active
                                            ? "active"
                                            : "",
                                    ].join(" ")}
                                >

                                    {complete ? (
                                        <Check
                                            size={15}
                                        />
                                    ) : (
                                        index + 1
                                    )}

                                </div>

                                <span
                                    className={
                                        active
                                            ? "active-label"
                                            : ""
                                    }
                                >
                                    {item.label}
                                </span>

                                {index <
                                    stages.length -
                                        1 && (
                                    <div className="pipeline-line" />
                                )}

                            </div>
                        );
                    }
                )}

            </section>

            {/* ERROR */}

            {error && (
                <section className="viz-message">

                    <Alert
                        type="error"
                        showIcon
                        message={error}
                    />

                </section>
            )}

            {/* DOCUMENT */}

            <section className="viz-section">

                <div className="section-heading">

                    <div>

                        <span>
                            STEP 01
                        </span>

                        <h2>
                            Choose your document
                        </h2>

                        <p>
                            Start with the source that
                            will move through the pipeline.
                        </p>

                    </div>

                </div>

                <Card className="document-card">

                    <div className="document-input-wrap">

                        <FileText size={19} />

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

                    <button
                        className="viz-primary-button"
                        onClick={
                            runExtraction
                        }
                        disabled={
                            loadingStage !== null
                        }
                    >

                        {loadingStage ===
                        "extraction" ? (
                            <>
                                <Spin size="small" />
                                Reading...
                            </>
                        ) : (
                            <>
                                Begin pipeline

                                <ArrowDown
                                    size={17}
                                />
                            </>
                        )}

                    </button>

                </Card>

            </section>

            {/* EXTRACTION */}

            {(stage !== "document" ||
                extractionReady) && (
                <section className="viz-section">

                    <div className="section-heading">

                        <div>

                            <span>
                                STEP 02 · DATA INGESTION
                            </span>

                            <h2>
                                Extracting the document
                            </h2>

                            <p>
                                The PDF is converted into
                                machine-readable text.
                            </p>

                        </div>

                        {extraction && (
                            <Tag color="green">
                                Extraction complete
                            </Tag>
                        )}

                    </div>

                    {extraction && (
                        <>

                            <div className="metric-grid">

                                <Card>

                                    <div className="metric-label">
                                        Pages
                                    </div>

                                    <div className="metric-value">
                                        {
                                            extraction.page_count
                                        }
                                    </div>

                                </Card>

                                <Card>

                                    <div className="metric-label">
                                        Characters
                                    </div>

                                    <div className="metric-value">
                                        {extraction.total_characters.toLocaleString()}
                                    </div>

                                </Card>

                                <Card>

                                    <div className="metric-label">
                                        Words
                                    </div>

                                    <div className="metric-value">
                                        {extraction.total_words.toLocaleString()}
                                    </div>

                                </Card>

                            </div>

                            <div className="page-density-card">

                                {extraction.pages.map(
                                    (page) => {

                                        const maxWords =
                                            Math.max(
                                                ...extraction.pages.map(
                                                    (
                                                        item
                                                    ) =>
                                                        item.word_count ??
                                                        item.text
                                                            .split(
                                                                /\s+/
                                                            )
                                                            .filter(
                                                                Boolean
                                                            )
                                                            .length
                                                ),
                                                1
                                            );

                                        const words =
                                            page.word_count ??
                                            page.text
                                                .split(
                                                    /\s+/
                                                )
                                                .filter(
                                                    Boolean
                                                ).length;

                                        return (
                                            <div
                                                className="density-row"
                                                key={
                                                    page.page
                                                }
                                            >

                                                <div className="density-page">
                                                    Page{" "}
                                                    {
                                                        page.page
                                                    }
                                                </div>

                                                <div className="density-track">

                                                    <div
                                                        className="density-fill"
                                                        style={{
                                                            width: `${(
                                                                words /
                                                                maxWords
                                                            ) *
                                                                100}%`,
                                                        }}
                                                    />

                                                </div>

                                                <strong>
                                                    {
                                                        words
                                                    }{" "}
                                                    words
                                                </strong>

                                            </div>
                                        );
                                    }
                                )}

                            </div>

                            <div className="continue-row">

                                <div>

                                    <Layers3
                                        size={18}
                                    />

                                    <span>
                                        Next: divide the
                                        document into chunks
                                    </span>

                                </div>

                                <button
                                    className="soft-button"
                                    onClick={() =>
                                        setStage(
                                            "chunking"
                                        )
                                    }
                                >
                                    Continue to chunking
                                </button>

                            </div>

                        </>
                    )}

                </section>
            )}

            {/* CHUNKING */}

            {(stage === "chunking" ||
                chunkingReady ||
                currentStageIndex >= 2) && (
                <section className="viz-section">

                    <div className="section-heading">

                        <div>

                            <span>
                                STEP 03 · CHUNKING
                            </span>

                            <h2>
                                How should we divide it?
                            </h2>

                            <p>
                                Choose a strategy and see the
                                document transform into smaller
                                retrieval units.
                            </p>

                        </div>

                    </div>

                    <Card className="chunk-control-card">

                        <div className="strategy-selector">

                            <label>
                                Chunking strategy
                            </label>

                            <Select
                                value={
                                    selectedStrategy
                                }
                                onChange={
                                    setSelectedStrategy
                                }
                                size="large"
                                options={[
                                    {
                                        value: "recursive",
                                        label:
                                            "Recursive",
                                    },
                                    {
                                        value: "fixed",
                                        label:
                                            "Fixed",
                                    },
                                    {
                                        value: "token",
                                        label:
                                            "Token",
                                    },
                                ]}
                            />

                        </div>

                        <button
                            className="viz-primary-button"
                            onClick={
                                runChunking
                            }
                            disabled={
                                loadingStage !== null
                            }
                        >

                            {loadingStage ===
                            "chunking" ? (
                                <>
                                    <Spin size="small" />
                                    Splitting...
                                </>
                            ) : (
                                <>
                                    Split document

                                    <Layers3
                                        size={17}
                                    />
                                </>
                            )}

                        </button>

                    </Card>

                    {chunkData && (
                        <>

                            <div className="metric-grid">

                                <Card>

                                    <div className="metric-label">
                                        Chunks created
                                    </div>

                                    <div className="metric-value">
                                        {
                                            chunkData.chunk_count
                                        }
                                    </div>

                                </Card>

                                <Card>

                                    <div className="metric-label">
                                        Strategy
                                    </div>

                                    <div className="metric-value metric-text">
                                        {
                                            chunkData.strategy
                                        }
                                    </div>

                                </Card>

                                <Card>

                                    <div className="metric-label">
                                        Pages represented
                                    </div>

                                    <div className="metric-value">
                                        {
                                            new Set(
                                                chunkData.chunks.map(
                                                    (
                                                        chunk
                                                    ) =>
                                                        chunk.page_number
                                                )
                                            ).size
                                        }
                                    </div>

                                </Card>

                            </div>

                            <div className="chunk-map-card">

                                {Object.entries(
                                    chunkData.chunks.reduce(
                                        (
                                            groups,
                                            chunk
                                        ) => {

                                            if (
                                                !groups[
                                                    chunk.page_number
                                                ]
                                            ) {
                                                groups[
                                                    chunk.page_number
                                                ] = [];
                                            }

                                            groups[
                                                chunk.page_number
                                            ].push(
                                                chunk
                                            );

                                            return groups;

                                        },
                                        {} as Record<
                                            number,
                                            Chunk[]
                                        >
                                    )
                                ).map(
                                    (
                                        [
                                            page,
                                            chunks,
                                        ]
                                    ) => (

                                        <div
                                            className="chunk-map-row"
                                            key={page}
                                        >

                                            <div className="chunk-map-page">

                                                <span>
                                                    PAGE
                                                </span>

                                                <strong>
                                                    {page}
                                                </strong>

                                            </div>

                                            <div className="chunk-map-items">

                                                {chunks.map(
                                                    (
                                                        chunk
                                                    ) => (

                                                        <div
                                                            className="chunk-map-item"
                                                            key={
                                                                chunk.chunk_id
                                                            }
                                                            style={{
                                                                borderColor:
                                                                    strategyColors[
                                                                        chunkData.strategy
                                                                    ],
                                                                background:
                                                                    `${strategyColors[
                                                                        chunkData.strategy
                                                                    ]}18`,
                                                            }}
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

                            <div className="continue-row">

                                <div>

                                    <CircleDot
                                        size={18}
                                    />

                                    <span>
                                        Next: turn each chunk
                                        into a vector
                                    </span>

                                </div>

                                <button
                                    className="soft-button"
                                    onClick={() =>
                                        setStage(
                                            "embedding"
                                        )
                                    }
                                >
                                    Continue to embeddings
                                </button>

                            </div>

                        </>
                    )}

                </section>
            )}

            {/* EMBEDDINGS */}

            {(stage === "embedding" ||
                currentStageIndex >= 3) && (
                <section className="viz-section">

                    <div className="section-heading">

                        <div>

                            <span>
                                STEP 04 · EMBEDDINGS
                            </span>

                            <h2>
                                Enter the vector space
                            </h2>

                            <p>
                                Your chunks are converted into
                                high-dimensional embeddings and
                                projected into 3D with UMAP.
                            </p>

                        </div>

                    </div>

                    <Card className="embedding-control-card">

                        <div>

                            <label>
                                Embedding model
                            </label>

                            <Select
                                value={
                                    embeddingModel
                                }
                                onChange={
                                    setEmbeddingModel
                                }
                                size="large"
                                options={[
                                    {
                                        value: "minilm",
                                        label:
                                            "MiniLM · 384D",
                                    },
                                    {
                                        value: "mpnet",
                                        label:
                                            "MPNet · 768D",
                                    },
                                    {
                                        value:
                                            "distilroberta",
                                        label:
                                            "DistilRoBERTa · 768D",
                                    },
                                ]}
                            />

                        </div>

                        <button
                            className="viz-primary-button"
                            onClick={
                                runEmbeddings
                            }
                            disabled={
                                loadingStage !== null
                            }
                        >

                            {loadingStage ===
                            "embedding" ? (
                                <>
                                    <Spin size="small" />
                                    Embedding...
                                </>
                            ) : (
                                <>
                                    Generate embeddings

                                    <Sparkles
                                        size={17}
                                    />
                                </>
                            )}

                        </button>

                    </Card>

                    {embeddingReady && (
                        <Card className="plot-card">

                            <div className="plot-heading">

                                <div>

                                    <strong>
                                        3D semantic space
                                    </strong>

                                    <span>
                                        UMAP projection of
                                        document chunks
                                    </span>

                                </div>

                                <div className="plot-legend">

                                    <span>
                                        <i className="legend-dot purple" />
                                        Chunks
                                    </span>

                                    <span>
                                        <i className="legend-dot orange" />
                                        Retrieved
                                    </span>

                                    <span>
                                        <i className="legend-dot green" />
                                        Query
                                    </span>

                                </div>

                            </div>

                            <div
                                ref={plotRef}
                                className="embedding-plot"
                            />

                        </Card>
                    )}

                    <div className="continue-row">

                        <div>

                            <MessageCircle
                                size={18}
                            />

                            <span>
                                Next: add a question to the
                                vector space
                            </span>

                        </div>

                        <button
                            className="soft-button"
                            onClick={() =>
                                setStage("query")
                            }
                        >
                            Continue to query
                        </button>

                    </div>

                </section>
            )}

            {/* QUERY */}

            {(stage === "query" ||
                currentStageIndex >= 4) && (
                <section className="viz-section">

                    <div className="section-heading">

                        <div>

                            <span>
                                STEP 05 · QUERY
                            </span>

                            <h2>
                                Ask your document
                            </h2>

                            <p>
                                Your question becomes another
                                point in the same semantic space.
                            </p>

                        </div>

                    </div>

                    <Card className="query-card">

                        <div className="query-input-wrap">

                            <Search size={19} />

                            <input
                                value={query}
                                onChange={(e) =>
                                    setQuery(
                                        e.target.value
                                    )
                                }
                                placeholder="What would you like to know?"
                                onKeyDown={(e) => {

                                    if (
                                        e.key ===
                                        "Enter"
                                    ) {
                                        runQuery();
                                    }

                                }}
                            />

                        </div>

                        <button
                            className="viz-primary-button"
                            onClick={
                                runQuery
                            }
                            disabled={
                                loadingStage !== null
                            }
                        >

                            {loadingStage ===
                            "query" ? (
                                <>
                                    <Spin size="small" />
                                    Mapping...
                                </>
                            ) : (
                                <>
                                    Map query

                                    <CircleDot
                                        size={17}
                                    />
                                </>
                            )}

                        </button>

                    </Card>

                    {query &&
                        visualization && (
                            <Card className="query-insight-card">

                                <div className="query-icon">

                                    <Search size={19} />

                                </div>

                                <div>

                                    <span>
                                        QUERY EMBEDDING
                                    </span>

                                    <strong>
                                        "{query}"
                                    </strong>

                                    <p>
                                        Your question is now
                                        represented as a green
                                        point in the same semantic
                                        space as the chunks.
                                    </p>

                                </div>

                            </Card>
                        )}

                    <div className="continue-row">

                        <div>

                            <Search size={18} />

                            <span>
                                Next: find the most relevant
                                chunks
                            </span>

                        </div>

                        <button
                            className="soft-button"
                            onClick={
                                runRetrieval
                            }
                            disabled={
                                loadingStage !== null
                            }
                        >
                            Retrieve context
                        </button>

                    </div>

                </section>
            )}

            {/* RETRIEVAL */}

            {(stage === "retrieval" ||
                currentStageIndex >= 5) && (
                <section className="viz-section">

                    <div className="section-heading">

                        <div>

                            <span>
                                STEP 06 · RETRIEVAL
                            </span>

                            <h2>
                                Finding the relevant context
                            </h2>

                            <p>
                                The query searches the vector
                                space and retrieves the chunks
                                closest to its meaning.
                            </p>

                        </div>

                        {retrievalResults.length > 0 && (
                            <Tag color="orange">

                                {
                                    retrievalResults.length
                                }{" "}
                                chunks retrieved

                            </Tag>
                        )}

                    </div>

                    <Card className="retrieval-card">

                        <div className="retrieval-flow">

                            <div className="flow-node query-node">

                                <Search size={18} />

                                <span>
                                    Query
                                </span>

                            </div>

                            <div className="flow-arrow">
                                →
                            </div>

                            <div className="flow-node vector-node">

                                <CircleDot
                                    size={18}
                                />

                                <span>
                                    Vector search
                                </span>

                            </div>

                            <div className="flow-arrow">
                                →
                            </div>

                            <div className="flow-node context-node">

                                <Layers3
                                    size={18}
                                />

                                <span>
                                    Top chunks
                                </span>

                            </div>

                        </div>

                    </Card>

                    {retrievalResults.length > 0 && (
                        <div className="retrieval-results-card">

                            <div className="retrieval-results-header">

                                <div>

                                    <span>
                                        RETRIEVAL RESULTS
                                    </span>

                                    <strong>
                                        Closest chunks to your query
                                    </strong>

                                </div>

                                <div className="retrieval-count">
                                    {
                                        retrievalResults.length
                                    }
                                </div>

                            </div>

                            <div className="retrieval-results-list">

                                {retrievalResults.map(
                                    (
                                        result,
                                        index
                                    ) => {

                                        const realChunkNumber =
                                            result.chunk_index ??
                                            result.chunk_number;

                                        const chunkFromText =
                                            result.text &&
                                            chunkData
                                                ? chunkData.chunks.find(
                                                      (
                                                          chunk
                                                      ) =>
                                                          normalizeText(
                                                              chunk.text
                                                          ) ===
                                                          normalizeText(
                                                              result.text ??
                                                                  ""
                                                          )
                                                  )
                                                : undefined;

                                        const displayChunkNumber =
                                            realChunkNumber ??
                                            chunkFromText
                                                ?.chunk_number ??
                                            index;

                                        return (
                                            <div
                                                className="retrieval-result"
                                                key={`${displayChunkNumber}-${index}`}
                                            >

                                                <div className="retrieval-rank">
                                                    #{index + 1}
                                                </div>

                                                <div className="retrieval-result-main">

                                                    <div className="retrieval-result-top">

                                                        <div className="retrieval-result-title">

                                                            <strong>
                                                                Chunk{" "}
                                                                {
                                                                    displayChunkNumber +
                                                                    1
                                                                }
                                                            </strong>

                                                            <Tag color="orange">
                                                                Page{" "}
                                                                {
                                                                    result.page_number ??
                                                                    chunkFromText
                                                                        ?.page_number ??
                                                                    "—"
                                                                }
                                                            </Tag>

                                                        </div>

                                                        <div className="retrieval-distance">

                                                            <span>
                                                                Distance
                                                            </span>

                                                            <strong>
                                                                {typeof result.distance ===
                                                                "number"
                                                                    ? result.distance.toFixed(
                                                                          4
                                                                      )
                                                                    : "—"}
                                                            </strong>

                                                        </div>

                                                    </div>

                                                    <p>
                                                        {
                                                            result.text ??
                                                            "Retrieved chunk"
                                                        }
                                                    </p>

                                                </div>

                                            </div>
                                        );
                                    }
                                )}

                            </div>

                        </div>
                    )}

                    {retrievalResults.length === 0 && (
                        <div className="retrieval-empty">

                            <CircleDot size={19} />

                            <div>

                                <strong>
                                    Retrieval completed
                                </strong>

                                <span>
                                    The search returned no
                                    matching chunks.
                                </span>

                            </div>

                        </div>
                    )}

                    <div className="continue-row">

                        <div>

                            <Sparkles size={18} />

                            <span>
                                Next: generate the grounded
                                answer
                            </span>

                        </div>

                        <button
                            className="soft-button"
                            onClick={
                                runAnswer
                            }
                            disabled={
                                loadingStage !== null
                            }
                        >
                            Generate answer
                        </button>

                    </div>

                </section>
            )}

            {/* ANSWER */}

            {(stage === "answer" ||
                answerData) && (
                <section className="viz-section answer-section">

                    <div className="section-heading">

                        <div>

                            <span>
                                STEP 07 · ANSWER
                            </span>

                            <h2>
                                Grounded response
                            </h2>

                            <p>
                                The final answer is generated
                                using the retrieved document context.
                            </p>

                        </div>

                        <Tag color="green">
                            Grounded
                        </Tag>

                    </div>

                    {answerData && (
                        <>

                            <Card className="answer-card">

                                <div className="answer-icon">

                                    <Sparkles size={20} />

                                </div>

                                <div>

                                    <span className="answer-label">
                                        ANSWER
                                    </span>

                                    <p className="answer-text">
                                        {
                                            answerData.answer
                                        }
                                    </p>

                                </div>

                            </Card>

                            <div className="sources-section">

                                <div className="sources-title">

                                    <FileText size={18} />

                                    <strong>
                                        Sources
                                    </strong>

                                    <span>
                                        {
                                            answerData
                                                .sources
                                                .length
                                        }{" "}
                                        cited chunks
                                    </span>

                                </div>

                                <Collapse
                                    bordered={false}
                                    items={answerData.sources.map(
                                        (
                                            source,
                                            index
                                        ) => {

                                            const sourceChunkNumber =
                                                getSourceChunkNumber(
                                                    source
                                                );

                                            const sourcePage =
                                                source.page_number ??
                                                (
                                                    chunkData?.chunks.find(
                                                        (
                                                            chunk
                                                        ) =>
                                                            normalizeText(
                                                                chunk.text
                                                            ) ===
                                                            normalizeText(
                                                                source.text
                                                            )
                                                    )
                                                )?.page_number;

                                            return {
                                                key: `${sourceChunkNumber ?? index}-${index}`,

                                                label: (
                                                    <div className="source-header">

                                                        <span>
                                                            Chunk{" "}
                                                            {sourceChunkNumber !==
                                                            null
                                                                ? sourceChunkNumber +
                                                                  1
                                                                : "—"}
                                                        </span>

                                                        <Tag>
                                                            Page{" "}
                                                            {
                                                                sourcePage ??
                                                                "—"
                                                            }
                                                        </Tag>

                                                        <small>
                                                            Distance{" "}
                                                            {
                                                                typeof source.distance ===
                                                                "number"
                                                                    ? source.distance.toFixed(
                                                                          4
                                                                      )
                                                                    : "—"
                                                            }
                                                        </small>

                                                    </div>
                                                ),

                                                children: (
                                                    <p className="source-text">
                                                        {
                                                            source.text
                                                        }
                                                    </p>
                                                ),
                                            };
                                        }
                                    )}
                                />

                            </div>

                            {answerData.metrics && (
                                <div className="answer-metrics">

                                    <div>

                                        <span>
                                            Retrieval
                                        </span>

                                        <strong>
                                            {
                                                answerData
                                                    .metrics
                                                    .retrieval_latency_ms
                                            }
                                            ms
                                        </strong>

                                    </div>

                                    <div>

                                        <span>
                                            LLM
                                        </span>

                                        <strong>
                                            {
                                                answerData
                                                    .metrics
                                                    .llm_latency_ms
                                            }
                                            ms
                                        </strong>

                                    </div>

                                    <div>

                                        <span>
                                            Total
                                        </span>

                                        <strong>
                                            {
                                                answerData
                                                    .metrics
                                                    .total_latency_ms
                                            }
                                            ms
                                        </strong>

                                    </div>

                                </div>
                            )}

                        </>
                    )}

                </section>
            )}

            {/* FOOTER */}

            <section className="viz-footer">

                <UploadCloud size={17} />

                <span>
                    Every stage is connected — from
                    document ingestion to grounded answer.
                </span>

            </section>

        </main>
    );
}

export default Visualization;