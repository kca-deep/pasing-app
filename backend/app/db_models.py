"""
SQLAlchemy ORM models for the parsing application.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Document(Base):
    """
    Document metadata table.
    Stores information about parsed documents.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False, unique=True, index=True)
    original_path = Column(String, nullable=False)
    file_size = Column(Integer)  # bytes
    file_extension = Column(String)  # .pdf, .docx, etc.
    total_pages = Column(Integer)
    parsing_status = Column(String, default="pending", index=True)  # pending, processing, completed, failed
    parsing_strategy = Column(String)  # docling, camelot, hybrid
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_parsed_at = Column(DateTime)
    output_folder = Column(String)  # output/{doc_name}/
    content_md_path = Column(String)  # output/{doc_name}/content.md
    manifest_json_path = Column(String)  # output/{doc_name}/manifest.json

    # Relationships
    tables = relationship("Table", back_populates="document", cascade="all, delete-orphan")
    parsing_history = relationship("ParsingHistory", back_populates="document", cascade="all, delete-orphan")
    pictures = relationship("Picture", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.parsing_status}')>"


class Table(Base):
    """
    Table metadata table.
    Stores information about extracted tables from documents.
    """
    __tablename__ = "tables"
    __table_args__ = (
        UniqueConstraint("document_id", "table_id", name="uq_document_table"),
        Index("idx_tables_document_id", "document_id"),
        Index("idx_tables_table_id", "table_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    table_id = Column(String, nullable=False)  # table_001, table_002, ...
    table_index = Column(Integer, nullable=False)
    page = Column(Integer)
    caption = Column(Text)
    rows = Column(Integer)
    cols = Column(Integer)
    has_merged_cells = Column(Boolean, default=False)
    is_complex = Column(Boolean, default=False)
    complexity_score = Column(Float)
    summary = Column(Text)  # AI-generated summary (Phase 8)
    json_path = Column(String)  # tables/table_001.json
    parsing_method = Column(String)  # docling, camelot_lattice, camelot_stream
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="tables")

    def __repr__(self):
        return f"<Table(id={self.id}, table_id='{self.table_id}', rows={self.rows}, cols={self.cols})>"


class ParsingHistory(Base):
    """
    Parsing history table.
    Tracks all parsing attempts for documents with version management.
    """
    __tablename__ = "parsing_history"
    __table_args__ = (
        Index("idx_parsing_history_document_id", "document_id"),
        Index("idx_parsing_history_version_folder", "version_folder"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    parsing_status = Column(String, nullable=False)  # started, completed, failed
    parsing_strategy = Column(String)  # docling, camelot, hybrid, remote_ocr, mineru
    options_json = Column(Text)  # JSON string of parsing options

    # Version management fields (NEW)
    version_folder = Column(String)  # 버전 폴더명 (예: "remote-ocr_upstage_20251105-163045")
    output_dir = Column(String)  # 전체 출력 경로 (예: "output/doc_name/remote-ocr_upstage_20251105-163045")
    content_path = Column(String)  # content.md 경로
    metadata_path = Column(String)  # metadata.json 경로
    is_latest = Column(Boolean, default=True)  # 최신 버전 여부

    # Table/Image statistics
    total_tables = Column(Integer)
    markdown_tables = Column(Integer)
    json_tables = Column(Integer)
    total_images = Column(Integer)

    # Error and duration
    error_message = Column(Text)
    duration_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="parsing_history")

    def __repr__(self):
        return f"<ParsingHistory(id={self.id}, document_id={self.document_id}, version='{self.version_folder}', status='{self.parsing_status}')>"


class Picture(Base):
    """
    Picture metadata table.
    Stores information about images extracted from documents.
    """
    __tablename__ = "pictures"
    __table_args__ = (
        UniqueConstraint("document_id", "picture_id", name="uq_document_picture"),
        Index("idx_pictures_document_id", "document_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    picture_id = Column(String, nullable=False)  # picture_001, picture_002, ...
    page = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    area = Column(Integer)  # width * height
    description = Column(Text)  # VLM-generated description
    image_path = Column(String)  # pictures/picture_001.png
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="pictures")

    def __repr__(self):
        return f"<Picture(id={self.id}, picture_id='{self.picture_id}', area={self.area})>"


class DifyConfig(Base):
    """
    Dify API configuration table.
    Stores Dify API key and base URL.
    """
    __tablename__ = "dify_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    api_key = Column(String, nullable=False)
    base_url = Column(String, nullable=False, default="https://api.dify.ai")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DifyConfig(id={self.id}, base_url='{self.base_url}')>"


class DifyUploadLog(Base):
    """
    Dify upload log table.
    Tracks all document uploads to Dify.
    """
    __tablename__ = "dify_upload_logs"
    __table_args__ = (
        Index("idx_dify_upload_logs_dataset_id", "dataset_id"),
        Index("idx_dify_upload_logs_uploaded_at", "uploaded_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String, nullable=False)
    dataset_name = Column(String)
    document_path = Column(String, nullable=False)
    document_name = Column(String, nullable=False)
    dify_document_id = Column(String)  # Dify document ID
    batch_id = Column(String)  # Dify batch ID
    indexing_status = Column(String, default="waiting")  # waiting, parsing, cleaning, splitting, indexing, completed, error
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    def __repr__(self):
        return f"<DifyUploadLog(id={self.id}, document_name='{self.document_name}', status='{self.indexing_status}')>"
