import os
import logging
import google.generativeai as genai
from docx import Document
from django.conf import settings
from .models import ReportChunk

logger = logging.getLogger(__name__)

def _ensure_configured():
    """Ensures that the Gemini API is configured with the key from environment."""
    if not os.getenv('GEMINI_API_KEY'):
        # Try finding .env if not loaded yet
        from dotenv import load_dotenv, find_dotenv
        load_dotenv(find_dotenv())
    
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
        return True
    logger.error("GEMINI_API_KEY not found in environment.")
    return False

def extract_text_from_docx(file_obj):
    """Extracts text from a .docx file object."""
    try:
        doc = Document(file_obj)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())
        return "\n".join(full_text)
    except Exception as e:
        logger.error(f"Error extracting text from docx: {e}")
        return ""

def chunk_text(text, chunk_size=1000, overlap=200):
    """Splits text into overlapping chunks."""
    chunks = []
    if not text:
        return chunks
        
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def get_embedding(text):
    """Fetches embedding for a single text chunk using Gemini."""
    if not _ensure_configured():
        return None
    try:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Error fetching embedding from Gemini for text '{text[:50]}...': {e}")
        return None

def index_report(report):
    """
    Indexes a report for RAG:
    1. Extracts text from the stored file object (requires file to be read).
    2. Chunks the text.
    3. Fetches embeddings for each chunk.
    4. Saves to ReportChunk model.
    """
    # Note: We need a way to read the file content. 
    # Since we are using Google Drive, we'll need to fetch the content or 
    # extract it during the upload process before it's gone from memory.
    pass # This will be called from upload_report with the file_obj

def index_report_from_content(report, file_content):
    """Indexes a report from raw bytes content with metadata-rich header."""
    from io import BytesIO
    text = extract_text_from_docx(BytesIO(file_content))
    if not text:
        logger.warning(f"No text extracted from report {report.id}")
        return
        
    # Construct metadata-rich header
    dept_name = report.department.department_name if report.department else "N/A"
    header = (
        f"REPORT_METADATA_HEADER\n"
        f"Type: {report.get_report_type_display()}\n"
        f"Department: {dept_name}\n"
        f"Agenda: {report.agenda or 'N/A'}\n"
        f"Topic: {report.topic or 'N/A'}\n"
        f"Date: {report.date_of_conduction or 'N/A'}\n"
        f"Original Filename: {report.original_filename}\n"
        f"--- START DOCUMENT CONTENT ---\n"
    )
    
    full_text = header + text
    chunks = chunk_text(full_text)
    
    # Clean previous chunks if any (for re-indexing)
    report.chunks.all().delete()
    
    for chunk in chunks:
        emb = get_embedding(chunk)
        if emb:
            ReportChunk.objects.create(
                report=report,
                chunk_text=chunk,
                embedding=emb
            )
    logger.info(f"Indexed report {report.id} ({len(chunks)} chunks) with prefix metadata.")

def cosine_similarity(v1, v2):
    """Simple cosine similarity implementation."""
    import math
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude = math.sqrt(sum(a * a for a in v1)) * math.sqrt(sum(b * b for b in v2))
    if not magnitude:
        return 0
    return dot_product / magnitude

def search_relevant_chunks(query_text, authorized_report_ids, top_k=5):
    """
    Search for relevant chunks across authorized reports.
    1. Get query embedding.
    2. Fetch chunks for authorized reports.
    3. Rank by cosine similarity.
    """
    query_emb = get_embedding(query_text)
    if not query_emb:
        return []
        
    # Fetch all chunks for authorized reports
    chunks = ReportChunk.objects.filter(report_id__in=authorized_report_ids)
    
    results = []
    for chunk in chunks:
        sim = cosine_similarity(query_emb, chunk.embedding)
        results.append((sim, chunk))
        
    # Sort by similarity descending
    results.sort(key=lambda x: x[0], reverse=True)
    return [chunk for sim, chunk in results[:top_k]]

def generate_answer(query, context_chunks):
    """Generates an answer using Gemini with the provided context."""
    if not _ensure_configured():
        return "Chatbot is currently misconfigured (Missing API Key)."

    if not context_chunks:
        context_text = "No relevant documents found. The user is just introducing themselves or asking something not in the records."
    else:
        context_text = "\n\n---\n\n".join([c.chunk_text for c in context_chunks])
        
    prompt = f"""
You are a precision documentation assistant for the TIC Matrix Platform. 
Use the following context (which includes document headers and extracted content) to answer the user's question accurately.

RULES:
1. If the user asks for "Agendas" or "Topics", list them exactly as they appear in the METADATA_HEADER section.
2. Use clean Markdown for lists and bold text. 
3. If multiple documents are relevant, group your answer by document or date.
4. If the info is not in the context, clearly state that there is no official record for that specific query.

CONTEXT:
{context_text}

QUESTION:
{query}

ANSWER:
"""
    try:
        model = genai.GenerativeModel('models/gemini-flash-latest')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating answer from Gemini for query '{query}': {e}")
        return f"I encountered an error while processing your request: {str(e)}"
