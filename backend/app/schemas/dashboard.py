from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

from .common import BaseResponse, TimeGrouping

class KPIMetric(BaseModel):
    name: str
    value: float
    previous_value: Optional[float] = None
    change_percentage: Optional[float] = None
    trend: Optional[str] = None  # "up", "down", "stable"
    format: str = "number"  # "number", "percentage", "currency"
    
class DashboardKPIs(BaseModel):
    total_checks: KPIMetric
    average_score: KPIMetric
    low_score_alerts: KPIMetric
    active_branches: KPIMetric
    checks_this_week: KPIMetric
    score_improvement: KPIMetric

class TrendPoint(BaseModel):
    date: datetime
    value: float
    count: int
    label: str

class TrendData(BaseModel):
    period: TimeGrouping
    points: List[TrendPoint]
    total_points: int
    average_value: float
    trend_direction: str  # "up", "down", "stable"

class BranchPerformance(BaseModel):
    branch_id: int
    branch_name: str
    total_checks: int
    average_score: float
    last_check_date: Optional[datetime]
    low_score_count: int
    score_trend: str  # "improving", "declining", "stable"
    rank: int

class ChefPerformance(BaseModel):
    chef_name: str
    branch_name: str
    total_checks: int
    average_score: float
    best_dish: Optional[str] = None
    improvement_area: Optional[str] = None

class DishPerformance(BaseModel):
    dish_name: str
    total_checks: int
    average_score: float
    branches_served: List[str]
    best_branch: Optional[str] = None
    lowest_scoring_branch: Optional[str] = None

class ScoreDistribution(BaseModel):
    score_range: str  # "1-2", "3-4", etc.
    count: int
    percentage: float

class AlertItem(BaseModel):
    id: int
    type: str  # "low_score", "no_recent_checks", etc.
    severity: str  # "low", "medium", "high", "critical"
    title: str
    description: str
    branch_name: Optional[str] = None
    created_at: datetime
    is_acknowledged: bool = False

class ComparisonPeriod(BaseModel):
    current_period: Dict[str, Any]
    previous_period: Dict[str, Any]
    comparison: Dict[str, float]  # percentage changes

class DashboardSummary(BaseModel):
    kpis: DashboardKPIs
    trends: TrendData
    top_branches: List[BranchPerformance]
    bottom_branches: List[BranchPerformance]
    recent_alerts: List[AlertItem]
    score_distribution: List[ScoreDistribution]

class BranchComparison(BaseModel):
    branches: List[BranchPerformance]
    metrics: List[str]
    time_period: str
    generated_at: datetime

class TimeBasedAnalysis(BaseModel):
    hourly_patterns: Dict[str, float]  # Hour -> average score
    daily_patterns: Dict[str, float]   # Day of week -> average score
    monthly_trends: List[TrendPoint]
    seasonal_insights: Dict[str, str]

class QualityInsights(BaseModel):
    summary: str
    key_findings: List[str]
    recommendations: List[str]
    risk_areas: List[str]
    success_stories: List[str]

class ExportRequest(BaseModel):
    format: str = "xlsx"  # "csv", "xlsx", "pdf"
    include_charts: bool = True
    date_range: Optional[Dict[str, datetime]] = None
    branches: Optional[List[str]] = None
    email_recipients: Optional[List[str]] = None

class DashboardResponse(BaseResponse):
    data: Optional[DashboardSummary] = None

class TrendsResponse(BaseResponse):
    data: Optional[TrendData] = None

class BranchComparisonResponse(BaseResponse):
    data: Optional[BranchComparison] = None

class AlertsResponse(BaseResponse):
    data: Optional[List[AlertItem]] = None

class InsightsResponse(BaseResponse):
    data: Optional[QualityInsights] = None
