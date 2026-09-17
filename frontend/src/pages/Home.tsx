import {
    ArrowRight,
    BookOpen,
    FlaskConical,
    Sparkles,
    Upload,
} from "lucide-react";

import "./Home.css";

interface HomeProps {
    onNavigate: (
        page:
            | "stored"
            | "upload"
            | "visualization"
            | "experiment"
    ) => void;
}

function Home({ onNavigate }: HomeProps) {
    return (
        <main className="home-page">

            {/* HERO */}

            <section className="home-hero">

                <div className="hero-badge">
                    <Sparkles size={10} />
                    Interactive RAG Playground
                </div>

                <h1>
                    Explore the entire RAG pipeline
                    <span> one stage at a time.</span>
                </h1>

                <p>
                    Upload a document, trace how it becomes
                    embeddings and retrieved context, and
                    understand what happens before the final
                    grounded answer.
                </p>

            </section>

            {/* FOUR MAIN OPTIONS */}

            <section className="home-options">

                <button
                    className="home-option option-documents"
                    onClick={() =>
                        onNavigate("stored")
                    }
                >
                    <div className="option-icon">
                        <BookOpen size={25} />
                    </div>

                    <div className="option-content">
                        <div className="option-top">
                            <span className="option-number">
                                01
                            </span>

                            <ArrowRight
                                size={19}
                                className="option-arrow"
                            />
                        </div>

                        <h2>
                            Stored Documents
                        </h2>

                        <p>
                            Browse the documents you've
                            already added to RAGViz.
                        </p>
                    </div>
                </button>


                <button
                    className="home-option option-upload"
                    onClick={() =>
                        onNavigate("upload")
                    }
                >
                    <div className="option-icon">
                        <Upload size={25} />
                    </div>

                    <div className="option-content">
                        <div className="option-top">
                            <span className="option-number">
                                02
                            </span>

                            <ArrowRight
                                size={19}
                                className="option-arrow"
                            />
                        </div>

                        <h2>
                            Upload Documents
                        </h2>

                        <p>
                            Add a PDF and prepare it for
                            exploration through the pipeline.
                        </p>
                    </div>
                </button>


                <button
                    className="home-option option-visualize"
                    onClick={() =>
                        onNavigate("visualization")
                    }
                >
                    <div className="option-icon">
                        <Sparkles size={25} />
                    </div>

                    <div className="option-content">
                        <div className="option-top">
                            <span className="option-number">
                                03
                            </span>

                            <ArrowRight
                                size={19}
                                className="option-arrow"
                            />
                        </div>

                        <h2>
                            Visualize RAG
                        </h2>

                        <p>
                            Follow the complete journey from
                            PDF ingestion to final retrieval, answer generation, and citations.
                        </p>
                    </div>
                </button>


                <button
                    className="home-option option-experiment"
                    onClick={() =>
                        onNavigate("experiment")
                    }
                >
                    <div className="option-icon">
                        <FlaskConical size={25} />
                    </div>

                    <div className="option-content">
                        <div className="option-top">
                            <span className="option-number">
                                04
                            </span>

                            <ArrowRight
                                size={19}
                                className="option-arrow"
                            />
                        </div>

                        <h2>
                            Experiment
                        </h2>

                        <p>
                            Compare different chunking strategies, embedding models,
                            retrieval strategies, and performance.
                        </p>
                    </div>
                </button>

            </section>


            {/* BOTTOM MESSAGE */}

            <section className="home-bottom">

                <div className="pipeline-line">

                    <div className="pipeline-step">
                        <span>01</span>
                        Ingest
                    </div>

                    <div className="pipeline-connector" />

                    <div className="pipeline-step">
                        <span>02</span>
                        Chunk
                    </div>

                    <div className="pipeline-connector" />

                    <div className="pipeline-step">
                        <span>03</span>
                        Embed
                    </div>

                    <div className="pipeline-connector" />

                    <div className="pipeline-step">
                        <span>04</span>
                        Retrieve
                    </div>

                    <div className="pipeline-connector" />

                    <div className="pipeline-step">
                        <span>05</span>
                        Answer
                    </div>

                </div>

                <p>
                    From document to answer —
                    <strong>
                        see what actually happens inside RAG.
                    </strong>
                </p>

            </section>

        </main>
    );
}

export default Home;