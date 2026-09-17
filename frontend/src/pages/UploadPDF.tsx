import { useRef, useState } from "react";
import api from "../services/api";
import "./UploadPDF.css";

import {
    CheckCircle2,
    FileText,
    Sparkles,
    UploadCloud,
    X,
} from "lucide-react";

interface UploadResponse {
    message: string;
    document_id: number;
    filename: string;
    user_id: number;
}

interface UploadPDFProps {
    onUploaded?: (documentId: number, filename: string) => void;
}

function UploadPDF({ onUploaded }: UploadPDFProps) {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState("");
    const [error, setError] = useState("");
    const [dragging, setDragging] = useState(false);

    const inputRef = useRef<HTMLInputElement | null>(null);

    const handleFile = (selectedFile: File | null) => {
        if (!selectedFile) {
            return;
        }

        setSuccess("");
        setError("");

        if (
            selectedFile.type !== "application/pdf" &&
            !selectedFile.name.toLowerCase().endsWith(".pdf")
        ) {
            setFile(null);
            setError("Only PDF files are allowed.");
            return;
        }

        setFile(selectedFile);
    };

    const handleUpload = async () => {
        if (!file) {
            setError("Please choose a PDF first.");
            return;
        }

        setLoading(true);
        setError("");
        setSuccess("");

        try {
            const formData = new FormData();
            formData.append("file", file);

            const response =
                await api.post<UploadResponse>(
                    "/upload",
                    formData
                );

            setSuccess(
                `${response.data.filename} uploaded successfully.`
            );

            onUploaded?.(
                response.data.document_id,
                response.data.filename
            );
        } catch (err: any) {
            console.error(err);

            setError(
                err.response?.data?.detail ||
                    "Failed to upload PDF."
            );
        } finally {
            setLoading(false);
        }
    };

    const clearFile = () => {
        setFile(null);
        setError("");
        setSuccess("");

        if (inputRef.current) {
            inputRef.current.value = "";
        }
    };

    return (
        <main className="upload-page">

            {/* HERO */}

            <section className="upload-hero">

                <div className="upload-badge">
                    DATA INGESTION
                </div>

                <h1>
                    Give your RAG pipeline
                    <span> something to explore.</span>
                </h1>

                <p>
                    Upload a PDF and watch RAGViz transform
                    it from raw document to chunks, embeddings,
                    retrieval, and grounded answers.
                </p>

            </section>

            {/* UPLOAD AREA */}

            <section className="upload-wrapper">

                <div
                    className={`drop-zone ${
                        dragging ? "is-dragging" : ""
                    } ${file ? "has-file" : ""}`}
                    onDragOver={(e) => {
                        e.preventDefault();
                        setDragging(true);
                    }}
                    onDragLeave={() =>
                        setDragging(false)
                    }
                    onDrop={(e) => {
                        e.preventDefault();
                        setDragging(false);

                        const droppedFile =
                            e.dataTransfer.files?.[0] ||
                            null;

                        handleFile(droppedFile);
                    }}
                    onClick={() => {
                        if (!file) {
                            inputRef.current?.click();
                        }
                    }}
                >

                    <input
                        ref={inputRef}
                        type="file"
                        accept=".pdf,application/pdf"
                        hidden
                        onChange={(e) => {
                            handleFile(
                                e.target.files?.[0] ||
                                    null
                            );
                        }}
                    />

                    {!file ? (
                        <>
                            <div className="upload-visual">
                                <UploadCloud size={30} />
                            </div>

                            <h2>
                                Drop your PDF here
                            </h2>

                            <p className="drop-description">
                                or choose a document from your
                                computer
                            </p>

                            <button
                                type="button"
                                className="choose-file-button"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    inputRef.current?.click();
                                }}
                            >
                                Choose PDF
                            </button>

                            <div className="upload-hint">
                                PDF files only
                            </div>
                        </>
                    ) : (
                        <div className="selected-file-view">

                            <div className="file-icon">
                                <FileText size={27} />
                            </div>

                            <div className="selected-file-info">
                                <span>
                                    Selected document
                                </span>

                                <strong>
                                    {file.name}
                                </strong>

                                <small>
                                    {(
                                        file.size /
                                        (1024 * 1024)
                                    ).toFixed(2)}{" "}
                                    MB
                                </small>
                            </div>

                            <button
                                type="button"
                                className="remove-file-button"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    clearFile();
                                }}
                            >
                                <X size={17} />
                            </button>

                        </div>
                    )}

                </div>

                {/* ACTION */}

                <button
                    className="upload-submit"
                    disabled={!file || loading}
                    onClick={handleUpload}
                >
                    {loading ? (
                        <>
                            <span className="button-spinner" />
                            Uploading...
                        </>
                    ) : (
                        <>
                            Upload Document
                            <UploadCloud size={17} />
                        </>
                    )}
                </button>

                {/* SUCCESS */}

                {success && (
                    <div className="upload-result success-result">

                        <div className="result-icon">
                            <CheckCircle2 size={19} />
                        </div>

                        <div>
                            <strong>
                                Document uploaded
                            </strong>

                            <span>
                                {success}
                            </span>
                        </div>

                    </div>
                )}

                {/* ERROR */}

                {error && (
                    <div className="upload-result error-result">

                        <div>
                            <strong>
                                Upload failed
                            </strong>

                            <span>
                                {error}
                            </span>
                        </div>

                    </div>
                )}

            </section>

            {/* PIPELINE PREVIEW */}

            <section className="upload-pipeline">

                <div className="pipeline-intro">
                    <span>
                        WHAT HAPPENS NEXT
                    </span>

                    <h2>
                        Your document becomes a RAG pipeline
                    </h2>
                </div>

                <div className="pipeline-preview">

                    <div className="pipeline-node node-orange">
                        <FileText size={18} />
                        <span>PDF</span>
                    </div>

                    <div className="pipeline-arrow">
                        →
                    </div>

                    <div className="pipeline-node node-violet">
                        <span>CHUNKS</span>
                    </div>

                    <div className="pipeline-arrow">
                        →
                    </div>

                    <div className="pipeline-node node-teal">
                        <span>VECTORS</span>
                    </div>

                    <div className="pipeline-arrow">
                        →
                    </div>

                    <div className="pipeline-node node-pink">
                        <span>RETRIEVAL</span>
                    </div>

                    <div className="pipeline-arrow">
                        →
                    </div>

                    <div className="pipeline-node node-gold">
                        <Sparkles size={18} />
                        <span>ANSWER</span>
                    </div>

                </div>

            </section>

        </main>
    );
}

export default UploadPDF;