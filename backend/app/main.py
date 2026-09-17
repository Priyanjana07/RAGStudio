# pyright: ignore
from fastapi import FastAPI, UploadFile, File, HTTPException  # type: ignore
from backend.app.services.pdf_service import extract_text
import time, uuid
from pathlib import Path
import shutil
from backend.app.services.vector_store import delete_document_embeddings
from chromadb.api.types import Metadata
from .database import get_db
from . import models
from .schemas import UserCreate,UserLogin
from fastapi import Depends
from sqlalchemy.orm import Session
from backend.app.services.reranker_service import rerank
from backend.app.services.retrieval_pipeline import (
    hybrid_rerank_search
)
from fastapi.middleware.cors import CORSMiddleware
from backend.app.services.retrieval_evaluation_service import vector_search
from backend.app.services.bm25_service import bm25_search
from backend.app.services.vector_store import get_embedding_collection
from backend.app.services.benchmark_aggregation_service import (
    aggregate_benchmark_results
)
from backend.app.services.retrieval_evaluation_service import (
    evaluate_retrieval_strategies, 
    run_retrieval_benchmark

)

from backend.app.services.evaluation_service import (
    calculate_overall_score,
    evaluate_answer,
    calculate_answer_overlap
)
from backend.app.services.dimensionality_service import (
    
    generate_visualization,
    get_document_embeddings,
    reduce_embeddings,
    reduce_embeddings_pca
)
from backend.app.services.bm25_service import bm25_search, hybrid_search, reciprocal_rank_fusion
from backend.app.services.jwt_service import create_access_token
from backend.app.services.auth_service import hash_password, verify_password
from backend.app.services.auth_dependency import get_current_user
from backend.app.services.chunk_service import fixed_chunking, recursive_chunking, token_chunking
from backend.app.services.embedding_service import generate_embedding, generate_embeddings, get_model
from backend.app.services.vector_store import (
    store_chunks,
    collection,
    get_embedding_collection,
    client,
    get_experiment_collection
)
from backend.app.services.retrieval_service import search_chunks
from backend.app.services.llmservice import generate_answer
from backend.app.services.context_service import build_context


app = FastAPI(title="RAGViz API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Upload_dir = Path("uploads") #Create a Python Path object representing a folder called uploads


Upload_dir.mkdir(exist_ok=True) #Create the uploads folder.


 #The function immediately below me handles POST requests to /upload.
 
@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided"
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Create a unique filename for the physical file
    unique_filename = (
        f"{uuid.uuid4().hex}.pdf"
    )

    file_path = Upload_dir / unique_filename

    # Save the uploaded PDF
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Store the original filename in the database
    document = models.Document(
        filename=file.filename,
        file_path=str(file_path),
        user_id=current_user.id
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "message": "PDF uploaded successfully",
        "document_id": document.id,
        "filename": document.filename,
        "user_id": document.user_id
    }

@app.get("/documents")
def get_documents(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    documents = db.query(models.Document).filter(
        models.Document.user_id == current_user.id
    ).all()

    return {
        "documents": [
            {
                "id": document.id,
                "filename": document.filename,
                "file_path": document.file_path,
                "user_id": document.user_id
            }
            for document in documents
        ]
    }
# -------------------------
# DELETE /documents/{filename}
# -------------------------

@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Delete embeddings from ChromaDB
    deleted_embeddings = delete_document_embeddings(
        document_id
    )

    # Delete the physical PDF
    file_path = Path(document.file_path)  # type: ignore

    if file_path.exists():
        file_path.unlink()

    # Delete PostgreSQL document
    # Its chunks are deleted through the relationship cascade
    db.delete(document)
    db.commit()

    return {
        "message": "Document deleted successfully",
        "document_id": document_id,
        "deleted_embeddings": deleted_embeddings
    }

@app.post("/documents/{filename}/extract")
def extract_document(
    filename: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(
        models.Document.filename == filename,
        models.Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    pdf_path = Path(document.file_path) #type:ignore

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF file not found"
        )

    # 1. PDF processing
    pages = extract_text(pdf_path)

    # 2. Calculate statistics
    total_characters = sum(
        len(page["text"])
        for page in pages
    )

    total_words = sum(
        len(page["text"].split())
        for page in pages
    )

    # 3. Page-level processing information
    processed_pages = []

    for page in pages:
        processed_pages.append({
            "page_number": page["page"],
            "characters": len(page["text"]),
            "words": len(page["text"].split()),
            "text_available": bool(page["text"].strip())
        })

    return {
        "filename": filename,

        # Existing information
        "page_count": len(pages),
        "total_characters": total_characters,
        "total_words": total_words,
        "pages": pages,

        # Processing visualization information
        "processing": {
            "status": "completed",

            "stages": [
                {
                    "name": "PDF Upload",
                    "status": "completed"
                },
                {
                    "name": "PDF Loading",
                    "status": "completed"
                },
                {
                    "name": "Text Extraction",
                    "status": "completed"
                },
                {
                    "name": "Page Analysis",
                    "status": "completed"
                }
            ],

            "statistics": {
                "pages": len(pages),
                "characters": total_characters,
                "words": total_words
            },

            "page_analysis": processed_pages
        }
    }

@app.get("/documents/{filename}/preview")
def preview_document(
    filename: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find document belonging to current user
    document = db.query(models.Document).filter(
        models.Document.filename == filename,
        models.Document.user_id == current_user.id
    ).first()

    # Document doesn't exist or doesn't belong to user
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Get PDF path from database
    pdf_path = Path(document.file_path) # type: ignore

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF file not found"
        )

    # Extract text
    pages = extract_text(pdf_path)

    # Check whether PDF has extractable text
    has_any_text = any(
        page["has_text"]
        for page in pages
    )

    if not has_any_text:
        raise HTTPException(
            status_code=422,
            detail="This PDF contains no extractable text. It may be a scanned document."
        )

    return {
        "filename": filename,
        "page_count": len(pages),
        "preview": pages[:3]
    }

@app.post("/test-user")
def create_test_user(
    db: Session = Depends(get_db)
):
    user = models.User(
        email="test2@example.com",
        password_hash="temporary"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email
    }

@app.post("/auth/register")
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # 1. Check if email already exists
    existing_user = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # 2. Hash the password
    hashed_password = hash_password(user_data.password)

    # 3. Create a User object
    user = models.User(
        email=user_data.email,
        password_hash=hashed_password
    )

    # 4. Add it to the database session
    db.add(user)

    # 5. Commit the INSERT
    db.commit()

    # 6. Get the generated ID
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email
    }

@app.post("/auth/login")
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    # 1. Find user
    user = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()

    # 2. User doesn't exist
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # 3. Verify password
    if not verify_password(
        user_data.password,
        user.password_hash # type: ignore
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # 4. Create JWTP
    access_token = create_access_token(user.id) # type: ignore

    # 5. Return token
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/documents/{filename}/chunks")
def create_chunks(
    filename: str,
    strategy: str = "recursive",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("========== CREATE CHUNKS ==========")
    print("filename:", repr(filename))
    print("current_user.id:", current_user.id)
    print("current_user.email:", current_user.email)

    # 1. Find document belonging to current user
    document = db.query(models.Document).filter(
        models.Document.filename == filename,
        models.Document.user_id == current_user.id
    ).first()

    print("document:", document)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # 2. Check PDF exists
    pdf_path = Path(document.file_path) # type: ignore

    print("PDF path:", pdf_path)
    print("PDF exists:", pdf_path.exists())

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF file not found"
        )

    # 3. Extract PDF text page-by-page
    pages = extract_text(pdf_path)

    # 4. Create chunks while preserving page number
    all_chunks = []

    for page in pages:

        page_text = page["text"]

        if not page_text.strip():
            continue

        # Select chunking strategy
        if strategy == "fixed":

            page_chunks = fixed_chunking(
                page_text,
                chunk_size=500,
                overlap=50
            )

        elif strategy == "recursive":

            page_chunks = recursive_chunking(
                page_text,
                chunk_size=500,
                overlap=50
            )

        elif strategy == "token":

            page_chunks = token_chunking(
                page_text,
                chunk_size=200,
                overlap=20
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid chunking strategy. "
                    "Use fixed, recursive, or token."
                )
            )

        # Store text + page number together
        for chunk in page_chunks:

            all_chunks.append({
                "text": chunk,
                "page_number": page["page"]
            })

    # Check if chunks were created
    if not all_chunks:
        raise HTTPException(
            status_code=422,
            detail="No text chunks were created"
        )

    # 5. Remove existing chunks for this document
    db.query(models.Chunk).filter(
        models.Chunk.document_id == document.id
    ).delete()

    # 6. Store chunks in PostgreSQL
    chunk_records = []

    for i, chunk_data in enumerate(all_chunks):

        chunk_record = models.Chunk(
            document_id=document.id,
            text=chunk_data["text"],
            chunk_number=i,
            page_number=chunk_data["page_number"]
        )

        db.add(chunk_record)
        chunk_records.append(chunk_record)

    # Save to database
    db.commit()

    # 7. Refresh IDs
    for chunk in chunk_records:
        db.refresh(chunk)

    # 8. Return chunks
    return {
        "filename": filename,
        "document_id": document.id,
        "strategy": strategy,
        "chunk_count": len(chunk_records),
        "chunks": [
            {
                "chunk_id": chunk.id,
                "chunk_number": chunk.chunk_number,
                "page_number": chunk.page_number,
                "text": chunk.text
            }
            for chunk in chunk_records
        ]
    }
@app.post("/documents/{filename}/embeddings")
def create_embeddings(
    filename: str,
    model_name: str = "minilm",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Find document belonging to current user
    document = db.query(models.Document).filter(
        models.Document.filename == filename,
        models.Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # 2. Get chunks from PostgreSQL
    chunks = db.query(models.Chunk).filter(
        models.Chunk.document_id == document.id
    ).order_by(
        models.Chunk.chunk_number
    ).all()

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail=(
                "No chunks found for this document. "
                "Create chunks first."
            )
        )

    # 3. Extract chunk text
    chunk_texts = [
        chunk.text
        for chunk in chunks
    ]

    # 4. Generate embeddings
    embeddings = [
        generate_embedding(
            text,
            model_name=model_name
        )
        for text in chunk_texts
    ]

    # 5. Metadata
    metadatas: list[Metadata] = [
        {
            "document_id": document.id,
            "chunk_index": chunk.chunk_number,
            "page_number": chunk.page_number
        }
        for chunk in chunks
    ]

    # --------------------------------------------------
    # 6. Store in the existing generic collection
    #    Used by the normal RAG pipeline
    # --------------------------------------------------

    stored_count = store_chunks(
        document_id=document.id,
        chunks=chunk_texts,
        embeddings=embeddings,
        metadatas=metadatas # type: ignore # pyright: ignore[reportArgumentType]
    )

    # --------------------------------------------------
    # 7. Store in model-specific collection
    #    Used by visualization and embedding experiments
    # --------------------------------------------------

    model_collection = get_embedding_collection(
        model_name
    )

    visualization_ids = [
        f"experiment_{document.id}_{model_name}_{i}"
        for i in range(len(chunks))
    ]

    model_collection.upsert(
        ids=visualization_ids,
        documents=chunk_texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    # 8. Return result
    return {
        "message": (
            "Embeddings created and stored successfully"
        ),
        "document_id": document.id,
        "filename": filename,
        "model_name": model_name,
        "chunk_count": stored_count,
        "embedding_dimension": len(embeddings[0])
    }

@app.post("/documents/{document_id}/search")
def search_document(
    document_id: int,
    query: str,
    model_name: str = "minilm",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    results = search_chunks(
        query=query,
        document_id=document_id,
        top_k=3,
        model_name=model_name
    )

    return {
        "query": query,
        "document_id": document_id,
        "model_name": model_name,
        "results": results
    }

@app.post("/documents/{document_id}/ask")
def ask_document(
    document_id: int,
    query: str,
    retrieval_strategy: str = "hybrid",
    model_name: str = "minilm",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_start = time.perf_counter()

    # 1. Check document ownership
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # 2. Validate retrieval strategy
    valid_strategies = [
        "vector",
        "bm25",
        "hybrid",
        "hybrid_reranker"
    ]

    if retrieval_strategy not in valid_strategies:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid retrieval strategy. "
                "Choose from: vector, bm25, hybrid, hybrid_reranker"
            )
        )

    # 3. Retrieval
    retrieval_start = time.perf_counter()

    if retrieval_strategy == "vector":

        results = vector_search(
            query=query,
            document_id=document_id,
            top_k=3,
            model_name=model_name
        )

    elif retrieval_strategy == "bm25":

        collection = get_embedding_collection(
            model_name
        )

        collection_results = collection.get(
            where={
                "document_id": document_id
            },
            include=[
                "documents",
                "metadatas"
            ]
        )

        documents = []

        for text, metadata in zip(
            collection_results["documents"], # type: ignore
            collection_results["metadatas"] # pyright: ignore[reportArgumentType] # pyright: ignore[reportArgumentType]
        ):
            documents.append({
                "text": text,
                "chunk_number": metadata.get(
                    "chunk_index",
                    metadata.get("chunk_number")
                ),
                "page_number": metadata.get(
                    "page_number"
                )
            })

        results = bm25_search(
            query=query,
            documents=documents,
            top_k=3
        )

    elif retrieval_strategy == "hybrid":

        # Hybrid = BM25 + Vector + RRF

        collection = get_embedding_collection(
            model_name
        )

        collection_results = collection.get(
            where={
                "document_id": document_id
            },
            include=[
                "documents",
                "metadatas"
            ]
        )

        documents = []

        for text, metadata in zip(
            collection_results["documents"], # type: ignore
            collection_results["metadatas"] # type: ignore
        ):
            documents.append({
                "text": text,
                "chunk_number": metadata.get(
                    "chunk_index",
                    metadata.get("chunk_number")
                ),
                "page_number": metadata.get(
                    "page_number"
                )
            })

        # BM25 candidates
        bm25_results = bm25_search(
            query=query,
            documents=documents,
            top_k=10
        )

        # Vector candidates
        vector_results = vector_search(
            query=query,
            document_id=document_id,
            top_k=10,
            model_name=model_name
        )

        from backend.app.services.bm25_service import (
            reciprocal_rank_fusion
        )

        results = reciprocal_rank_fusion(
            result_lists=[
                bm25_results,
                vector_results
            ],
            top_k=3
        )

    else:

        # Hybrid + reranker

        results = hybrid_rerank_search(
            query=query,
            document_id=document_id,
            top_k=3,
            candidate_k=10,
            model_name=model_name
        )

    retrieval_time = (
        time.perf_counter()
        - retrieval_start
    )

    # 4. No results
    if not results:

        total_time = (
            time.perf_counter()
            - total_start
        )

        return {
            "question": query,
            "document_id": document_id,
            "answer": (
                "I couldn't find relevant context "
                "in the document."
            ),
            "sources": [],

            "metrics": {
                "retrieval_latency_ms": round(
                    retrieval_time * 1000,
                    2
                ),
                "total_latency_ms": round(
                    total_time * 1000,
                    2
                ),
                "chunks_retrieved": 0
            },

            "retrieval_metrics": {
                "retrieval_strategy":
                    retrieval_strategy,
                "top_k": 3,
                "retrieved_chunks": 0,
                "best_distance": None,
                "average_distance": None
            }
        }

    # 5. Build context
    context_start = time.perf_counter()

    context = build_context(results)

    context_time = (
        time.perf_counter()
        - context_start
    )

    # 6. Generate answer
    llm_start = time.perf_counter()

    answer = generate_answer(
        question=query,
        context=context
    )

    llm_time = (
        time.perf_counter()
        - llm_start
    )

    # 7. Sources
    sources = []

    for result in results:

        sources.append({
            "chunk_number": result.get(
                "chunk_number",
                result.get("chunk_index")
            ),

            "page_number": result.get(
                "page_number"
            ),

            "distance": result.get(
                "distance"
            ),

            "rerank_score": result.get(
                "rerank_score"
            ),

            "rrf_score": result.get(
                "rrf_score"
            ),

            "score": result.get(
                "score"
            ),

            "text": result.get(
                "text",
                ""
            )
        })

    # 8. Retrieval metrics
    distances = [
        result["distance"]
        for result in results
        if result.get("distance") is not None
    ]

    retrieval_metrics = {
        "retrieval_strategy":
            retrieval_strategy,

        "top_k": 3,

        "retrieved_chunks":
            len(results),

        "best_distance": (
            round(
                min(distances),
                4
            )
            if distances
            else None
        ),

        "average_distance": (
            round(
                sum(distances) /
                len(distances),
                4
            )
            if distances
            else None
        )
    }

    # 9. Total time
    total_time = (
        time.perf_counter()
        - total_start
    )

    # 10. Return
    return {
        "question": query,

        "document_id": document_id,

        "model_name": model_name,

        "answer": answer,

        "sources": sources,

        "metrics": {
            "retrieval_latency_ms": round(
                retrieval_time * 1000,
                2
            ),

            "context_latency_ms": round(
                context_time * 1000,
                2
            ),

            "llm_latency_ms": round(
                llm_time * 1000,
                2
            ),

            "total_latency_ms": round(
                total_time * 1000,
                2
            ),

            "chunks_retrieved":
                len(results)
        },

        "retrieval_metrics":
            retrieval_metrics
    }

@app.post("/documents/{document_id}/embedding-experiment")
def embedding_experiment(
    document_id: int,
    query: str,
    benchmark_runs: int = 3,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if benchmark_runs < 1 or benchmark_runs > 5:
        raise HTTPException(
            status_code=400,
            detail="benchmark_runs must be between 1 and 5"
        )

    # ==================================================
    # 1. CHECK DOCUMENT OWNERSHIP
    # ==================================================

    document = (
        db.query(models.Document)
        .filter(
            models.Document.id == document_id,
            models.Document.user_id == current_user.id
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # ==================================================
    # 2. CHECK PDF EXISTS
    # ==================================================

    pdf_path = Path(document.file_path)

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF file not found"
        )

    # ==================================================
    # 3. EXTRACT TEXT
    # ==================================================

    pages = extract_text(pdf_path)

    # ==================================================
    # 4. CREATE CHUNKS PAGE-WISE
    # ==================================================

    chunks = []

    for page in pages:

        page_text = page["text"]

        if not page_text.strip():
            continue

        page_chunks = recursive_chunking(
            page_text,
            chunk_size=500,
            overlap=50
        )

        for chunk_text in page_chunks:

            chunks.append({
                "text": chunk_text,
                "page_number": page["page"]
            })

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No chunks could be created"
        )

    chunk_texts = [
        chunk["text"]
        for chunk in chunks
    ]

    # ==================================================
    # 5. MODELS TO COMPARE
    # ==================================================

    embedding_models = [
        "minilm",
        "mpnet",
        "distilroberta"
    ]

    results = []

    # ==================================================
    # 6. RUN EACH EMBEDDING MODEL
    # ==================================================

    for model_name in embedding_models:

        # --------------------------------------------------
        # MODEL LOAD TIME
        # --------------------------------------------------

        load_start = time.perf_counter()

        get_model(model_name)

        load_end = time.perf_counter()

        model_load_latency_ms = (
            load_end - load_start
        ) * 1000

        # --------------------------------------------------
        # WARM UP
        # --------------------------------------------------

        generate_embeddings(
            chunk_texts[:min(2, len(chunk_texts))],
            model_name=model_name
        )

        # --------------------------------------------------
        # DOCUMENT EMBEDDING BENCHMARK
        # --------------------------------------------------

        embedding_times = []
        embeddings = None

        for _ in range(benchmark_runs):

            embedding_start = time.perf_counter()

            embeddings = generate_embeddings(
                chunk_texts,
                model_name=model_name
            )

            embedding_end = time.perf_counter()

            embedding_times.append(
                (embedding_end - embedding_start) * 1000
            )

        document_embedding_latency_ms = (
            sum(embedding_times)
            / len(embedding_times)
        )

        # --------------------------------------------------
        # MODEL-SPECIFIC CHROMA COLLECTION
        # --------------------------------------------------

        model_collection = get_embedding_collection(
            model_name
        )

        experiment_ids = [
            f"experiment_{document_id}_{model_name}_{i}"
            for i in range(len(chunks))
        ]

        metadatas = [
            {
                "document_id": document_id,
                "filename": document.filename,
                "chunk_number": i,
                "page_number": chunk["page_number"],
                "embedding_model": model_name
            }
            for i, chunk in enumerate(chunks)
        ]

        model_collection.upsert(
            ids=experiment_ids,

            documents=chunk_texts,

            embeddings=embeddings,

            metadatas=metadatas # type: ignore
        )

        # --------------------------------------------------
        # QUERY EMBEDDING BENCHMARK
        # --------------------------------------------------

        query_embedding_times = []
        query_embedding = None

        for _ in range(benchmark_runs):

            query_start = time.perf_counter()

            query_embedding = generate_embedding(
                query,
                model_name=model_name
            )

            query_end = time.perf_counter()

            query_embedding_times.append(
                (query_end - query_start) * 1000
            )

        query_embedding_latency_ms = (
            sum(query_embedding_times)
            / len(query_embedding_times)
        )

        # --------------------------------------------------
        # RETRIEVAL
        # --------------------------------------------------

        retrieval_start = time.perf_counter()

        search_result = model_collection.query(
            query_embeddings=[query_embedding], # type: ignore # type: ignore

            n_results=min(
                3,
                len(chunks)
            ),

            where={
                "document_id": document_id
            }
        )

        retrieval_end = time.perf_counter()

        retrieval_latency_ms = (
            retrieval_end - retrieval_start
        ) * 1000

        # --------------------------------------------------
        # RETRIEVED DATA
        # --------------------------------------------------

        retrieved_documents = (
            search_result["documents"][0]
        )

        retrieved_metadatas = (
            search_result["metadatas"][0]
        )

        distances = (
            search_result["distances"][0]
        )

        # --------------------------------------------------
        # BUILD RETRIEVED CHUNKS
        # --------------------------------------------------

        retrieved_chunks = []

        for i in range(len(retrieved_documents)):

            retrieved_chunks.append({

                "text": retrieved_documents[i],

                "page_number": retrieved_metadatas[i][
                    "page_number"
                ],

                "chunk_number": retrieved_metadatas[i].get("chunk_number",i),

                "distance": distances[i]
            })

        # --------------------------------------------------
        # BUILD CONTEXT
        # --------------------------------------------------

        context_start = time.perf_counter()

        context = build_context(
            retrieved_chunks
        )

        context_end = time.perf_counter()

        context_latency_ms = (
            context_end - context_start
        ) * 1000

        # --------------------------------------------------
        # GENERATE ANSWER
        # --------------------------------------------------

        llm_start = time.perf_counter()

        answer = generate_answer(
            question=query,
            context=context
        )

        llm_end = time.perf_counter()

        llm_latency_ms = (
            llm_end - llm_start
        ) * 1000

        # --------------------------------------------------
        # LLM EVALUATION
        # --------------------------------------------------

        answer_evaluation = evaluate_answer(
            question=query,
            context=context,
            answer=answer # type: ignore
        )

        # --------------------------------------------------
        # WEIGHTED ANSWER QUALITY
        # --------------------------------------------------

        answer_quality = (
            0.30 * answer_evaluation["relevance"]
            + 0.40 * answer_evaluation["faithfulness"]
            + 0.30 * answer_evaluation["completeness"]
        )

        # --------------------------------------------------
        # RETRIEVAL DISTANCE
        # --------------------------------------------------

        if distances:

            best_distance = min(distances)

            average_distance = (
                sum(distances)
                / len(distances)
            )

        else:

            best_distance = None
            average_distance = None

        # --------------------------------------------------
        # SAVE RESULT
        # --------------------------------------------------

        results.append({

            "model_name": model_name,

            "embedding_dimension": len(
                embeddings[0]
            ),

            "chunk_count": len(chunks),

            "model_load_latency_ms": round(
                model_load_latency_ms,
                2
            ),

            "document_embedding_latency_ms": round(
                document_embedding_latency_ms,
                2
            ),

            "query_embedding_latency_ms": round(
                query_embedding_latency_ms,
                2
            ),

            "retrieval_latency_ms": round(
                retrieval_latency_ms,
                2
            ),

            "context_latency_ms": round(
                context_latency_ms,
                2
            ),

            "llm_latency_ms": round(
                llm_latency_ms,
                2
            ),

            "best_distance": (
                round(best_distance, 4)
                if best_distance is not None
                else None
            ),

            "average_distance": (
                round(average_distance, 4)
                if average_distance is not None
                else None
            ),

            "answer_quality": round(
                answer_quality,
                4
            ),

            "answer_evaluation": answer_evaluation
        })

    # ==================================================
    # 7. REMOVE INVALID RESULTS
    # ==================================================

    valid_results = [
        result
        for result in results
        if result["best_distance"] is not None
    ]

    if not valid_results:

        raise HTTPException(
            status_code=422,
            detail="No valid experiment results"
        )

    # ==================================================
    # 8. DISTANCE RANGE
    # ==================================================

    distances = [
        result["best_distance"]
        for result in valid_results
    ]

    min_distance = min(distances)
    max_distance = max(distances)

    # ==================================================
    # 9. PIPELINE LATENCY
    # ==================================================

    pipeline_latencies = []

    for result in valid_results:

        pipeline_latency = (
            result["document_embedding_latency_ms"]
            + result["query_embedding_latency_ms"]
            + result["retrieval_latency_ms"]
            + result["context_latency_ms"]
            + result["llm_latency_ms"]
        )

        result["pipeline_latency_ms"] = round(
            pipeline_latency,
            2
        )

        pipeline_latencies.append(
            pipeline_latency
        )

    min_latency = min(pipeline_latencies)
    max_latency = max(pipeline_latencies)

    # ==================================================
    # 10. CALCULATE FINAL SCORES
    # ==================================================

    for result in valid_results:

        scoring = calculate_overall_score(

            answer_quality=result[
                "answer_quality"
            ],

            best_distance=result[
                "best_distance"
            ],

            latency_ms=result[
                "pipeline_latency_ms"
            ],

            min_distance=min_distance,

            max_distance=max_distance,

            min_latency=min_latency,

            max_latency=max_latency
        )

        result["retrieval_score"] = scoring[
            "retrieval_score"
        ]

        result["speed_score"] = scoring[
            "speed_score"
        ]

        result["overall_score"] = scoring[
            "overall_score"
        ]

        result[
            "embedding_throughput_chunks_per_sec"
        ] = round(

            len(chunks)
            / (
                result[
                    "document_embedding_latency_ms"
                ] / 1000
            ),

            2
        )

  # ==================================================
# 11. FIND BEST MODELS
# ==================================================

    best_model_result = max(
    valid_results,
    key=lambda x: x["overall_score"]
)

    best_quality_result = max(
    valid_results,
    key=lambda x: x["answer_quality"]
)

    best_speed_result = min(
    valid_results,
    key=lambda x: x["pipeline_latency_ms"]
)

    best_retrieval_result = max(
    valid_results,
    key=lambda x: x["retrieval_score"]
)

    # ==================================================
    # 12. RETURN RESULTS
    # ==================================================

    return {

    "document_id": document_id,

    "filename": document.filename,

    "query": query,

    "benchmark_runs": benchmark_runs,

    # Overall winner
    "best_model": best_model_result[
        "model_name"
    ],

    "best_overall_score": best_model_result[
        "overall_score"
    ],

    # Best answer quality
    "best_quality_model": best_quality_result[
        "model_name"
    ],

    "best_quality_score": best_quality_result[
        "answer_quality"
    ],

    # Fastest pipeline
    "best_speed_model": best_speed_result[
        "model_name"
    ],

    "best_speed_pipeline_latency_ms":
        best_speed_result[
            "pipeline_latency_ms"
        ],

    # Best retrieval
    "best_retrieval_model": best_retrieval_result[
        "model_name"
    ],

    "best_retrieval_score": best_retrieval_result[
        "retrieval_score"
    ],

    "comparison": valid_results
}

@app.post("/documents/{document_id}/retrieval-experiment")
def retrieval_experiment(
    document_id: int,
    query: str,
    benchmark_runs: int = 3,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # ==================================================
    # 0. VALIDATE BENCHMARK RUNS
    # ==================================================

    if benchmark_runs < 1 or benchmark_runs > 5:
        raise HTTPException(
            status_code=400,
            detail="benchmark_runs must be between 1 and 5"
        )

    # ==================================================
    # 1. CHECK DOCUMENT OWNERSHIP
    # ==================================================

    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # ==================================================
    # 2. TOP-K VALUES TO TEST
    # ==================================================

    top_k_values = [3, 5, 8]

    results = []

    # ==================================================
    # 3. GENERATE QUERY EMBEDDING ONCE
    # ==================================================

    query_embedding = generate_embedding(query)

    # ==================================================
    # 4. RUN EXPERIMENT
    # ==================================================

    for top_k in top_k_values:

        # ----------------------------------------------
        # Warm-up retrieval
        # ----------------------------------------------

        collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={
                "document_id": document_id
            }
        )

        # ----------------------------------------------
        # Benchmark retrieval
        # ----------------------------------------------

        retrieval_times = []
        retrieved_chunks = None

        for _ in range(benchmark_runs):

            retrieval_start = time.perf_counter()

            chroma_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={
                    "document_id": document_id
                }
            )

            retrieval_times.append(
                (time.perf_counter() - retrieval_start) * 1000
            )

            # Keep results from the final run
            retrieved_chunks = []

            documents = chroma_results["documents"][0]
            metadatas = chroma_results["metadatas"][0]
            distances = chroma_results["distances"][0]

            for i in range(len(documents)):

                if distances[i] > 1.3:
                    continue

                retrieved_chunks.append({
                    "text": documents[i],
                    "chunk_index": metadatas[i]["chunk_index"],
                    "page_number": metadatas[i].get("page_number"),
                    "distance": distances[i]
                })

        retrieval_latency_ms = round(
            sum(retrieval_times) / len(retrieval_times),
            2
        )

        # ----------------------------------------------
        # Handle no results
        # ----------------------------------------------

        if not retrieved_chunks:

            results.append({
                "top_k": top_k,
                "retrieved_chunks": 0,
                "retrieval_latency_ms": retrieval_latency_ms,
                "context_latency_ms": 0,
                "llm_latency_ms": 0,
                "best_distance": None,
                "average_distance": None,
                "answer_quality": 0,
                "answer_evaluation": {
                    "relevance": 0,
                    "faithfulness": 0,
                    "completeness": 0
                },
                "answer": None
            })

            continue

        # ----------------------------------------------
        # Distance metrics
        # ----------------------------------------------

        distances = [
            chunk["distance"]
            for chunk in retrieved_chunks
        ]

        best_distance = min(distances)

        average_distance = (
            sum(distances) / len(distances)
        )

        # ----------------------------------------------
        # Build context
        # ----------------------------------------------

        context_start = time.perf_counter()

        context = build_context(
            retrieved_chunks
        )

        context_latency_ms = round(
            (time.perf_counter() - context_start) * 1000,
            2
        )

        # ----------------------------------------------
        # Generate answer
        # ----------------------------------------------

        llm_start = time.perf_counter()

        answer = generate_answer(
            query,
            context
        )

        llm_latency_ms = round(
            (time.perf_counter() - llm_start) * 1000,
            2
        )

        # ----------------------------------------------
        # Evaluate answer
        # ----------------------------------------------

        evaluation = evaluate_answer(
            question=query,
            context=context,
            answer=answer
        )

        # ----------------------------------------------
        # Calculate answer quality
        # ----------------------------------------------

        answer_quality = (
            0.30 * evaluation["relevance"]
            + 0.40 * evaluation["faithfulness"]
            + 0.30 * evaluation["completeness"]
        )

        answer_quality = round(
            answer_quality,
            4
        )

        # ----------------------------------------------
        # Store result
        # ----------------------------------------------

        results.append({
            "top_k": top_k,

            "retrieved_chunks": len(
                retrieved_chunks
            ),

            "retrieval_latency_ms":
                retrieval_latency_ms,

            "context_latency_ms":
                context_latency_ms,

            "llm_latency_ms":
                llm_latency_ms,

            "best_distance":
                round(best_distance, 4),

            "average_distance":
                round(average_distance, 4),

            "answer_quality":
                answer_quality,

            "answer_evaluation":
                evaluation,

            "answer":
                answer
        })

    # ==================================================
    # 5. FIND BEST RESULTS
    # ==================================================

    valid_results = [
        result
        for result in results
        if result["retrieved_chunks"] > 0
    ]

    if not valid_results:
        raise HTTPException(
            status_code=404,
            detail="No relevant chunks found"
        )

    # Best quality
    best_quality_result = max(
        valid_results,
        key=lambda x: x["answer_quality"]
    )

    # Best retrieval speed
    best_speed_result = min(
        valid_results,
        key=lambda x: x["retrieval_latency_ms"]
    )

    # Best retrieval distance
    best_retrieval_result = min(
        valid_results,
        key=lambda x: x["best_distance"]
    )

    # ==================================================
    # 6. RETURN RESULTS
    # ==================================================

    return {
        "document_id": document_id,
        "filename": document.filename,
        "query": query,
        "benchmark_runs": benchmark_runs,

        "best_quality_top_k":
            best_quality_result["top_k"],

        "best_quality_score":
            best_quality_result["answer_quality"],

        "best_speed_top_k":
            best_speed_result["top_k"],

        "best_speed_retrieval_latency_ms":
            best_speed_result["retrieval_latency_ms"],

        "best_retrieval_top_k":
            best_retrieval_result["top_k"],

        "best_retrieval_distance":
            best_retrieval_result["best_distance"],

        "comparison": results
    }

@app.post("/documents/{document_id}/chunk-size-experiment")
def chunk_size_experiment(
    document_id: int,
    query: str,
    benchmark_runs: int = 3,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if benchmark_runs < 1 or benchmark_runs > 5:
        raise HTTPException(
            status_code=400,
            detail="benchmark_runs must be between 1 and 5"
        )

    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    chunk_sizes = [250, 500, 1000]
    results = []

    pdf_path = Path(document.file_path)
    pages = extract_text(pdf_path)

    for chunk_size in chunk_sizes:

        # -----------------------------
        # 1. CHUNK DOCUMENT
        # -----------------------------

        all_chunks = []

        for page in pages:
            page_text = page["text"]

            if not page_text.strip():
                continue

            page_chunks = recursive_chunking(
                page_text,
                chunk_size=chunk_size,
                overlap=50
            )

            for chunk in page_chunks:
                all_chunks.append({
                    "text": chunk,
                    "page_number": page["page"]
                })

        texts = [chunk["text"] for chunk in all_chunks]

        # -----------------------------
        # 2. GENERATE EMBEDDINGS
        # -----------------------------

        embedding_start = time.perf_counter()

        embeddings = generate_embeddings(
            texts,
            model_name="minilm"
        )

        embedding_latency_ms = round(
            (time.perf_counter() - embedding_start) * 1000,
            2
        )

        # -----------------------------
        # 3. STORE IN CHROMA
        # -----------------------------

        experiment_collection = client.get_or_create_collection(
            name=f"chunk_size_{document_id}_{chunk_size}"
        )

        ids = [
            f"{document_id}_{chunk_size}_{i}"
            for i in range(len(texts))
        ]

        metadatas = [
            {
                "document_id": document_id,
                "chunk_number": i,
                "page_number": all_chunks[i]["page_number"],
                "chunk_size": chunk_size
            }
            for i in range(len(texts))
        ]

        experiment_collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        # -----------------------------
        # 4. QUERY EMBEDDING
        # -----------------------------

        query_embedding = generate_embedding(
            query,
            model_name="minilm"
        )

        # -----------------------------
        # 5. RETRIEVAL
        # -----------------------------

        retrieval_times = []
        chroma_results = None

        for _ in range(benchmark_runs):

            retrieval_start = time.perf_counter()

            chroma_results = experiment_collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                where={
                    "document_id": document_id
                }
            )

            retrieval_times.append(
                (time.perf_counter() - retrieval_start) * 1000
            )

        retrieval_latency_ms = round(
            sum(retrieval_times) / len(retrieval_times),
            2
        )

        # -----------------------------
        # 6. PROCESS RESULTS
        # -----------------------------

        retrieved_chunks = []

        documents = chroma_results["documents"][0]
        metadatas = chroma_results["metadatas"][0]
        distances = chroma_results["distances"][0]

        for i in range(len(documents)):

            retrieved_chunks.append({
                "text": documents[i],
                "chunk_index": metadatas[i]["chunk_number"],
                "page_number": metadatas[i].get("page_number"),
                "distance": distances[i]
            })

        # -----------------------------
        # 7. DISTANCE METRICS
        # -----------------------------

        distance_values = [
            chunk["distance"]
            for chunk in retrieved_chunks
        ]

        best_distance = min(distance_values)
        average_distance = (
            sum(distance_values) / len(distance_values)
        )

        # -----------------------------
        # 8. BUILD CONTEXT
        # -----------------------------

        context_start = time.perf_counter()

        context = build_context(
            retrieved_chunks
        )

        context_latency_ms = round(
            (time.perf_counter() - context_start) * 1000,
            2
        )

        # -----------------------------
        # 9. GENERATE ANSWER
        # -----------------------------

        llm_start = time.perf_counter()

        answer = generate_answer(
            query,
            context
        )

        llm_latency_ms = round(
            (time.perf_counter() - llm_start) * 1000,
            2
        )

        # -----------------------------
        # 10. EVALUATE
        # -----------------------------

        evaluation = evaluate_answer(
            question=query,
            context=context,
            answer=answer
        )

        answer_quality = (
            0.30 * evaluation["relevance"]
            + 0.40 * evaluation["faithfulness"]
            + 0.30 * evaluation["completeness"]
        )

        answer_quality = round(
            answer_quality,
            4
        )

        # -----------------------------
        # 11. SAVE RESULT
        # -----------------------------

        results.append({
            "chunk_size": chunk_size,
            "overlap": 50,
            "chunk_count": len(all_chunks),
            "embedding_latency_ms": embedding_latency_ms,
            "retrieved_chunks": len(retrieved_chunks),
            "retrieval_latency_ms": retrieval_latency_ms,
            "context_latency_ms": context_latency_ms,
            "llm_latency_ms": llm_latency_ms,
            "best_distance": round(best_distance, 4),
            "average_distance": round(average_distance, 4),
            "answer_quality": answer_quality,
            "answer_evaluation": evaluation,
            "answer": answer
        })

    # -----------------------------
    # 12. WINNERS
    # -----------------------------

    best_quality = max(
        results,
        key=lambda x: x["answer_quality"]
    )

    best_retrieval = min(
        results,
        key=lambda x: x["best_distance"]
    )

    best_speed = min(
        results,
        key=lambda x: x["retrieval_latency_ms"]
    )

    return {
        "document_id": document_id,
        "filename": document.filename,
        "query": query,
        "benchmark_runs": benchmark_runs,

        "best_quality_chunk_size":
            best_quality["chunk_size"],

        "best_quality_score":
            best_quality["answer_quality"],

        "best_retrieval_chunk_size":
            best_retrieval["chunk_size"],

        "best_retrieval_distance":
            best_retrieval["best_distance"],

        "best_speed_chunk_size":
            best_speed["chunk_size"],

        "best_speed_retrieval_latency_ms":
            best_speed["retrieval_latency_ms"],

        "comparison": results
    }

@app.post("/documents/{document_id}/chunk-overlap-experiment")
def chunk_overlap_experiment(
    document_id: int,
    query: str,
    benchmark_runs: int = 3,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if benchmark_runs < 1 or benchmark_runs > 5:
        raise HTTPException(
            status_code=400,
            detail="benchmark_runs must be between 1 and 5"
        )

    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    overlaps = [0, 50, 100]
    results = []

    pdf_path = Path(document.file_path)
    pages = extract_text(pdf_path)

    # Generate query embedding once
    query_embedding = generate_embedding(
        query,
        model_name="minilm"
    )

    for overlap in overlaps:

        # =============================
        # 1. CHUNK DOCUMENT
        # =============================

        all_chunks = []

        for page in pages:
            page_text = page["text"]

            if not page_text.strip():
                continue

            page_chunks = recursive_chunking(
                page_text,
                chunk_size=500,
                overlap=overlap
            )

            for chunk in page_chunks:
                all_chunks.append({
                    "text": chunk,
                    "page_number": page["page"]
                })

        texts = [chunk["text"] for chunk in all_chunks]

        # =============================
        # 2. GENERATE EMBEDDINGS
        # =============================

        embedding_start = time.perf_counter()

        embeddings = generate_embeddings(
            texts,
            model_name="minilm"
        )

        embedding_latency_ms = round(
            (time.perf_counter() - embedding_start) * 1000,
            2
        )

        # =============================
        # 3. VECTOR STORE
        # =============================

        experiment_collection = get_experiment_collection(
            f"chunk_overlap_{document_id}_{overlap}"
        )

        ids = [
            f"{document_id}_{overlap}_{i}"
            for i in range(len(texts))
        ]

        metadatas = [
            {
                "document_id": document_id,
                "chunk_number": i,
                "page_number": all_chunks[i]["page_number"],
                "overlap": overlap
            }
            for i in range(len(texts))
        ]

        experiment_collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        # =============================
        # 4. RETRIEVAL
        # =============================

        retrieval_times = []
        chroma_results = None

        for _ in range(benchmark_runs):

            retrieval_start = time.perf_counter()

            chroma_results = experiment_collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                where={
                    "document_id": document_id
                }
            )

            retrieval_times.append(
                (time.perf_counter() - retrieval_start) * 1000
            )

        retrieval_latency_ms = round(
            sum(retrieval_times) / len(retrieval_times),
            2
        )

        # =============================
        # 5. PROCESS RESULTS
        # =============================

        retrieved_chunks = []

        documents = chroma_results["documents"][0]
        metadatas = chroma_results["metadatas"][0]
        distances = chroma_results["distances"][0]

        for i in range(len(documents)):

            retrieved_chunks.append({
                "text": documents[i],
                "chunk_index": metadatas[i]["chunk_number"],
                "page_number": metadatas[i].get("page_number"),
                "distance": distances[i]
            })

        distance_values = [
            chunk["distance"]
            for chunk in retrieved_chunks
        ]

        best_distance = min(distance_values)
        average_distance = (
            sum(distance_values) / len(distance_values)
        )

        # =============================
        # 6. CONTEXT
        # =============================

        context_start = time.perf_counter()

        context = build_context(
            retrieved_chunks
        )

        context_latency_ms = round(
            (time.perf_counter() - context_start) * 1000,
            2
        )

        # =============================
        # 7. LLM
        # =============================

        llm_start = time.perf_counter()

        answer = generate_answer(
            query,
            context
        )

        llm_latency_ms = round(
            (time.perf_counter() - llm_start) * 1000,
            2
        )

        # =============================
        # 8. EVALUATION
        # =============================

        evaluation = evaluate_answer(
            question=query,
            context=context,
            answer=answer
        )

        answer_quality = (
            0.30 * evaluation["relevance"]
            + 0.40 * evaluation["faithfulness"]
            + 0.30 * evaluation["completeness"]
        )

        answer_quality = round(
            answer_quality,
            4
        )

        # =============================
        # 9. SAVE RESULT
        # =============================

        results.append({
            "overlap": overlap,
            "chunk_size": 500,
            "chunk_count": len(all_chunks),
            "embedding_latency_ms": embedding_latency_ms,
            "retrieved_chunks": len(retrieved_chunks),
            "retrieval_latency_ms": retrieval_latency_ms,
            "context_latency_ms": context_latency_ms,
            "llm_latency_ms": llm_latency_ms,
            "best_distance": round(best_distance, 4),
            "average_distance": round(average_distance, 4),
            "answer_quality": answer_quality,
            "answer_evaluation": evaluation,
            "answer": answer
        })

    # =============================
    # 10. WINNERS
    # =============================

    best_quality = max(
        results,
        key=lambda x: x["answer_quality"]
    )

    best_retrieval = min(
        results,
        key=lambda x: x["best_distance"]
    )

    best_speed = min(
        results,
        key=lambda x: x["retrieval_latency_ms"]
    )

    return {
        "document_id": document_id,
        "filename": document.filename,
        "query": query,
        "benchmark_runs": benchmark_runs,

        "best_quality_overlap":
            best_quality["overlap"],

        "best_quality_score":
            best_quality["answer_quality"],

        "best_retrieval_overlap":
            best_retrieval["overlap"],

        "best_retrieval_distance":
            best_retrieval["best_distance"],

        "best_speed_overlap":
            best_speed["overlap"],

        "best_speed_retrieval_latency_ms":
            best_speed["retrieval_latency_ms"],

        "comparison": results
    }

@app.post("/documents/{document_id}/retrieval-threshold-experiment")
def retrieval_threshold_experiment(
    document_id: int,
    query: str,
    benchmark_runs: int = 3,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if benchmark_runs < 1 or benchmark_runs > 5:
        raise HTTPException(
            status_code=400,
            detail="benchmark_runs must be between 1 and 5"
        )

    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    thresholds = [0.8, 1.0, 1.3]
    results = []

    # Generate query embedding once
    query_embedding = generate_embedding(
        query,
        model_name="minilm"
    )

    for max_distance in thresholds:

        # --------------------------------
        # 1. RETRIEVAL BENCHMARK
        # --------------------------------

        retrieval_times = []
        chroma_results = None

        for _ in range(benchmark_runs):

            retrieval_start = time.perf_counter()

            chroma_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                where={
                    "document_id": document_id
                }
            )

            retrieval_times.append(
                (time.perf_counter() - retrieval_start) * 1000
            )

        retrieval_latency_ms = round(
            sum(retrieval_times) / len(retrieval_times),
            2
        )

        # --------------------------------
        # 2. APPLY DISTANCE THRESHOLD
        # --------------------------------

        retrieved_chunks = []

        documents = chroma_results["documents"][0]
        metadatas = chroma_results["metadatas"][0]
        distances = chroma_results["distances"][0]

        for i in range(len(documents)):

            if distances[i] > max_distance:
                continue

            retrieved_chunks.append({
                "text": documents[i],
                "chunk_index": metadatas[i]["chunk_index"],
                "page_number": metadatas[i].get("page_number"),
                "distance": distances[i]
            })

        # --------------------------------
        # 3. NO RESULTS
        # --------------------------------

        if not retrieved_chunks:
            results.append({
                "max_distance": max_distance,
                "retrieved_chunks": 0,
                "retrieval_latency_ms": retrieval_latency_ms,
                "context_latency_ms": 0,
                "llm_latency_ms": 0,
                "best_distance": None,
                "average_distance": None,
                "answer_quality": 0,
                "answer_evaluation": {
                    "relevance": 0,
                    "faithfulness": 0,
                    "completeness": 0
                },
                "answer": None
            })
            continue

        # --------------------------------
        # 4. DISTANCE METRICS
        # --------------------------------

        distance_values = [
            chunk["distance"]
            for chunk in retrieved_chunks
        ]

        best_distance = min(distance_values)

        average_distance = (
            sum(distance_values)
            / len(distance_values)
        )

        # --------------------------------
        # 5. BUILD CONTEXT
        # --------------------------------

        context_start = time.perf_counter()

        context = build_context(
            retrieved_chunks
        )

        context_latency_ms = round(
            (time.perf_counter() - context_start) * 1000,
            2
        )

        # --------------------------------
        # 6. GENERATE ANSWER
        # --------------------------------

        llm_start = time.perf_counter()

        answer = generate_answer(
            query,
            context
        )

        llm_latency_ms = round(
            (time.perf_counter() - llm_start) * 1000,
            2
        )

        # --------------------------------
        # 7. EVALUATE ANSWER
        # --------------------------------

        evaluation = evaluate_answer(
            question=query,
            context=context,
            answer=answer
        )

        answer_quality = (
            0.30 * evaluation["relevance"]
            + 0.40 * evaluation["faithfulness"]
            + 0.30 * evaluation["completeness"]
        )

        answer_quality = round(
            answer_quality,
            4
        )

        # --------------------------------
        # 8. SAVE RESULT
        # --------------------------------

        results.append({
            "max_distance": max_distance,
            "retrieved_chunks": len(retrieved_chunks),
            "retrieval_latency_ms": retrieval_latency_ms,
            "context_latency_ms": context_latency_ms,
            "llm_latency_ms": llm_latency_ms,
            "best_distance": round(best_distance, 4),
            "average_distance": round(average_distance, 4),
            "answer_quality": answer_quality,
            "answer_evaluation": evaluation,
            "answer": answer
        })

    # --------------------------------
    # 9. WINNERS
    # --------------------------------

    valid_results = [
        result
        for result in results
        if result["retrieved_chunks"] > 0
    ]

    if not valid_results:
        raise HTTPException(
            status_code=404,
            detail="No relevant chunks found"
        )

    best_quality = max(
        valid_results,
        key=lambda x: x["answer_quality"]
    )

    best_retrieval = min(
        valid_results,
        key=lambda x: x["best_distance"]
    )

    best_speed = min(
        valid_results,
        key=lambda x: x["retrieval_latency_ms"]
    )

    return {
        "document_id": document_id,
        "filename": document.filename,
        "query": query,
        "benchmark_runs": benchmark_runs,

        "best_quality_threshold":
            best_quality["max_distance"],

        "best_quality_score":
            best_quality["answer_quality"],

        "best_retrieval_threshold":
            best_retrieval["max_distance"],

        "best_retrieval_distance":
            best_retrieval["best_distance"],

        "best_speed_threshold":
            best_speed["max_distance"],

        "best_speed_retrieval_latency_ms":
            best_speed["retrieval_latency_ms"],

        "comparison": results
    }

@app.get("/documents/{document_id}/visualization")
def document_visualization(
    document_id: int,
    model_name: str = "minilm",
    method: str = "umap",
    dimensions: int = 3,
    query: str | None = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    try:
        points = generate_visualization(
            document_id=document_id,
            model_name=model_name,
            method=method,
            dimensions=dimensions,
            query=query
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    return {
        "document_id": document_id,
        "filename": document.filename,
        "model_name": model_name,
        "dimensions": dimensions,
        "points": points
    }

@app.post("/documents/{document_id}/bm25-search")
def bm25_search_document(
    document_id: int,
    query: str,
    top_k: int = 3,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(
        models.Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this document"
        )

    collection = get_embedding_collection("minilm")

    results = collection.get(
        where={
            "document_id": document_id
        },
        include=[
            "documents",
            "metadatas"
        ]
    )

    documents = []

    for text, metadata in zip(
        results["documents"],
        results["metadatas"]
    ):
        documents.append({
            "text": text,
            "chunk_number": metadata.get("chunk_number"),
            "page_number": metadata.get("page_number")
        })

    ranked_results = bm25_search(
        query=query,
        documents=documents,
        top_k=top_k
    )

    return {
        "document_id": document_id,
        "query": query,
        "top_k": top_k,
        "results": ranked_results
    }

@app.post("/documents/{document_id}/hybrid-search")
def hybrid_search_document(
    document_id: int,
    query: str,
    top_k: int = 3,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(
        models.Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this document"
        )

    collection = get_embedding_collection("minilm")

    results = collection.get(
        where={
            "document_id": document_id
        },
        include=[
            "documents",
            "metadatas"
        ]
    )

    documents = []

    for text, metadata in zip(
        results["documents"],
        results["metadatas"] # type: ignore
    ):
        documents.append({
            "text": text,
            "chunk_number": metadata.get("chunk_number"),
            "page_number": metadata.get("page_number")
        })

    # -------------------------
    # BM25 retrieval
    # -------------------------

    bm25_results = bm25_search(
        query=query,
        documents=documents,
        top_k=top_k
    )

    # -------------------------
    # Vector retrieval
    # -------------------------

    query_embedding = generate_embedding(
        query,
        model_name="minilm"
    )

    vector_results_raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={
            "document_id": document_id
        }
    )

    vector_results = []

    for text, metadata, distance in zip(
        vector_results_raw["documents"][0],
        vector_results_raw["metadatas"][0],
        vector_results_raw["distances"][0]
    ):
        vector_results.append({
            "text": text,
            "chunk_number": metadata.get("chunk_number"),
            "page_number": metadata.get("page_number"),
            "distance": float(distance)
        })

    # -------------------------
    # Combine
    # -------------------------

    rrf_results = reciprocal_rank_fusion(
    result_lists=[
        bm25_results,
        vector_results
    ],
    top_k=top_k
)

    return {
        "document_id": document_id,
        "query": query,
        "top_k": top_k,
        "bm25_results": bm25_results,
        "vector_results": vector_results,
        "rrf_results": rrf_results
    }

@app.post("/documents/{document_id}/rerank-test")
def rerank_test(
    document_id: int,
    query: str,
    top_k: int = 3,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(
        models.Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this document"
        )

    collection = get_embedding_collection("minilm")

    results = collection.get(
        where={
            "document_id": document_id
        },
        include=[
            "documents",
            "metadatas"
        ]
    )

    documents = []

    for text, metadata in zip(
        results["documents"],
        results["metadatas"]
    ):
        documents.append({
            "text": text,
            "chunk_number": metadata.get("chunk_number"),
            "page_number": metadata.get("page_number")
        })

    reranked_results = rerank(
        query=query,
        documents=documents,
        top_k=top_k
    )

    return {
        "document_id": document_id,
        "query": query,
        "top_k": top_k,
        "results": reranked_results
    }
@app.post("/documents/{document_id}/advanced-search")
def advanced_search(
    document_id: int,
    query: str,
    top_k: int = 3,
    candidate_k: int = 10,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(
        models.Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this document"
        )

    results = hybrid_rerank_search(
        query=query,
        document_id=document_id,
        top_k=top_k,
        candidate_k=candidate_k
    )

    return {
        "document_id": document_id,
        "query": query,
        "top_k": top_k,
        "candidate_k": candidate_k,
        "results": results
    }

@app.post("/documents/{document_id}/retrieval-comparison")
def retrieval_comparison(
    document_id: int,
    query: str,
    relevant_chunks: list[int],
    top_k: int = 3,
    candidate_k: int = 10,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(
        models.Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this document"
        )

    results = evaluate_retrieval_strategies(
        query=query,
        document_id=document_id,
        relevant_chunks=set(relevant_chunks),
        top_k=top_k,
        candidate_k=candidate_k,
    )

    return {
        "document_id": document_id,
        "query": query,
        "top_k": top_k,
        "candidate_k": candidate_k,
        "results": results
    }


@app.post("/documents/{document_id}/retrieval-benchmark")
def retrieval_benchmark(
    document_id: int,
    top_k: int = 3,
    candidate_k: int = 10,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(
        models.Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this document"
        )

    results = run_retrieval_benchmark(
        document_id=document_id,
        top_k=top_k,
        candidate_k=candidate_k
    )

    aggregate = aggregate_benchmark_results(results)

    return {
        "document_id": document_id,
        "top_k": top_k,
        "candidate_k": candidate_k,
        "questions_evaluated": len(results),
        "aggregate": aggregate,
        "results": results
    }

@app.delete("/documents/{document_id}/rebuild-minilm")
def rebuild_minilm_collection(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------
    # Verify document
    # --------------------------------

    document = (
        db.query(models.Document)
        .filter(models.Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    # --------------------------------
    # Get existing chunks from PostgreSQL
    # --------------------------------

    chunks = (
        db.query(models.Chunk)
        .filter(
            models.Chunk.document_id == document_id
        )
        .order_by(models.Chunk.chunk_number)
        .all()
    )

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No chunks found for this document"
        )

    # --------------------------------
    # Get MiniLM collection
    # --------------------------------

    collection = get_embedding_collection("minilm")

    # --------------------------------
    # Delete existing records for
    # this document
    # --------------------------------

    existing = collection.get(
        where={
            "document_id": document_id
        }
    )

    if existing["ids"]:
        collection.delete(
            ids=existing["ids"]
        )

    # --------------------------------
    # Generate fresh embeddings
    # --------------------------------

    texts = [
        chunk.text
        for chunk in chunks
    ]

    embeddings = generate_embeddings(
        texts,
        model_name="minilm"
    )

    # --------------------------------
    # Store clean records
    # --------------------------------

    ids = [
        f"experiment_{document_id}_minilm_{i}"
        for i in range(len(chunks))
    ]

    metadatas = [
        {
            "document_id": document_id,
            "filename": document.filename,
            "chunk_number": i,
            "page_number": chunk.page_number,
            "embedding_model": "minilm"
        }
        for i, chunk in enumerate(chunks)
    ]

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return {
        "message": "MiniLM collection rebuilt successfully",
        "document_id": document_id,
        "chunks_stored": len(chunks)
    }


def main() -> None:
    """Run the API with the installed ``ragviz`` command."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
