import logging
import sqlglot
from sqlglot import exp
from typing import Optional, Dict, Any, List
from services.database_service import DatabaseService
from services.policy_service import PolicyService
from services.risk_service import RiskScoringService
from services.approval_service import ApprovalService
from services.masking_service import MaskingService
from services.confidence_service import ConfidenceService
from utils.sql_safety import validate_sql_safety, extract_tables
from core.request_context import get_request_context
from utils.utils import run_with_timeout
from models.tenant_model import DatabaseAccessLevel

logger = logging.getLogger(__name__)

_WRITE_TYPES = (
    exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter,
    exp.Create, exp.Grant, exp.Revoke,
)
_READ_TYPES = (exp.Select, exp.Show, exp.Describe, exp.With)


def _is_write_sql(sql: str) -> bool:
    """Returns True if the SQL is a write/DDL statement, using AST-based detection."""
    try:
        expressions = sqlglot.parse(sql)
        if not expressions:
            return False
        expression = expressions[0]
        if not expression:
            return False
        # Any dangerous node anywhere, or not a read-only top-level type
        if any(True for _ in expression.find_all(_WRITE_TYPES)):
            return True
        return not isinstance(expression, _READ_TYPES)
    except Exception as exc:
        logger.warning("Failed to parse SQL for write detection: %s", exc)
        return False


def _inject_limit(sql: str, limit: int) -> str:
    """Injects a LIMIT clause using AST manipulation (safe, not string-based)."""
    try:
        expression = sqlglot.parse_one(sql, read="postgres")
        if isinstance(expression, exp.Select):
            existing_limit = expression.find(exp.Limit)
            if existing_limit is None:
                expression = expression.limit(limit)
            else:
                # Enforce the policy limit if it's stricter than the existing one
                try:
                    existing_value = int(existing_limit.this.this)
                    if limit < existing_value:
                        expression = expression.limit(limit)
                except (AttributeError, ValueError):
                    expression = expression.limit(limit)
            return expression.sql(dialect="postgres")
    except Exception as exc:
        logger.warning("AST limit injection failed, falling back to string append: %s", exc)
    # Fallback: string-based (only if AST fails)
    if "LIMIT" not in sql.upper():
        return sql.rstrip(";") + f" LIMIT {limit};"
    return sql


class GovernanceService:
    def __init__(
        self,
        db_service: DatabaseService,
        policy_service: PolicyService,
        risk_service: RiskScoringService,
        approval_service: ApprovalService,
        masking_service: MaskingService,
        confidence_service: ConfidenceService
    ):
        self.db_service = db_service
        self.policy_service = policy_service
        self.risk_service = risk_service
        self.approval_service = approval_service
        self.masking_service = masking_service
        self.confidence_service = confidence_service

    async def execute_governed_query(
        self,
        db_id: int,
        user_id: int,
        sql: str,
        original_prompt: Optional[str] = None,
        agent_tools: Any = None,
        bypass_approval: bool = False,
        sql_rationale: Optional[str] = None,
        required_access_level: DatabaseAccessLevel = DatabaseAccessLevel.QUERY,
        skip_access_check: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes a query through the full governance pipeline:
        AST validate -> Policy check -> Risk evaluate -> Confidence? -> Approval? -> Audit -> Execute -> Mask

        Set skip_access_check=True when the caller has already verified access (avoids double DB hit).
        """
        context = get_request_context()
        workspace_id = context.workspace_id

        # Access check (callers can skip if they've already checked to avoid duplicate queries)
        if not skip_access_check:
            has_access = await self.db_service.has_database_access(
                db_id, user_id, required_access_level
            )
            if not has_access:
                error_msg = f"Permission denied: {required_access_level.value} access required"
                qh = await self.db_service.log_query(
                    db_id=db_id,
                    user_id=user_id,
                    event_type="execution",
                    prompt=original_prompt,
                    executed_sql=sql,
                    success=False,
                    error=error_msg,
                )
                return {"error": error_msg, "status": "denied", "query_id": qh.id}

        # 1. AST Validation
        safety_error = validate_sql_safety(sql)
        if safety_error:
            qh = await self.db_service.log_query(
                db_id=db_id, user_id=user_id, event_type="execution",
                prompt=original_prompt, executed_sql=sql, success=False, error=safety_error
            )
            return {"error": safety_error, "status": "blocked", "query_id": qh.id}

        # Determine if it's a write operation for policy context (AST-based, no inline import)
        is_write = _is_write_sql(sql)

        # 2. Policy Evaluation
        policies = await self.policy_service.get_active_policies(workspace_id)
        decision = self.policy_service.evaluate_policy(policies, {
            "sql": sql,
            "user_role": context.role,
            "is_write": is_write
        })

        policy_outcome = {
            "allowed": decision["allowed"],
            "reason": decision["reason"],
            "policy_id": decision.get("policy_id")
        }

        if not decision["allowed"]:
            error_msg = f"Policy Denied: {decision['reason']}"
            qh = await self.db_service.log_query(
                db_id=db_id, user_id=user_id, event_type="execution",
                prompt=original_prompt, executed_sql=sql, success=False, error=error_msg
            )
            return {
                "error": error_msg,
                "status": "denied",
                "query_id": qh.id,
                "explainability": {
                    "tables_referenced": list(extract_tables(sql)),
                    "policy_outcome": policy_outcome,
                    "risk_metadata": {"score": 0.0, "flags": []},
                    "confidence_score": 0.0,
                    "needs_review": True
                }
            }

        # 3. Risk Evaluation
        risk_result = self.risk_service.evaluate_risk(sql)
        risk_metadata = {
            "score": risk_result["risk_score"],
            "flags": risk_result["flags"]
        }

        # 3b. Confidence Evaluation
        conf_result = self.confidence_service.evaluate_confidence(sql)

        # 4. Approval check
        confidence_threshold = 0.7
        is_low_confidence = conf_result["score"] < confidence_threshold

        if (risk_result["requires_approval"] or is_low_confidence) and not bypass_approval:
            # Create approval request
            app_req = await self.approval_service.request_approval(
                workspace_id=workspace_id,
                requester_id=user_id,
                db_id=db_id,
                sql=sql,
                risk_score=risk_result["risk_score"],
                prompt=original_prompt
            )

            reason = "High risk" if risk_result["requires_approval"] else "Low confidence"
            if risk_result["requires_approval"] and is_low_confidence:
                reason = "High risk and low confidence"

            msg = f"{reason} query requires approval. Risk: {risk_result['risk_score']}, Confidence: {conf_result['score']}"

            qh = await self.db_service.log_query(
                db_id=db_id, user_id=user_id, event_type="execution",
                prompt=original_prompt, executed_sql=sql, success=False, error=msg
            )

            # Log specific audit event for approval request
            await self.db_service.audit_service.record_event(
                event_type="APPROVAL_REQUESTED",
                user_id=user_id,
                details={
                    "approval_id": app_req.id,
                    "risk_score": risk_result["risk_score"],
                    "confidence_score": conf_result["score"],
                    "reason": reason
                }
            )

            return {
                "status": "approval_required",
                "approval_id": app_req.id,
                "error": msg,
                "query_id": qh.id,
                "explainability": {
                    "tables_referenced": list(extract_tables(sql)),
                    "policy_outcome": policy_outcome,
                    "risk_metadata": risk_metadata,
                    "confidence_score": conf_result["score"],
                    "needs_review": True
                }
            }

        # 5. Apply Policy Transformations (e.g. Row Limits) — AST-based injection
        final_sql = sql
        if decision.get("limit_rows"):
            final_sql = _inject_limit(sql, decision["limit_rows"])

        # 6. Execution
        if not agent_tools:
            return {"error": "Internal error: agent_tools required for execution", "status": "error"}

        timeout = decision.get("timeout") or 15
        result = await run_with_timeout(agent_tools.execute_query, final_sql, timeout_seconds=timeout)

        if result is None:
            err = "Execution timed out"
            qh = await self.db_service.log_query(
                db_id=db_id, user_id=user_id, event_type="execution",
                prompt=original_prompt, executed_sql=sql, success=False, error=err
            )
            return {
                "error": err,
                "status": "timeout",
                "query_id": qh.id,
                "explainability": {
                    "tables_referenced": list(extract_tables(sql)),
                    "policy_outcome": policy_outcome,
                    "risk_metadata": risk_metadata,
                    "confidence_score": conf_result["score"],
                    "needs_review": conf_result["needs_review"]
                }
            }

        if isinstance(result, dict) and "error" in result:
            qh = await self.db_service.log_query(
                db_id=db_id, user_id=user_id, event_type="execution",
                prompt=original_prompt, executed_sql=sql, success=False, error=result["error"]
            )
            return {
                "error": result["error"],
                "status": "error",
                "query_id": qh.id,
                "explainability": {
                    "tables_referenced": list(extract_tables(sql)),
                    "policy_outcome": policy_outcome,
                    "risk_metadata": risk_metadata,
                    "confidence_score": conf_result["score"],
                    "needs_review": conf_result["needs_review"]
                }
            }

        # 7. Result Size Cap
        if isinstance(result, list):
            size_cap = decision.get("size_cap")
            if size_cap and len(result) > size_cap:
                err = f"Result set size ({len(result)}) exceeds policy cap ({size_cap})"
                qh = await self.db_service.log_query(
                    db_id=db_id, user_id=user_id, event_type="execution",
                    prompt=original_prompt, executed_sql=sql, success=False, error=err
                )
                return {
                    "error": err,
                    "status": "denied",
                    "query_id": qh.id,
                    "explainability": {
                        "tables_referenced": list(extract_tables(sql)),
                        "policy_outcome": policy_outcome,
                        "risk_metadata": risk_metadata,
                        "confidence_score": conf_result["score"],
                        "needs_review": conf_result["needs_review"]
                    }
                }

        # 8. Result Masking
        if isinstance(result, list):
            tables = extract_tables(sql)
            table_rules = await self.masking_service.sensitivity_service.get_applicable_rules(workspace_id, list(tables))
            result = self.masking_service.mask_results(result, table_rules, context.role)

        # 9. Success Audit
        qh = await self.db_service.log_query(
            db_id=db_id, user_id=user_id, event_type="execution",
            prompt=original_prompt, executed_sql=sql, success=True
        )

        return {
            "status": "success",
            "result": result,
            "query_id": qh.id,
            "explainability": {
                "sql_rationale": sql_rationale or "Query executed successfully",
                "tables_referenced": list(extract_tables(sql)),
                "policy_outcome": policy_outcome,
                "risk_metadata": risk_metadata,
                "confidence_score": conf_result["score"],
                "needs_review": conf_result["needs_review"]
            }
        }
