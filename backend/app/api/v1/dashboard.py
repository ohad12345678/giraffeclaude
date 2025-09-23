from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ...utils.database import get_db
from ...utils.dependencies import get_current_active_user
from ...services.claude_service import ClaudeService
from ...schemas.dashboard import (
    DashboardResponse, TrendsResponse, BranchComparisonResponse,
    InsightsResponse, AlertsResponse, DashboardSummary, 
    DashboardKPIs, KPIMetric, BranchPerformance, AlertItem
)
from ...schemas.common import TimeGrouping
from ...models.user import User
from ...models.quality_check import QualityCheck, CheckStatus
from ...models.branch import Branch
from ...utils.config import settings

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("", response_model=DashboardResponse)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get complete dashboard summary"""
    
    # Get user's accessible branches
    accessible_branches = _get_user_accessible_branches(current_user, db)
    
    # Calculate KPIs
    kpis = _calculate_kpis(db, accessible_branches)
    
    # Get top and bottom performing branches
    branch_performance = _get_branch_performance(db, accessible_branches)
    top_branches = sorted(branch_performance, key=lambda x: x.average_score, reverse=True)[:5]
    bottom_branches = sorted(branch_performance, key=lambda x: x.average_score)[:5]
    
    # Get recent alerts
    recent_alerts = _get_recent_alerts(db, accessible_branches)
    
    # Get score distribution
    score_distribution = _get_score_distribution(db, accessible_branches)
    
    # Get trends (simplified for summary)
    trends = _get_simple_trends(db, accessible_branches)
    
    dashboard_summary = DashboardSummary(
        kpis=kpis,
        trends=trends,
        top_branches=top_branches,
        bottom_branches=bottom_branches,
        recent_alerts=recent_alerts,
        score_distribution=score_distribution
    )
    
    return DashboardResponse(
        status="success",
        data=dashboard_summary
    )

@router.get("/kpis")
async def get_kpis(
    period_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get key performance indicators"""
    
    accessible_branches = _get_user_accessible_branches(current_user, db)
    kpis = _calculate_kpis(db, accessible_branches, period_days)
    
    return {"status": "success", "data": kpis}

@router.get("/trends", response_model=TrendsResponse)
async def get_trends(
    period_days: int = Query(30, ge=7, le=365),
    grouping: TimeGrouping = Query(TimeGrouping.DAY),
    branch_ids: Optional[List[int]] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get quality trends over time"""
    
    accessible_branches = _get_user_accessible_branches(current_user, db)
    
    # Filter by specific branches if requested
    if branch_ids:
        accessible_branches = [b for b in accessible_branches if b.id in branch_ids]
    
    trends = _get_detailed_trends(db, accessible_branches, period_days, grouping)
    
    return TrendsResponse(
        status="success",
        data=trends
    )

@router.get("/branch-comparison", response_model=BranchComparisonResponse)
async def get_branch_comparison(
    period_days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Compare branch performances"""
    
    accessible_branches = _get_user_accessible_branches(current_user, db)
    branch_performance = _get_branch_performance(db, accessible_branches, period_days)
    
    from ...schemas.dashboard import BranchComparison
    comparison = BranchComparison(
        branches=branch_performance,
        metrics=["average_score", "total_checks", "low_score_count"],
        time_period=f"Last {period_days} days",
        generated_at=datetime.utcnow()
    )
    
    return BranchComparisonResponse(
        status="success",
        data=comparison
    )

@router.get("/alerts", response_model=AlertsResponse)
async def get_alerts(
    days_back: int = Query(7, ge=1, le=30),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get quality alerts"""
    
    accessible_branches = _get_user_accessible_branches(current_user, db)
    alerts = _get_recent_alerts(db, accessible_branches, days_back, severity)
    
    return AlertsResponse(
        status="success",
        data=alerts
    )

@router.post("/insights", response_model=InsightsResponse)
async def get_ai_insights(
    period_days: int = Query(30, ge=7, le=90),
    branches: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered quality insights using Claude"""
    
    # Check if user has AI access permission
    if not current_user.has_permission("can_access_ai"):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI insights access not permitted"
        )
    
    claude_service = ClaudeService(db)
    
    # Filter branches by user access
    accessible_branch_names = [b.name for b in _get_user_accessible_branches(current_user, db)]
    if branches:
        branches = [b for b in branches if b in accessible_branch_names]
    else:
        branches = accessible_branch_names
    
    insights = await claude_service.analyze_trends(period_days, branches)
    
    from ...schemas.dashboard import QualityInsights
    quality_insights = QualityInsights(
        summary=insights.get("summary", "No insights available"),
        key_findings=insights.get("positive_trends", []),
        recommendations=insights.get("recommendations", []),
        risk_areas=insights.get("concerns", []),
        success_stories=insights.get("branch_insights", {})
    )
    
    return InsightsResponse(
        status="success",
        data=quality_insights
    )

@router.post("/ask-claude")
async def ask_claude_question(
    question: str,
    context_days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Ask Claude AI a specific question about quality data"""
    
    if not current_user.has_permission("can_access_ai"):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI access not permitted"
        )
    
    claude_service = ClaudeService(db)
    response = await claude_service.answer_question(question, context_days)
    
    return {"status": "success", "data": response}

# Helper functions

def _get_user_accessible_branches(user: User, db: Session) -> List[Branch]:
    """Get branches user has access to"""
    if user.has_permission("can_view_all_branches"):
        return db.query(Branch).filter(Branch.is_active == True).all()
    
    if not user.assigned_branches:
        return []
    
    return db.query(Branch).filter(
        Branch.name.in_(user.assigned_branches),
        Branch.is_active == True
    ).all()

def _calculate_kpis(db: Session, accessible_branches: List[Branch], period_days: int = 30) -> DashboardKPIs:
    """Calculate key performance indicators"""
    
    if not accessible_branches:
        return DashboardKPIs(
            total_checks=KPIMetric(name="Total Checks", value=0),
            average_score=KPIMetric(name="Average Score", value=0),
            low_score_alerts=KPIMetric(name="Low Score Alerts", value=0),
            active_branches=KPIMetric(name="Active Branches", value=0),
            checks_this_week=KPIMetric(name="Checks This Week", value=0),
            score_improvement=KPIMetric(name="Score Improvement", value=0)
        )
    
    branch_ids = [b.id for b in accessible_branches]
    
    # Current period
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    current_checks = db.query(QualityCheck).filter(
        QualityCheck.branch_id.in_(branch_ids),
        QualityCheck.created_at >= start_date
    ).all()
    
    # Previous period for comparison
    prev_start = start_date - timedelta(days=period_days)
    prev_checks = db.query(QualityCheck).filter(
        QualityCheck.branch_id.in_(branch_ids),
        QualityCheck.created_at >= prev_start,
        QualityCheck.created_at < start_date
    ).all()
    
    # This week
    week_start = end_date - timedelta(days=7)
    week_checks = db.query(QualityCheck).filter(
        QualityCheck.branch_id.in_(branch_ids),
        QualityCheck.created_at >= week_start
    ).count()
    
    # Calculate metrics
    total_checks = len(current_checks)
    avg_score = sum(c.overall_score for c in current_checks) / total_checks if current_checks else 0
    low_score_alerts = len([c for c in current_checks if c.overall_score < settings.ALERT_THRESHOLD])
    
    # Previous period comparison
    prev_avg = sum(c.overall_score for c in prev_checks) / len(prev_checks) if prev_checks else 0
    score_improvement = ((avg_score - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0
    
    return DashboardKPIs(
        total_checks=KPIMetric(name="Total Checks", value=total_checks, format="number"),
        average_score=KPIMetric(name="Average Score", value=round(avg_score, 2), format="number"),
        low_score_alerts=KPIMetric(name="Low Score Alerts", value=low_score_alerts, format="number"),
        active_branches=KPIMetric(name="Active Branches", value=len(accessible_branches), format="number"),
        checks_this_week=KPIMetric(name="Checks This Week", value=week_checks, format="number"),
        score_improvement=KPIMetric(name="Score Improvement", value=round(score_improvement, 1), format="percentage")
    )

def _get_branch_performance(db: Session, accessible_branches: List[Branch], period_days: int = 30) -> List[BranchPerformance]:
    """Get branch performance data"""
    
    branch_performance = []
    
    for i, branch in enumerate(accessible_branches):
        # Get recent checks for this branch
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        checks = db.query(QualityCheck).filter(
            QualityCheck.branch_id == branch.id,
            QualityCheck.created_at >= start_date
        ).all()
        
        total_checks = len(checks)
        avg_score = sum(c.overall_score for c in checks) / total_checks if checks else 0
        low_score_count = len([c for c in checks if c.overall_score < settings.ALERT_THRESHOLD])
        last_check_date = max((c.created_at for c in checks), default=None)
        
        branch_performance.append(BranchPerformance(
            branch_id=branch.id,
            branch_name=branch.name,
            total_checks=total_checks,
            average_score=round(avg_score, 2),
            last_check_date=last_check_date,
            low_score_count=low_score_count,
            score_trend="stable",  # Simplified - could calculate actual trend
            rank=i + 1  # Will be recalculated after sorting
        ))
    
    # Update ranks based on average score
    branch_performance.sort(key=lambda x: x.average_score, reverse=True)
    for i, bp in enumerate(branch_performance):
        bp.rank = i + 1
    
    return branch_performance

def _get_recent_alerts(db: Session, accessible_branches: List[Branch], days_back: int = 7, severity: Optional[str] = None) -> List[AlertItem]:
    """Get recent quality alerts"""
    
    if not accessible_branches:
        return []
    
    branch_ids = [b.id for b in accessible_branches]
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Get low score checks
    low_score_checks = db.query(QualityCheck).filter(
        QualityCheck.branch_id.in_(branch_ids),
        QualityCheck.overall_score < settings.ALERT_THRESHOLD,
        QualityCheck.created_at >= start_date,
        QualityCheck.status.in_([CheckStatus.OPEN, CheckStatus.IN_PROGRESS])
    ).order_by(desc(QualityCheck.created_at)).limit(20).all()
    
    alerts = []
    for check in low_score_checks:
        severity_level = "critical" if check.overall_score <= 3 else "high" if check.overall_score <= 5 else "medium"
        
        if severity and severity_level != severity:
            continue
            
        alerts.append(AlertItem(
            id=check.id,
            type="low_score",
            severity=severity_level,
            title=f"ציון נמוך: {check.dish_name} - {check.overall_score}/10",
            description=f"השף {check.chef_name} קיבל ציון {check.overall_score} עבור {check.dish_name}",
            branch_name=check.branch.name if check.branch else None,
            created_at=check.created_at,
            is_acknowledged=False
        ))
    
    return alerts

def _get_score_distribution(db: Session, accessible_branches: List[Branch]) -> List:
    """Get score distribution data"""
    
    if not accessible_branches:
        return []
    
    branch_ids = [b.id for b in accessible_branches]
    
    # Get all scores from last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    checks = db.query(QualityCheck).filter(
        QualityCheck.branch_id.in_(branch_ids),
        QualityCheck.created_at >= start_date
    ).all()
    
    if not checks:
        return []
    
    # Calculate distribution
    distribution = {}
    total_checks = len(checks)
    
    for score in range(1, 11):
        count = len([c for c in checks if c.overall_score == score])
        percentage = (count / total_checks * 100) if total_checks > 0 else 0
        
        if count > 0:  # Only include scores that have occurrences
            distribution[str(score)] = {
                "score_range": str(score),
                "count": count,
                "percentage": round(percentage, 1)
            }
    
    return list(distribution.values())

def _get_simple_trends(db: Session, accessible_branches: List[Branch]):
    """Get simplified trends for dashboard summary"""
    
    if not accessible_branches:
        return None
    
    branch_ids = [b.id for b in accessible_branches]
    end_date = datetime.utcnow()
    
    # Get last 30 days of data
    trends = []
    for i in range(30):
        day_start = end_date - timedelta(days=i+1)
        day_end = day_start + timedelta(days=1)
        
        day_checks = db.query(QualityCheck).filter(
            QualityCheck.branch_id.in_(branch_ids),
            QualityCheck.created_at >= day_start,
            QualityCheck.created_at < day_end
        ).all()
        
        if day_checks:
            avg_score = sum(c.overall_score for c in day_checks) / len(day_checks)
            trends.append({
                "date": day_start,
                "value": round(avg_score, 2),
                "count": len(day_checks),
                "label": day_start.strftime("%d/%m")
            })
    
    trends.reverse()  # Oldest to newest
    
    from ...schemas.dashboard import TrendData
    return TrendData(
        period=TimeGrouping.DAY,
        points=trends,
        total_points=len(trends),
        average_value=sum(t["value"] for t in trends) / len(trends) if trends else 0,
        trend_direction="stable"
    )

def _get_detailed_trends(db: Session, accessible_branches: List[Branch], period_days: int, grouping: TimeGrouping):
    """Get detailed trends data"""
    # Implementation would depend on specific grouping requirements
    return _get_simple_trends(db, accessible_branches)  # Simplified for now
