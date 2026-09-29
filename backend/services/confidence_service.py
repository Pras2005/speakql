from typing import Dict, Any, List

class ConfidenceService:
    def evaluate_confidence(self, sql: str, reasoning_steps: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluates the confidence of the generated SQL.
        Returns a score (0.0 to 1.0) and whether it needs review.
        """
        # Baseline confidence
        score = 0.9
        
        # Simple heuristics for Phase 3:
        # 1. If SQL is very long/complex, reduce confidence slightly
        if len(sql) > 500:
            score -= 0.1
            
        # 2. If SQL contains many joins
        join_count = sql.upper().count("JOIN")
        if join_count > 3:
            score -= 0.1
        if join_count > 5:
            score -= 0.1
            
        return {
            "score": round(max(0.0, score), 2),
            "needs_review": score < 0.7
        }
