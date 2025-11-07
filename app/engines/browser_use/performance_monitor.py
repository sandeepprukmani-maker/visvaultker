"""
Performance Monitoring and Metrics Tracking
Tracks automation performance, timing, and resource usage
"""
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Monitor and track performance metrics for browser automation
    Tracks timing, success rates, and resource usage
    """
    
    def __init__(self, track_detailed_metrics: bool = True):
        """
        Initialize performance monitor
        
        Args:
            track_detailed_metrics: Track detailed per-operation metrics
        """
        self.track_detailed_metrics = track_detailed_metrics
        self.metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "total_duration": 0.0,
            "start_time": datetime.now().isoformat()
        }
        
        self.operation_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "success_count": 0,
            "fail_count": 0,
            "total_duration": 0.0,
            "min_duration": float('inf'),
            "max_duration": 0.0
        })
        
        self.timing_stack: List[Dict[str, Any]] = []
        
        logger.info("📊 Performance monitor initialized")
    
    def start_operation(self, operation_name: str) -> str:
        """
        Start tracking an operation
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Operation ID for stopping later
        """
        operation_id = f"{operation_name}_{len(self.timing_stack)}"
        
        timing_info = {
            "operation_id": operation_id,
            "operation_name": operation_name,
            "start_time": time.time(),
            "start_timestamp": datetime.now().isoformat()
        }
        
        self.timing_stack.append(timing_info)
        
        if self.track_detailed_metrics:
            logger.debug(f"⏱️  Started: {operation_name}")
        
        return operation_id
    
    def end_operation(self, operation_id: str, success: bool = True, metadata: Optional[Dict] = None):
        """
        End tracking an operation
        
        Args:
            operation_id: ID returned from start_operation
            success: Whether operation succeeded
            metadata: Optional metadata about the operation
        """
        if not self.timing_stack:
            logger.warning("⚠️  No operation to end")
            return
        
        timing_info = self.timing_stack.pop()
        
        if timing_info["operation_id"] != operation_id:
            logger.warning(f"⚠️  Operation ID mismatch: expected {timing_info['operation_id']}, got {operation_id}")
        
        duration = time.time() - timing_info["start_time"]
        operation_name = timing_info["operation_name"]
        
        self.metrics["total_operations"] += 1
        self.metrics["total_duration"] += duration
        
        if success:
            self.metrics["successful_operations"] += 1
        else:
            self.metrics["failed_operations"] += 1
        
        op_metrics = self.operation_metrics[operation_name]
        op_metrics["count"] += 1
        op_metrics["total_duration"] += duration
        op_metrics["min_duration"] = min(op_metrics["min_duration"], duration)
        op_metrics["max_duration"] = max(op_metrics["max_duration"], duration)
        
        if success:
            op_metrics["success_count"] += 1
        else:
            op_metrics["fail_count"] += 1
        
        if self.track_detailed_metrics:
            status = "✅" if success else "❌"
            logger.info(f"{status} {operation_name} completed in {duration:.2f}s")
    
    def record_metric(self, metric_name: str, value: Any):
        """
        Record a custom metric
        
        Args:
            metric_name: Name of the metric
            value: Metric value
        """
        if "custom_metrics" not in self.metrics:
            self.metrics["custom_metrics"] = {}
        
        self.metrics["custom_metrics"][metric_name] = value
        
        if self.track_detailed_metrics:
            logger.debug(f"📊 Metric recorded: {metric_name} = {value}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get performance summary
        
        Returns:
            Dictionary with performance metrics
        """
        total_ops = self.metrics["total_operations"]
        
        summary = {
            "overview": {
                "total_operations": total_ops,
                "successful_operations": self.metrics["successful_operations"],
                "failed_operations": self.metrics["failed_operations"],
                "success_rate": (self.metrics["successful_operations"] / max(total_ops, 1)) * 100,
                "total_duration": self.metrics["total_duration"],
                "average_duration": self.metrics["total_duration"] / max(total_ops, 1),
                "start_time": self.metrics["start_time"],
                "current_time": datetime.now().isoformat()
            },
            "operation_breakdown": {}
        }
        
        for op_name, op_metrics in self.operation_metrics.items():
            count = op_metrics["count"]
            summary["operation_breakdown"][op_name] = {
                "count": count,
                "success_count": op_metrics["success_count"],
                "fail_count": op_metrics["fail_count"],
                "success_rate": (op_metrics["success_count"] / max(count, 1)) * 100,
                "total_duration": op_metrics["total_duration"],
                "average_duration": op_metrics["total_duration"] / max(count, 1),
                "min_duration": op_metrics["min_duration"] if op_metrics["min_duration"] != float('inf') else 0,
                "max_duration": op_metrics["max_duration"]
            }
        
        if "custom_metrics" in self.metrics:
            summary["custom_metrics"] = self.metrics["custom_metrics"]
        
        return summary
    
    def get_top_slowest_operations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the slowest operations
        
        Args:
            limit: Number of operations to return
            
        Returns:
            List of slowest operations with metrics
        """
        operations = []
        
        for op_name, op_metrics in self.operation_metrics.items():
            if op_metrics["count"] > 0:
                avg_duration = op_metrics["total_duration"] / op_metrics["count"]
                operations.append({
                    "operation": op_name,
                    "average_duration": avg_duration,
                    "max_duration": op_metrics["max_duration"],
                    "count": op_metrics["count"]
                })
        
        operations.sort(key=lambda x: x["average_duration"], reverse=True)
        return operations[:limit]
    
    def reset(self):
        """Reset all metrics"""
        self.metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "total_duration": 0.0,
            "start_time": datetime.now().isoformat()
        }
        self.operation_metrics.clear()
        self.timing_stack.clear()
        
        logger.info("🔄 Performance metrics reset")
    
    def log_summary(self):
        """Log a formatted summary of metrics"""
        summary = self.get_summary()
        
        logger.info("=" * 80)
        logger.info("📊 PERFORMANCE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Operations: {summary['overview']['total_operations']}")
        logger.info(f"Success Rate: {summary['overview']['success_rate']:.1f}%")
        logger.info(f"Total Duration: {summary['overview']['total_duration']:.2f}s")
        logger.info(f"Average Duration: {summary['overview']['average_duration']:.2f}s")
        
        if summary['operation_breakdown']:
            logger.info("\n📋 Operation Breakdown:")
            for op_name, metrics in summary['operation_breakdown'].items():
                logger.info(f"  • {op_name}: {metrics['count']} ops, "
                          f"avg {metrics['average_duration']:.2f}s, "
                          f"success {metrics['success_rate']:.1f}%")
        
        logger.info("=" * 80)
