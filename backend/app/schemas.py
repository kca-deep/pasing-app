"""
Pydantic schemas for database API responses.
These schemas are used to serialize SQLAlchemy models to JSON.
"""
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


# Document schemas
class DocumentBase(BaseModel):
    filename: str
    original_path: str
    file_size: Optional[int] = None
    file_extension: Optional[str] = None
    total_pages: Optional[int] = None
    parsing_status: str = "pending"
    parsing_strategy: Optional[str] = None
    output_folder: Optional[str] = None
    content_md_path: Optional[str] = None
    manifest_json_path: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    parsing_status: Optional[str] = None
    parsing_strategy: Optional[str] = None
    last_parsed_at: Optional[datetime] = None
    output_folder: Optional[str] = None
    content_md_path: Optional[str] = None
    manifest_json_path: Optional[str] = None


class DocumentSchema(DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_parsed_at: Optional[datetime] = None

    # Aggregates
    chunk_count: Optional[int] = None
    table_count: Optional[int] = None
    picture_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Chunk schemas
class ChunkBase(BaseModel):
    document_id: int
    chunk_id: str
    chunk_index: int
    heading_level: Optional[int] = None
    heading_text: Optional[str] = None
    content_preview: Optional[str] = None
    char_count: Optional[int] = None
    word_count: Optional[int] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    has_table: bool = False
    has_image: bool = False


class ChunkCreate(ChunkBase):
    pass


class ChunkSchema(ChunkBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Table schemas
class TableBase(BaseModel):
    document_id: int
    chunk_id: Optional[int] = None
    table_id: str
    table_index: int
    page: Optional[int] = None
    caption: Optional[str] = None
    rows: Optional[int] = None
    cols: Optional[int] = None
    has_merged_cells: bool = False
    is_complex: bool = False
    complexity_score: Optional[float] = None
    summary: Optional[str] = None
    json_path: Optional[str] = None
    parsing_method: Optional[str] = None


class TableCreate(TableBase):
    pass


class TableUpdate(BaseModel):
    summary: Optional[str] = None  # For AI summary updates (Phase 8)


class TableSchema(TableBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Parsing History schemas
class ParsingHistoryBase(BaseModel):
    document_id: int
    parsing_status: str
    parsing_strategy: Optional[str] = None
    options_json: Optional[str] = None
    total_chunks: Optional[int] = None
    total_tables: Optional[int] = None
    markdown_tables: Optional[int] = None
    json_tables: Optional[int] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None


class ParsingHistoryCreate(ParsingHistoryBase):
    pass


class ParsingHistorySchema(ParsingHistoryBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Picture schemas
class PictureBase(BaseModel):
    document_id: int
    chunk_id: Optional[int] = None
    picture_id: str
    page: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    area: Optional[int] = None
    description: Optional[str] = None
    image_path: Optional[str] = None


class PictureCreate(PictureBase):
    pass


class PictureSchema(PictureBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Combined response schemas
class DocumentDetailSchema(DocumentSchema):
    """Document with related data (chunks, tables, etc.)"""
    chunks: List[ChunkSchema] = []
    tables: List[TableSchema] = []
    parsing_history: List[ParsingHistorySchema] = []
    pictures: List[PictureSchema] = []

    model_config = ConfigDict(from_attributes=True)
