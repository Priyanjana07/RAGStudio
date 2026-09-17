import { useState } from "react";
import api from "../services/api";
import "./PDFProcessing.css";

interface PageData {
    page: number;
    text: string;
}

interface ExtractionResponse {
    filename: string;
    page_count: number;
    total_characters: number;
    total_words: number;
    pages: PageData[];
}

function PDFProcessing() {
    const [filename, setFilename] = useState("");
    const [data, setData] = useState<ExtractionResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleProcess = async () => {
        if (!filename.trim()) {
            setError("Please enter a PDF filename.");
            return;
        }

        setLoading(true);
        setError("");
        setData(null);

        try {
            const response = await api.post<ExtractionResponse>(
                `/documents/${encodeURIComponent(filename)}/extract`
            );

            setData(response.data);
        } catch (err: any) {
            setError(
                err.response?.data?.detail ||
                "Failed to process PDF."
            );
        } finally {
            setLoading(false);
        }
    };

    const maxWords = data
        ? Math.max(
              ...data.pages.map((page) =>
                  page.text.split(/\s+/).filter(Boolean).length
              ),
              1
          )
        : 1;

    return (
        <main className="processing-page">

            <section className="page-header">
                <p className="eyebrow">RAGVIZ</p>

                <h1>PDF Processing</h1>

                <p className="subtitle">
                    See how your document is processed before
                    entering the RAG pipeline.
                </p>
            </section>

            <section className="input-card">

                <input
                    type="text"
                    placeholder="Enter PDF filename..."
                    value={filename}
                    onChange={(e) => setFilename(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter") {
                            handleProcess();
                        }
                    }}
                />

                <button
                    onClick={handleProcess}
                    disabled={loading}
                >
                    {loading ? "Processing..." : "Process PDF"}
                </button>

            </section>

            {error && (
                <div className="error-box">
                    {error}
                </div>
            )}

            {loading && (
                <section className="pipeline-card">

                    <div className="pipeline-stage active">
                        <div className="stage-icon">1</div>

                        <div>
                            <strong>Loading PDF</strong>
                            <span>Reading document</span>
                        </div>
                    </div>

                    <div className="pipeline-arrow">→</div>

                    <div className="pipeline-stage">
                        <div className="stage-icon">2</div>

                        <div>
                            <strong>Extracting Text</strong>
                            <span>Reading page content</span>
                        </div>
                    </div>

                    <div className="pipeline-arrow">→</div>

                    <div className="pipeline-stage">
                        <div className="stage-icon">3</div>

                        <div>
                            <strong>Analyzing Pages</strong>
                            <span>Calculating statistics</span>
                        </div>
                    </div>

                </section>
            )}

            {data && (
                <>

                    {/* Processing pipeline */}

                    <section className="pipeline-card">

                        <div className="pipeline-wrapper">

                            <div className="pipeline-stage completed">
                                <div className="stage-icon">
                                    ✓
                                </div>

                                <div>
                                    <strong>PDF Upload</strong>
                                    <span>completed</span>
                                </div>
                            </div>

                            <div className="pipeline-arrow">
                                →
                            </div>

                            <div className="pipeline-stage completed">
                                <div className="stage-icon">
                                    ✓
                                </div>

                                <div>
                                    <strong>PDF Loading</strong>
                                    <span>completed</span>
                                </div>
                            </div>

                            <div className="pipeline-arrow">
                                →
                            </div>

                            <div className="pipeline-stage completed">
                                <div className="stage-icon">
                                    ✓
                                </div>

                                <div>
                                    <strong>Text Extraction</strong>
                                    <span>completed</span>
                                </div>
                            </div>

                            <div className="pipeline-arrow">
                                →
                            </div>

                            <div className="pipeline-stage completed">
                                <div className="stage-icon">
                                    ✓
                                </div>

                                <div>
                                    <strong>Page Analysis</strong>
                                    <span>completed</span>
                                </div>
                            </div>

                        </div>

                    </section>


                    {/* Document statistics */}

                    <section className="document-section">

                        <div className="section-heading">
                            <div>
                                <p className="section-label">
                                    DOCUMENT
                                </p>

                                <h2>{data.filename}</h2>
                            </div>
                        </div>

                        <div className="stats-grid">

                            <div className="stat-card">
                                <span>Pages</span>

                                <strong>
                                    {data.page_count}
                                </strong>
                            </div>

                            <div className="stat-card">
                                <span>Words</span>

                                <strong>
                                    {data.total_words.toLocaleString()}
                                </strong>
                            </div>

                            <div className="stat-card">
                                <span>Characters</span>

                                <strong>
                                    {data.total_characters.toLocaleString()}
                                </strong>
                            </div>

                        </div>

                    </section>


                    {/* Words per page visualization */}

                    <section className="page-density">

                        <div className="section-heading">

                            <div>
                                <p className="section-label">
                                    DOCUMENT STRUCTURE
                                </p>

                                <h2>Words per Page</h2>
                            </div>

                        </div>

                        <div className="density-card">

                            {data.pages.map((page) => {

                                const words = page.text
                                    .split(/\s+/)
                                    .filter(Boolean)
                                    .length;

                                const percentage =
                                    (words / maxWords) * 100;

                                return (
                                    <div
                                        className="density-row"
                                        key={page.page}
                                    >

                                        <div className="density-label">

                                            <span>
                                                Page {page.page}
                                            </span>

                                            <strong>
                                                {words}
                                            </strong>

                                        </div>

                                        <div className="density-track">

                                            <div
                                                className="density-bar"
                                                style={{
                                                    width: `${percentage}%`,
                                                }}
                                            />

                                        </div>

                                    </div>
                                );
                            })}

                        </div>

                    </section>


                    {/* Page analysis */}

                    <section className="page-analysis">

                        <div className="section-heading">

                            <div>
                                <p className="section-label">
                                    EXTRACTION
                                </p>

                                <h2>Page Analysis</h2>
                            </div>

                        </div>

                        <div className="table">

                            <div className="table-row table-heading">

                                <span>Page</span>
                                <span>Words</span>
                                <span>Characters</span>
                                <span>Status</span>

                            </div>

                            {data.pages.map((page) => {

                                const words = page.text
                                    .split(/\s+/)
                                    .filter(Boolean)
                                    .length;

                                const characters =
                                    page.text.length;

                                const textAvailable =
                                    page.text.trim().length > 0;

                                return (
                                    <div
                                        className="table-row"
                                        key={page.page}
                                    >

                                        <span>
                                            {page.page}
                                        </span>

                                        <span>
                                            {words.toLocaleString()}
                                        </span>

                                        <span>
                                            {characters.toLocaleString()}
                                        </span>

                                        <span
                                            className={
                                                textAvailable
                                                    ? "status-ok"
                                                    : "status-warning"
                                            }
                                        >
                                            {textAvailable
                                                ? "✓ Text available"
                                                : "⚠ No text"}
                                        </span>

                                    </div>
                                );
                            })}

                        </div>

                    </section>

                </>
            )}

        </main>
    );
}

export default PDFProcessing;