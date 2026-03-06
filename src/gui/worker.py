"""
Worker thread implementation using QThreadPool for concurrent task execution.
"""

import sys
import traceback
from typing import Callable, Any, Optional
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot


class WorkerSignals(QObject):
    """Signals available from a running worker thread."""
    finished = pyqtSignal(int)
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(tuple)


class Worker(QRunnable):
    """Worker thread for executing functions in the background."""
    
    def __init__(self, fn: Callable, worker_id: int = 0, *args: Any, **kwargs: Any):
        super().__init__()
        self.fn = fn
        self.worker_id = worker_id
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
        if 'progress_callback' not in self.kwargs:
            self.kwargs['progress_callback'] = self.signals.progress
    
    @pyqtSlot()
    def run(self):
        """Execute the worker function with passed args/kwargs."""
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit(self.worker_id)


class ThreadPoolManager:
    """Manager for QThreadPool with tracking and cleanup capabilities."""
    
    _instance: Optional['ThreadPoolManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        from PyQt6.QtCore import QThreadPool
        self._pool = QThreadPool()
        self._active_workers: set[int] = set()
        self._worker_counter = 0
        self._initialized = True
    
    @property
    def max_thread_count(self) -> int:
        return self._pool.maxThreadCount()
    
    def start(self, fn: Callable, *args: Any, **kwargs: Any) -> Worker:
        """Start a new worker in the thread pool."""
        self._worker_counter += 1
        worker = Worker(fn, self._worker_counter, *args, **kwargs)
        worker.signals.finished.connect(self._on_worker_finished)
        self._active_workers.add(self._worker_counter)
        self._pool.start(worker)
        return worker
    
    def _on_worker_finished(self, worker_id: int):
        self._active_workers.discard(worker_id)
    
    def active_worker_count(self) -> int:
        return len(self._active_workers)
    
    def wait_for_done(self, msecs: int = -1) -> bool:
        return self._pool.waitForDone(msecs)
    
    def clear(self):
        self._pool.clear()
        self._active_workers.clear()


thread_pool = ThreadPoolManager()
