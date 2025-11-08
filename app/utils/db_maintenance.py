"""
Database Maintenance Utilities
Cleanup and pruning for execution history
"""
import logging
from datetime import datetime, timedelta
from app.models import db, ExecutionHistory, GeneratedScript, AutomationPlan, TraceFile

logger = logging.getLogger(__name__)


def prune_old_executions(days_to_keep: int = 30, dry_run: bool = False) -> dict:
    """
    Remove old execution history records to prevent unbounded database growth.
    
    Args:
        days_to_keep: Number of days of history to retain (default: 30)
        dry_run: If True, only count records without deleting
        
    Returns:
        Dictionary with pruning statistics
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count records to be deleted (optimized to avoid loading all into memory)
        execution_count = ExecutionHistory.query.filter(
            ExecutionHistory.created_at < cutoff_date
        ).count()
        
        if execution_count == 0:
            logger.info(f"No execution records older than {days_to_keep} days found")
            return {
                'deleted_executions': 0,
                'deleted_scripts': 0,
                'deleted_plans': 0,
                'deleted_traces': 0,
                'dry_run': dry_run
            }
        
        # Get execution IDs for related record queries
        execution_ids = db.session.query(ExecutionHistory.id).filter(
            ExecutionHistory.created_at < cutoff_date
        ).all()
        execution_ids = [e[0] for e in execution_ids]
        
        scripts_count = GeneratedScript.query.filter(
            GeneratedScript.execution_id.in_(execution_ids)
        ).count()
        
        plans_count = AutomationPlan.query.filter(
            AutomationPlan.execution_id.in_(execution_ids)
        ).count()
        
        traces_count = TraceFile.query.filter(
            TraceFile.execution_id.in_(execution_ids)
        ).count()
        
        if dry_run:
            logger.info(f"[DRY RUN] Would delete {execution_count} executions and {scripts_count} scripts, {plans_count} plans, {traces_count} traces")
            return {
                'deleted_executions': execution_count,
                'deleted_scripts': scripts_count,
                'deleted_plans': plans_count,
                'deleted_traces': traces_count,
                'dry_run': True
            }
        
        # Delete related records first (due to foreign keys)
        GeneratedScript.query.filter(
            GeneratedScript.execution_id.in_(execution_ids)
        ).delete(synchronize_session='fetch')
        
        AutomationPlan.query.filter(
            AutomationPlan.execution_id.in_(execution_ids)
        ).delete(synchronize_session='fetch')
        
        TraceFile.query.filter(
            TraceFile.execution_id.in_(execution_ids)
        ).delete(synchronize_session='fetch')
        
        # Delete execution records
        ExecutionHistory.query.filter(
            ExecutionHistory.created_at < cutoff_date
        ).delete(synchronize_session='fetch')
        
        db.session.commit()
        
        logger.info(f"✅ Deleted {execution_count} executions, {scripts_count} scripts, {plans_count} plans, {traces_count} traces older than {days_to_keep} days")
        
        return {
            'deleted_executions': execution_count,
            'deleted_scripts': scripts_count,
            'deleted_plans': plans_count,
            'deleted_traces': traces_count,
            'dry_run': False
        }
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error pruning old executions: {e}", exc_info=True)
        raise


def get_database_stats() -> dict:
    """
    Get statistics about database size and growth.
    
    Returns:
        Dictionary with database statistics
    """
    try:
        total_executions = ExecutionHistory.query.count()
        total_scripts = GeneratedScript.query.count()
        total_plans = AutomationPlan.query.count()
        total_traces = TraceFile.query.count()
        
        # Get oldest and newest records
        oldest_execution = ExecutionHistory.query.order_by(
            ExecutionHistory.created_at.asc()
        ).first()
        
        newest_execution = ExecutionHistory.query.order_by(
            ExecutionHistory.created_at.desc()
        ).first()
        
        return {
            'total_executions': total_executions,
            'total_scripts': total_scripts,
            'total_plans': total_plans,
            'total_traces': total_traces,
            'oldest_record': oldest_execution.created_at.isoformat() if oldest_execution else None,
            'newest_record': newest_execution.created_at.isoformat() if newest_execution else None
        }
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}", exc_info=True)
        return {}
