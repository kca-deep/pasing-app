"""
CRUD (Create, Read, Update, Delete) operations for database models.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app import db_models, schemas


# ===== Document CRUD =====

def create_document(db: Session, document: schemas.DocumentCreate) -> db_models.Document:
    """Create a new document record."""
    db_document = db_models.Document(**document.model_dump())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def get_document_by_id(db: Session, document_id: int) -> Optional[db_models.Document]:
    """Get a document by its ID."""
    return db.query(db_models.Document).filter(db_models.Document.id == document_id).first()


def get_document_by_filename(db: Session, filename: str) -> Optional[db_models.Document]:
    """Get a document by its filename."""
    return db.query(db_models.Document).filter(db_models.Document.filename == filename).first()


def list_documents(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
) -> List[db_models.Document]:
    """List all documents with optional filtering."""
    query = db.query(db_models.Document)
    if status:
        query = query.filter(db_models.Document.parsing_status == status)
    return query.offset(skip).limit(limit).all()


def update_document(
    db: Session,
    document_id: int,
    document_update: schemas.DocumentUpdate
) -> Optional[db_models.Document]:
    """Update a document's metadata."""
    db_document = get_document_by_id(db, document_id)
    if not db_document:
        return None

    update_data = document_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_document, field, value)

    db_document.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_document)
    return db_document


def delete_document(db: Session, document_id: int) -> bool:
    """Delete a document and all related records (cascades)."""
    db_document = get_document_by_id(db, document_id)
    if not db_document:
        return False

    db.delete(db_document)
    db.commit()
    return True


def get_document_with_counts(db: Session, document_id: int) -> Optional[dict]:
    """Get document with aggregated counts of tables and pictures."""
    document = get_document_by_id(db, document_id)
    if not document:
        return None

    table_count = db.query(func.count(db_models.Table.id)).filter(
        db_models.Table.document_id == document_id
    ).scalar()

    picture_count = db.query(func.count(db_models.Picture.id)).filter(
        db_models.Picture.document_id == document_id
    ).scalar()

    return {
        "document": document,
        "chunk_count": 0,  # Chunk is not used
        "table_count": table_count or 0,
        "picture_count": picture_count or 0,
    }


def list_documents_with_counts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    order_by: str = "last_parsed_at"
) -> List[dict]:
    """List all documents with aggregated counts of tables and pictures."""
    query = db.query(
        db_models.Document,
        func.count(db_models.Table.id.distinct()).label('table_count'),
        func.count(db_models.Picture.id.distinct()).label('picture_count')
    ).outerjoin(
        db_models.Table, db_models.Document.id == db_models.Table.document_id
    ).outerjoin(
        db_models.Picture, db_models.Document.id == db_models.Picture.document_id
    ).group_by(db_models.Document.id)

    if status:
        query = query.filter(db_models.Document.parsing_status == status)

    # Order by specified field (default: last_parsed_at descending)
    if order_by == "last_parsed_at":
        query = query.order_by(db_models.Document.last_parsed_at.desc().nullslast())
    elif order_by == "created_at":
        query = query.order_by(db_models.Document.created_at.desc())
    elif order_by == "filename":
        query = query.order_by(db_models.Document.filename.asc())

    results = query.offset(skip).limit(limit).all()

    # Convert to list of dicts
    documents_with_counts = []
    for document, table_count, picture_count in results:
        documents_with_counts.append({
            "document": document,
            "chunk_count": 0,  # Chunk is not used
            "table_count": table_count or 0,
            "picture_count": picture_count or 0,
        })

    return documents_with_counts


# ===== Table CRUD =====

def create_table(db: Session, table: schemas.TableCreate) -> db_models.Table:
    """Create a new table record."""
    db_table = db_models.Table(**table.model_dump())
    db.add(db_table)
    db.commit()
    db.refresh(db_table)
    return db_table


def create_tables_bulk(db: Session, tables: List[schemas.TableCreate]) -> List[db_models.Table]:
    """Create multiple tables in bulk."""
    db_tables = [db_models.Table(**table.model_dump()) for table in tables]
    db.add_all(db_tables)
    db.commit()
    for table in db_tables:
        db.refresh(table)
    return db_tables


def get_tables_by_document_id(db: Session, document_id: int) -> List[db_models.Table]:
    """Get all tables for a document."""
    return db.query(db_models.Table).filter(
        db_models.Table.document_id == document_id
    ).order_by(db_models.Table.table_index).all()


def get_table_by_table_id(db: Session, document_id: int, table_id: str) -> Optional[db_models.Table]:
    """Get a specific table by its table_id."""
    return db.query(db_models.Table).filter(
        db_models.Table.document_id == document_id,
        db_models.Table.table_id == table_id
    ).first()


def update_table_summary(
    db: Session,
    table_id: int,
    summary: str
) -> Optional[db_models.Table]:
    """Update a table's AI-generated summary (Phase 8)."""
    db_table = db.query(db_models.Table).filter(db_models.Table.id == table_id).first()
    if not db_table:
        return None

    db_table.summary = summary
    db.commit()
    db.refresh(db_table)
    return db_table


# ===== Parsing History CRUD =====

def create_parsing_history(
    db: Session,
    history: schemas.ParsingHistoryCreate
) -> db_models.ParsingHistory:
    """Create a new parsing history record."""
    db_history = db_models.ParsingHistory(**history.model_dump())
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history


def get_parsing_history(
    db: Session,
    document_id: int,
    limit: int = 10
) -> List[db_models.ParsingHistory]:
    """Get parsing history for a document."""
    return db.query(db_models.ParsingHistory).filter(
        db_models.ParsingHistory.document_id == document_id
    ).order_by(db_models.ParsingHistory.created_at.desc()).limit(limit).all()


# ===== Picture CRUD =====

def create_picture(db: Session, picture: schemas.PictureCreate) -> db_models.Picture:
    """Create a new picture record."""
    db_picture = db_models.Picture(**picture.model_dump())
    db.add(db_picture)
    db.commit()
    db.refresh(db_picture)
    return db_picture


def create_pictures_bulk(db: Session, pictures: List[schemas.PictureCreate]) -> List[db_models.Picture]:
    """Create multiple pictures in bulk."""
    db_pictures = [db_models.Picture(**picture.model_dump()) for picture in pictures]
    db.add_all(db_pictures)
    db.commit()
    for picture in db_pictures:
        db.refresh(picture)
    return db_pictures


def get_pictures_by_document_id(db: Session, document_id: int) -> List[db_models.Picture]:
    """Get all pictures for a document."""
    return db.query(db_models.Picture).filter(
        db_models.Picture.document_id == document_id
    ).all()


# ===== Dify CRUD =====

def get_dify_config(db: Session) -> Optional[db_models.DifyConfig]:
    """Get the most recent Dify configuration."""
    return db.query(db_models.DifyConfig).order_by(
        db_models.DifyConfig.updated_at.desc()
    ).first()


def create_or_update_dify_config(
    db: Session,
    api_key: str,
    base_url: str
) -> db_models.DifyConfig:
    """Create or update Dify configuration."""
    config = get_dify_config(db)

    if config:
        # Update existing config
        config.api_key = api_key
        config.base_url = base_url
        config.updated_at = datetime.utcnow()
    else:
        # Create new config
        config = db_models.DifyConfig(
            api_key=api_key,
            base_url=base_url
        )
        db.add(config)

    db.commit()
    db.refresh(config)
    return config


def create_upload_log(
    db: Session,
    dataset_id: str,
    dataset_name: Optional[str],
    document_path: str,
    document_name: str,
    dify_document_id: Optional[str] = None,
    batch_id: Optional[str] = None
) -> db_models.DifyUploadLog:
    """Create a new upload log."""
    log = db_models.DifyUploadLog(
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        document_path=document_path,
        document_name=document_name,
        dify_document_id=dify_document_id,
        batch_id=batch_id,
        indexing_status="waiting"
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def update_upload_log(
    db: Session,
    log_id: int,
    indexing_status: str,
    completed_at: Optional[datetime] = None
) -> Optional[db_models.DifyUploadLog]:
    """Update an upload log."""
    log = db.query(db_models.DifyUploadLog).filter(
        db_models.DifyUploadLog.id == log_id
    ).first()

    if not log:
        return None

    log.indexing_status = indexing_status
    if completed_at:
        log.completed_at = completed_at

    db.commit()
    db.refresh(log)
    return log


def get_upload_history(db: Session, limit: int = 50) -> List[db_models.DifyUploadLog]:
    """Get upload history (most recent first)."""
    return db.query(db_models.DifyUploadLog).order_by(
        db_models.DifyUploadLog.uploaded_at.desc()
    ).limit(limit).all()
