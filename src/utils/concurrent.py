"""Concurrent processing utilities for AWS operations."""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional, TypeVar, Generic, Coroutine
from dataclasses import dataclass
import time

from ..config import get_config
from .progress import get_progress_tracker

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class ProcessingResult(Generic[T, R]):
    """Result of a concurrent processing operation."""
    input_item: T
    result: Optional[R] = None
    error: Optional[Exception] = None
    processing_time: float = 0.0
    
    @property
    def success(self) -> bool:
        """Check if processing was successful."""
        return self.error is None
    
    @property
    def failed(self) -> bool:
        """Check if processing failed."""
        return self.error is not None


class ConcurrentAWSProcessor:
    """Concurrent processor for AWS operations with progress tracking."""
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize concurrent processor.
        
        Args:
            max_workers: Maximum number of worker threads (optional)
        """
        config = get_config()
        self.max_workers = max_workers or config.max_concurrent_workers
        self.progress = get_progress_tracker()
        
        logger.info(f"Initialized concurrent processor with {self.max_workers} workers")
    
    def process_items(
        self,
        items: List[T],
        processor_func: Callable[[T], R],
        description: str = "Processing items",
        fail_fast: bool = False
    ) -> List[ProcessingResult[T, R]]:
        """
        Process items concurrently with progress tracking.
        
        Args:
            items: List of items to process
            processor_func: Function to process each item
            description: Description for progress tracking
            fail_fast: Whether to stop on first error
            
        Returns:
            List of processing results
        """
        if not items:
            logger.info("No items to process")
            return []
        
        results: List[ProcessingResult[T, R]] = []
        
        with self.progress.track_operation(f"{description} ({len(items)} items)", total=len(items)) as task_id:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_item = {
                    executor.submit(self._safe_process_item, item, processor_func): item
                    for item in items
                }
                
                # Process completed tasks
                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    result = future.result()
                    results.append(result)
                    
                    # Update progress
                    self.progress.update_progress(task_id)
                    
                    # Handle errors
                    if result.failed:
                        logger.warning(f"Failed to process item {item}: {result.error}")
                        if fail_fast:
                            logger.error("Stopping processing due to fail_fast=True")
                            # Cancel remaining futures
                            for remaining_future in future_to_item:
                                if not remaining_future.done():
                                    remaining_future.cancel()
                            break
        
        # Log summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_time = sum(r.processing_time for r in results)
        
        logger.info(f"Processing complete: {successful} successful, {failed} failed, {total_time:.2f}s total")
        
        if failed > 0:
            self.progress.show_warning(
                f"Processing completed with {failed} failures",
                f"Successfully processed {successful}/{len(items)} items"
            )
        else:
            self.progress.show_success(
                f"All {successful} items processed successfully",
                f"Total processing time: {total_time:.2f}s"
            )
        
        return results
    
    def _safe_process_item(self, item: T, processor_func: Callable[[T], R]) -> ProcessingResult[T, R]:
        """
        Safely process a single item with error handling and timing.
        
        Args:
            item: Item to process
            processor_func: Processing function
            
        Returns:
            Processing result
        """
        start_time = time.time()
        
        try:
            result = processor_func(item)
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                input_item=item,
                result=result,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.debug(f"Error processing item {item}: {e}")
            
            return ProcessingResult(
                input_item=item,
                error=e,
                processing_time=processing_time
            )
    
    def process_accounts_concurrently(
        self,
        accounts: List[Dict[str, Any]],
        processor_func: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> List[ProcessingResult[Dict[str, Any], Dict[str, Any]]]:
        """
        Process AWS accounts concurrently.
        
        Args:
            accounts: List of account dictionaries
            processor_func: Function to process each account
            
        Returns:
            List of processing results
        """
        return self.process_items(
            accounts,
            processor_func,
            description="Processing AWS accounts",
            fail_fast=False
        )
    
    def process_organizational_units_concurrently(
        self,
        ous: List[Dict[str, Any]],
        processor_func: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> List[ProcessingResult[Dict[str, Any], Dict[str, Any]]]:
        """
        Process organizational units concurrently.
        
        Args:
            ous: List of OU dictionaries
            processor_func: Function to process each OU
            
        Returns:
            List of processing results
        """
        return self.process_items(
            ous,
            processor_func,
            description="Processing organizational units",
            fail_fast=False
        )
    
    def process_permission_sets_concurrently(
        self,
        permission_sets: List[str],
        processor_func: Callable[[str], Dict[str, Any]]
    ) -> List[ProcessingResult[str, Dict[str, Any]]]:
        """
        Process permission sets concurrently.
        
        Args:
            permission_sets: List of permission set ARNs
            processor_func: Function to process each permission set
            
        Returns:
            List of processing results
        """
        return self.process_items(
            permission_sets,
            processor_func,
            description="Processing permission sets",
            fail_fast=False
        )


class AsyncAWSProcessor:
    """Async processor for AWS operations (for future async AWS SDK support)."""
    
    def __init__(self, max_concurrent: Optional[int] = None):
        """
        Initialize async processor.
        
        Args:
            max_concurrent: Maximum concurrent operations
        """
        config = get_config()
        self.max_concurrent = max_concurrent or config.max_concurrent_workers
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.progress = get_progress_tracker()
    
    async def process_items_async(
        self,
        items: List[T],
        processor_func: Callable[[T], Coroutine[Any, Any, R]],
        description: str = "Processing items async"
    ) -> List[ProcessingResult[T, R]]:
        """
        Process items asynchronously.
        
        Args:
            items: List of items to process
            processor_func: Async function to process each item
            description: Description for progress tracking
            
        Returns:
            List of processing results
        """
        if not items:
            return []
        
        async def _process_with_semaphore(item: T) -> ProcessingResult[T, R]:
            async with self.semaphore:
                return await self._safe_process_item_async(item, processor_func)
        
        # Create tasks for all items
        tasks = [_process_with_semaphore(item) for item in items]
        
        # Process with progress tracking
        results = []
        with self.progress.track_operation(f"{description} ({len(items)} items)", total=len(items)) as task_id:
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                self.progress.update_progress(task_id)
        
        return results
    
    async def _safe_process_item_async(
        self,
        item: T,
        processor_func: Callable[[T], Coroutine[Any, Any, R]]
    ) -> ProcessingResult[T, R]:
        """
        Safely process a single item asynchronously.
        
        Args:
            item: Item to process
            processor_func: Async processing function
            
        Returns:
            Processing result
        """
        start_time = time.time()
        
        try:
            result = await processor_func(item)
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                input_item=item,
                result=result,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                input_item=item,
                error=e,
                processing_time=processing_time
            )


# Global processor instances
_concurrent_processor: Optional[ConcurrentAWSProcessor] = None
_async_processor: Optional[AsyncAWSProcessor] = None


def get_concurrent_processor() -> ConcurrentAWSProcessor:
    """Get or create global concurrent processor instance."""
    global _concurrent_processor
    if _concurrent_processor is None:
        _concurrent_processor = ConcurrentAWSProcessor()
    return _concurrent_processor


def get_async_processor() -> AsyncAWSProcessor:
    """Get or create global async processor instance."""
    global _async_processor
    if _async_processor is None:
        _async_processor = AsyncAWSProcessor()
    return _async_processor


def process_concurrently(
    items: List[T],
    processor_func: Callable[[T], R],
    description: str = "Processing items",
    max_workers: Optional[int] = None,
    fail_fast: bool = False
) -> List[ProcessingResult[T, R]]:
    """
    Convenience function for concurrent processing.
    
    Args:
        items: List of items to process
        processor_func: Function to process each item
        description: Description for progress tracking
        max_workers: Maximum number of workers (optional)
        fail_fast: Whether to stop on first error
        
    Returns:
        List of processing results
    """
    if max_workers:
        processor = ConcurrentAWSProcessor(max_workers=max_workers)
    else:
        processor = get_concurrent_processor()
    
    return processor.process_items(items, processor_func, description, fail_fast)