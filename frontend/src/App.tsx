import { useState } from "react";

import UploadPDF from "./pages/UploadPDF";
import Login from "./pages/Login";
import PDFProcessing from "./pages/PDFProcessing";
import ChunkVisualization from "./pages/ChunkVisualization";
import Home from "./pages/Home";
import Visualization from "./pages/Visualization";

function App() {
    const [loggedIn, setLoggedIn] = useState(
        Boolean(localStorage.getItem("access_token"))
    );

    const [page, setPage] = useState<
        | "home"
        | "upload"
        | "processing"
        | "chunks"
        | "visualization"
    >("home");

    if (!loggedIn) {
        return (
            <Login
                onLogin={() => setLoggedIn(true)}
            />
        );
    }

    return (
        <div className="app">

            {/* NAVIGATION */}

            <nav
                style={{
                    padding: "14px 48px",
                    background: "#ffffff",
                    borderBottom: "1px solid #ebe7f0",
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                }}
            >

                {/* LOGO */}

                <button
                    onClick={() => setPage("home")}
                    style={{
                        border: "none",
                        background: "none",
                        cursor: "pointer",
                        fontWeight: 900,
                        fontSize: "17px",
                        color: "#292638",
                        letterSpacing: "0.04em",
                        padding: 0,
                    }}
                >
                    RAGVIZ
                </button>

                {/* HOME */}

                <button
                    onClick={() => setPage("home")}
                    style={{
                        marginLeft: "20px",
                        padding: "9px 14px",
                        borderRadius: "9px",
                        border: "1px solid #e1dce8",
                        background:
                            page === "home"
                                ? "#f1eeff"
                                : "#ffffff",
                        color:
                            page === "home"
                                ? "#6758d8"
                                : "#777181",
                        cursor: "pointer",
                        fontWeight: 600,
                    }}
                >
                    Home
                </button>

                {/* UPLOAD */}

                <button
                    onClick={() => setPage("upload")}
                    style={{
                        padding: "9px 14px",
                        borderRadius: "9px",
                        border: "1px solid #e1dce8",
                        background:
                            page === "upload"
                                ? "#fff4eb"
                                : "#ffffff",
                        color:
                            page === "upload"
                                ? "#a9633b"
                                : "#777181",
                        cursor: "pointer",
                        fontWeight: 600,
                    }}
                >
                    Upload
                </button>

                {/* VISUALIZATION */}

                <button
                    onClick={() =>
                        setPage("visualization")
                    }
                    style={{
                        padding: "9px 14px",
                        borderRadius: "9px",
                        border: "1px solid #e1dce8",
                        background:
                            page === "visualization"
                                ? "#f1eeff"
                                : "#ffffff",
                        color:
                            page === "visualization"
                                ? "#6758d8"
                                : "#777181",
                        cursor: "pointer",
                        fontWeight: 600,
                    }}
                >
                    Visualize RAG
                </button>

                {/* PDF PROCESSING */}

                <button
                    onClick={() =>
                        setPage("processing")
                    }
                    style={{
                        padding: "9px 14px",
                        borderRadius: "9px",
                        border: "1px solid #e1dce8",
                        background:
                            page === "processing"
                                ? "#eefaf7"
                                : "#ffffff",
                        color:
                            page === "processing"
                                ? "#278d73"
                                : "#777181",
                        cursor: "pointer",
                        fontWeight: 600,
                    }}
                >
                    PDF Processing
                </button>

                {/* CHUNKS */}

                <button
                    onClick={() => setPage("chunks")}
                    style={{
                        padding: "9px 14px",
                        borderRadius: "9px",
                        border: "1px solid #e1dce8",
                        background:
                            page === "chunks"
                                ? "#fff0f7"
                                : "#ffffff",
                        color:
                            page === "chunks"
                                ? "#b85d90"
                                : "#777181",
                        cursor: "pointer",
                        fontWeight: 600,
                    }}
                >
                    Chunks
                </button>

                {/* LOGOUT */}

                <button
                    onClick={() => {
                        localStorage.removeItem(
                            "access_token"
                        );

                        setLoggedIn(false);
                    }}
                    style={{
                        marginLeft: "auto",
                        padding: "9px 14px",
                        borderRadius: "9px",
                        border: "1px solid #e1dce8",
                        background: "#ffffff",
                        color: "#777181",
                        cursor: "pointer",
                    }}
                >
                    Logout
                </button>

            </nav>

            {/* HOME */}

            {page === "home" && (
                <Home
                    onNavigate={(nextPage) => {
                        if (
                            nextPage === "upload"
                        ) {
                            setPage("upload");
                        }

                        if (
                            nextPage ===
                            "visualization"
                        ) {
                            setPage("visualization");
                        }
                    }}
                />
            )}

            {/* UPLOAD */}

            {page === "upload" && (
                <UploadPDF />
            )}

            {/* PDF PROCESSING */}

            {page === "processing" && (
                <PDFProcessing />
            )}

            {/* CHUNKS */}

            {page === "chunks" && (
                <ChunkVisualization />
            )}

            {/* VISUALIZATION WORKSPACE */}

            {page === "visualization" && (
                <Visualization />
            )}

        </div>
    );
}

export default App;