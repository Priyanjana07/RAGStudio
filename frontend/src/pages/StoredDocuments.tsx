import { useEffect, useState } from "react";

import {
    ArrowRight,
    FileText,
    Plus,
    Search,
    Trash2,
} from "lucide-react";

import "./StoredDocuments.css";

interface Document {
    id: number;
    filename: string;
    file_path: string;
    user_id: number;
}

interface StoredDocumentsProps {
    onNavigate?: (
        page: "upload" | "visualization"
    ) => void;
}

function StoredDocuments({
    onNavigate,
}: StoredDocumentsProps) {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [search, setSearch] = useState("");
    const [deletingId, setDeletingId] = useState<number | null>(null);

    useEffect(() => {
        fetchDocuments();
    }, []);

    const fetchDocuments = async () => {
        try {
            const token =
                localStorage.getItem("access_token");

            const response = await fetch(
                "http://127.0.0.1:8000/documents",
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Failed to fetch documents: ${response.status}`
                );
            }

            const data = await response.json();

            setDocuments(data.documents);
        } catch (err) {
            console.error(
                "Error loading documents:",
                err
            );

            setError(
                "Could not load your documents."
            );
        } finally {
            setLoading(false);
        }
    };

    const deleteDocument = async (
        document: Document
    ) => {
        const confirmed = window.confirm(
            `Are you sure you want to delete "${document.filename}"?`
        );

        if (!confirmed) {
            return;
        }

        try {
            setDeletingId(document.id);

            const token =
                localStorage.getItem("access_token");

            const response = await fetch(
                `http://127.0.0.1:8000/documents/${document.id}`,
                {
                    method: "DELETE",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Failed to delete document: ${response.status}`
                );
            }

            setDocuments((currentDocuments) =>
                currentDocuments.filter(
                    (item) =>
                        item.id !== document.id
                )
            );
        } catch (err) {
            console.error(
                "Error deleting document:",
                err
            );

            alert(
                "Could not delete the document."
            );
        } finally {
            setDeletingId(null);
        }
    };

    const filteredDocuments =
        documents.filter((document) =>
            document.filename
                .toLowerCase()
                .includes(search.toLowerCase())
        );

    return (
        <main className="stored-page">
            <section className="stored-header">
                <div>
                    <div className="stored-eyebrow">
                        <FileText size={13} />
                        YOUR DOCUMENT LIBRARY
                    </div>

                    <h1>
                        Stored
                        <span> Documents</span>
                    </h1>

                    <p>
                        Access the PDFs you've uploaded
                        and continue exploring them through
                        the RAG pipeline.
                    </p>
                </div>

                <button
                    className="stored-upload-button"
                    onClick={() =>
                        onNavigate?.("upload")
                    }
                >
                    <Plus size={18} />
                    Upload document
                </button>
            </section>

            {!loading &&
                !error &&
                documents.length > 0 && (
                    <section className="stored-toolbar">
                        <div className="stored-count">
                            <strong>
                                {documents.length}
                            </strong>

                            <span>
                                {documents.length === 1
                                    ? "document"
                                    : "documents"}{" "}
                                stored
                            </span>
                        </div>

                        <div className="stored-search">
                            <Search size={17} />

                            <input
                                type="text"
                                placeholder="Search documents..."
                                value={search}
                                onChange={(event) =>
                                    setSearch(
                                        event.target.value
                                    )
                                }
                            />
                        </div>
                    </section>
                )}

            {loading && (
                <div className="stored-state">
                    <div className="stored-loader" />

                    <p>
                        Loading your documents...
                    </p>
                </div>
            )}

            {error && (
                <div className="stored-state stored-error">
                    <FileText size={30} />

                    <h3>
                        Couldn't load your documents
                    </h3>

                    <p>{error}</p>
                </div>
            )}

            {!loading &&
                !error &&
                documents.length === 0 && (
                    <div className="stored-empty">
                        <div className="empty-icon">
                            <FileText size={30} />
                        </div>

                        <h2>
                            Your library is empty
                        </h2>

                        <p>
                            Upload your first PDF to start
                            exploring the RAG pipeline.
                        </p>

                        <button
                            onClick={() =>
                                onNavigate?.("upload")
                            }
                        >
                            <Plus size={17} />
                            Upload your first document
                            <ArrowRight size={17} />
                        </button>
                    </div>
                )}

            {!loading &&
                !error &&
                filteredDocuments.length > 0 && (
                    <section className="stored-grid">
                        {filteredDocuments.map(
                            (document) => (
                                <article
                                    className="document-card"
                                    key={document.id}
                                >
                                    <div className="document-card-top">
                                        <div className="pdf-icon">
                                            <FileText
                                                size={25}
                                            />
                                        </div>

                                        <span className="document-type">
                                            PDF
                                        </span>
                                    </div>

                                    <div className="document-info">
                                        <h2
                                            title={
                                                document.filename
                                            }
                                        >
                                            {document.filename}
                                        </h2>

                                        <p>
                                            Document #
                                            {document.id}
                                        </p>
                                    </div>

                                    <div className="document-card-bottom">
                                        <span>
                                            Ready to explore
                                        </span>

                                        <div className="document-actions">
                                            <button
                                                className="delete-document-button"
                                                onClick={() =>
                                                    deleteDocument(
                                                        document
                                                    )
                                                }
                                                disabled={
                                                    deletingId ===
                                                    document.id
                                                }
                                                title="Delete document"
                                            >
                                                <Trash2
                                                    size={15}
                                                />

                                                {deletingId ===
                                                document.id
                                                    ? "Deleting..."
                                                    : "Delete"}
                                            </button>

                                            <button
                                                className="explore-document-button"
                                                onClick={() =>
                                                    onNavigate?.(
                                                        "visualization"
                                                    )
                                                }
                                            >
                                                Explore

                                                <ArrowRight
                                                    size={16}
                                                />
                                            </button>
                                        </div>
                                    </div>
                                </article>
                            )
                        )}
                    </section>
                )}

            {!loading &&
                !error &&
                documents.length > 0 &&
                filteredDocuments.length === 0 && (
                    <div className="stored-no-results">
                        <Search size={25} />

                        <h3>
                            No documents found
                        </h3>

                        <p>
                            Try a different search term.
                        </p>
                    </div>
                )}
        </main>
    );
}

export default StoredDocuments;