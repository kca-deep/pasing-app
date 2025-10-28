"""
Job Manager for Background Parsing Tasks

Manages asynchronous document parsing jobs with progress tracking.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel


class JobStatus(str, Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobProgress(BaseModel):
    """Job progress information"""
    job_id: str
    filename: str
    status: JobStatus
    progress: int = 0  # 0-100
    message: str = ""
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JobManager:
    """
    In-memory job manager for parsing tasks

    Note: Jobs are stored in memory and will be lost on server restart.
    For production, consider using Redis or a database.
    """

    def __init__(self):
        self._jobs: Dict[str, JobProgress] = {}

    def create_job(self, filename: str) -> str:
        """
        Create a new parsing job

        Args:
            filename: Document filename

        Returns:
            job_id: Unique job identifier
        """
        job_id = str(uuid.uuid4())

        job = JobProgress(
            job_id=job_id,
            filename=filename,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow()
        )

        self._jobs[job_id] = job
        return job_id

    def get_job(self, job_id: str) -> Optional[JobProgress]:
        """Get job by ID"""
        return self._jobs.get(job_id)

    def update_progress(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None
    ) -> None:
        """
        Update job progress

        Args:
            job_id: Job identifier
            status: New status (optional)
            progress: Progress percentage 0-100 (optional)
            message: Progress message (optional)
        """
        job = self._jobs.get(job_id)
        if not job:
            return

        if status:
            job.status = status

            # Set timestamps
            if status == JobStatus.PROCESSING and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                job.completed_at = datetime.utcnow()

        if progress is not None:
            job.progress = min(100, max(0, progress))

        if message is not None:
            job.message = message

    def set_result(self, job_id: str, result: Dict[str, Any]) -> None:
        """Set job result (on success)"""
        job = self._jobs.get(job_id)
        if job:
            job.result = result
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.completed_at = datetime.utcnow()

    def set_error(self, job_id: str, error: str) -> None:
        """Set job error (on failure)"""
        job = self._jobs.get(job_id)
        if job:
            job.error = error
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()

    def delete_job(self, job_id: str) -> None:
        """Delete job from memory"""
        if job_id in self._jobs:
            del self._jobs[job_id]

    def cleanup_old_jobs(self, hours: int = 24) -> int:
        """
        Delete jobs older than specified hours

        Args:
            hours: Age threshold in hours

        Returns:
            Number of deleted jobs
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        to_delete = []

        for job_id, job in self._jobs.items():
            if job.completed_at and job.completed_at < cutoff:
                to_delete.append(job_id)

        for job_id in to_delete:
            del self._jobs[job_id]

        return len(to_delete)


# Global job manager instance
job_manager = JobManager()
