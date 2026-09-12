"""
AI Services Package — Phase 10
Provides rule-based SEO intelligence and optional OpenAI-powered recommendations.
"""
from app.services.ai.recommendation_engine import AIRecommendationEngine
from app.services.ai.content_gap_analyzer import ContentGapAnalyzer

__all__ = ["AIRecommendationEngine", "ContentGapAnalyzer"]
