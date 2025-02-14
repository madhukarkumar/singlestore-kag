import logging
from celery import states
from celeryconfig import app
from pdf_processor import process_pdf
from celery.signals import task_prerun, task_success, task_failure
from celery.exceptions import Ignore

logger = logging.getLogger(__name__)

@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    """Log when task starts"""
    logger.info(f"Starting task {task_id}")

@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Log when task succeeds"""
    logger.info(f"Task {sender.request.id} completed successfully")

@task_failure.connect
def task_failure_handler(sender=None, exception=None, **kwargs):
    """Log when task fails"""
    logger.error(f"Task {sender.request.id} failed: {str(exception)}")

@app.task(bind=True, name='tasks.process_pdf_task')
def process_pdf_task(self, doc_id: int):
    """
    Celery task to process a PDF file.
    
    Args:
        doc_id: Document ID to process
    """
    try:
        # Update task state to STARTED
        self.update_state(state=states.STARTED, meta={
            'status': 'Starting PDF processing...',
            'current': 0,
            'total': 100
        })
        
        # Process the PDF, passing the task instance for progress updates
        process_pdf(doc_id, task=self)
        
        # Update task state to SUCCESS
        self.update_state(state=states.SUCCESS, meta={
            'status': 'PDF processed successfully',
            'current': 100,
            'total': 100
        })
        
        return {
            'status': 'success',
            'message': f'Successfully processed document {doc_id}'
        }
        
    except Exception as exc:
        # Log the error
        logger.error(f"Error processing PDF: {str(exc)}", exc_info=True)
        
        # Update task state to FAILURE
        self.update_state(state=states.FAILURE, meta={
            'status': 'Failed to process PDF',
            'error': str(exc),
            'exc_type': type(exc).__name__
        })
        
        # Re-raise the exception for Celery to handle
        raise exc
