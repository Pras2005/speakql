from typing import List, Optional, Dict, Any
from models.workflow_model import SavedQuery, SavedQueryRun, QueryComment, SavedQueryStatus, SavedQueryVisibility
from repositories.workflow_repository import SavedQueryRepository, QueryCommentRepository
from services.governance_service import GovernanceService
from core.request_context import get_request_context
from datetime import datetime
import sqlglot
from sqlglot import exp

class WorkflowService:
    def __init__(
        self, 
        query_repo: SavedQueryRepository, 
        comment_repo: QueryCommentRepository,
        gov_service: GovernanceService
    ):
        self.query_repo = query_repo
        self.comment_repo = comment_repo
        self.gov_service = gov_service

    async def save_query(
        self, 
        name: str, 
        sql: str, 
        prompt: Optional[str] = None, 
        description: Optional[str] = None,
        tags: Optional[str] = None,
        visibility: SavedQueryVisibility = SavedQueryVisibility.PRIVATE,
        is_template: bool = False
    ) -> SavedQuery:
        context = get_request_context()
        query = SavedQuery(
            workspace_id=context.workspace_id,
            created_by=context.user_id,
            name=name,
            sql=sql,
            prompt=prompt,
            description=description,
            tags=tags,
            visibility=visibility,
            is_template=is_template,
            status=SavedQueryStatus.DRAFT
        )
        saved = await self.query_repo.create(query)
        await self.gov_service.db_service.audit_service.record_event(
            event_type="SAVED_QUERY_CREATED",
            user_id=context.user_id,
            details={"query_id": saved.id, "name": saved.name}
        )
        return saved

    async def get_query(self, query_id: int) -> Optional[SavedQuery]:
        context = get_request_context()
        return await self.query_repo.get_by_id(query_id, context.workspace_id)

    async def update_query(self, query_id: int, updates: Dict[str, Any]) -> Optional[SavedQuery]:
        context = get_request_context()
        query = await self.query_repo.get_by_id(query_id, context.workspace_id)
        if not query:
            return None
        
        for key, value in updates.items():
            if hasattr(query, key):
                setattr(query, key, value)
        
        query.updated_at = datetime.utcnow()
        updated = await self.query_repo.update(query)
        await self.gov_service.db_service.audit_service.record_event(
            event_type="SAVED_QUERY_UPDATED",
            user_id=context.user_id,
            details={"query_id": updated.id, "name": updated.name, "updates": list(updates.keys())}
        )
        return updated

    async def delete_query(self, query_id: int) -> bool:
        context = get_request_context()
        query = await self.query_repo.get_by_id(query_id, context.workspace_id)
        if not query:
            return False
        await self.query_repo.delete(query)
        await self.gov_service.db_service.audit_service.record_event(
            event_type="SAVED_QUERY_DELETED",
            user_id=context.user_id,
            details={"query_id": query_id, "name": query.name}
        )
        return True

    async def submit_for_review(self, query_id: int, reason: Optional[str] = None) -> Optional[SavedQuery]:
        updates = {
            "status": SavedQueryStatus.SUBMITTED,
            "review_reason": reason
        }
        res = await self.update_query(query_id, updates)
        context = get_request_context()
        await self.gov_service.db_service.audit_service.record_event(
            event_type="SAVED_QUERY_SUBMITTED",
            user_id=context.user_id,
            details={"query_id": query_id}
        )
        return res

    async def approve_query(self, query_id: int, reviewer_id: int, reason: Optional[str] = None) -> Optional[SavedQuery]:
        # Role check should be in router, but we check workspace here via update_query
        updates = {
            "status": SavedQueryStatus.APPROVED,
            "reviewed_by": reviewer_id,
            "reviewed_at": datetime.utcnow(),
            "review_reason": reason
        }
        res = await self.update_query(query_id, updates)
        if res:
            await self.gov_service.db_service.audit_service.record_event(
                event_type="SAVED_QUERY_APPROVED",
                user_id=reviewer_id,
                details={"query_id": query_id}
            )
        return res

    async def reject_query(self, query_id: int, reviewer_id: int, reason: str) -> Optional[SavedQuery]:
        updates = {
            "status": SavedQueryStatus.REJECTED,
            "reviewed_by": reviewer_id,
            "reviewed_at": datetime.utcnow(),
            "review_reason": reason
        }
        res = await self.update_query(query_id, updates)
        if res:
            await self.gov_service.db_service.audit_service.record_event(
                event_type="SAVED_QUERY_REJECTED",
                user_id=reviewer_id,
                details={"query_id": query_id, "reason": reason}
            )
        return res

    async def archive_query(self, query_id: int) -> Optional[SavedQuery]:
        updates = {"status": SavedQueryStatus.ARCHIVED}
        res = await self.update_query(query_id, updates)
        if res:
            context = get_request_context()
            await self.gov_service.db_service.audit_service.record_event(
                event_type="SAVED_QUERY_ARCHIVED",
                user_id=context.user_id,
                details={"query_id": query_id}
            )
        return res

    async def list_queries(
        self, 
        include_private=True, 
        search: Optional[str] = None,
        status: Optional[SavedQueryStatus] = None,
        visibility: Optional[SavedQueryVisibility] = None,
        owner_id: Optional[int] = None
    ) -> List[SavedQuery]:
        context = get_request_context()
        return await self.query_repo.list_by_workspace(
            context.workspace_id, 
            include_private=include_private,
            user_id=context.user_id,
            search=search,
            status=status,
            visibility=visibility,
            owner_id=owner_id
        )

    async def replay_query(
        self, 
        query_id: int, 
        db_id: int, 
        agent_tools: Any,
        bypass_approval: bool = False
    ) -> Dict[str, Any]:
        context = get_request_context()
        query = await self.query_repo.get_by_id(query_id, context.workspace_id)
        if not query:
            return {"error": "Saved query not found", "status": "error"}
            
        # 1. Execute via GovernanceService
        result = await self.gov_service.execute_governed_query(
            db_id=db_id,
            user_id=context.user_id,
            sql=query.sql,
            original_prompt=query.prompt,
            agent_tools=agent_tools,
            bypass_approval=bypass_approval,
            sql_rationale=f"Replay of saved query: {query.name}"
        )
        
        if result.get("status") == "success":
            # 2. Record the run with snapshot
            import hashlib
            import json
            
            result_data = result.get("result", [])
            row_count = len(result_data) if isinstance(result_data, list) else 0
            
            # Simple result snapshot (hash of the first 100 rows to detect drift)
            snapshot_payload = json.dumps(result_data[:100], sort_keys=True)
            snapshot_ref = hashlib.sha256(snapshot_payload.encode()).hexdigest()
            
            run = SavedQueryRun(
                saved_query_id=query.id,
                workspace_id=context.workspace_id,
                run_by=context.user_id,
                row_count=row_count,
                result_snapshot_ref=snapshot_ref,
                sql_metadata=self._extract_sql_metadata(query.sql)
            )
            await self.query_repo.create_run(run)
            
            # 3. Audit the replay
            await self.gov_service.db_service.audit_service.record_event(
                event_type="SAVED_QUERY_REPLAYED",
                user_id=context.user_id,
                details={
                    "query_id": query.id,
                    "query_name": query.name,
                    "db_id": db_id,
                    "row_count": run.row_count
                }
            )
            
        return result

    def _extract_sql_metadata(self, sql: str) -> Dict[str, Any]:
        """Extracts structural metadata from SQL for diffing."""
        try:
            parsed = sqlglot.parse_one(sql)
            tables = [t.name for t in parsed.find_all(exp.Table)]
            joins = [j.find(exp.Table).name for j in parsed.find_all(exp.Join) if j.find(exp.Table)]
            ctes = [cte.alias for cte in parsed.find_all(exp.CTE)]
            
            # Extract basic clause info
            metadata = {
                "tables": sorted(list(set(tables))),
                "joins": sorted(list(set(joins))),
                "ctes": sorted(list(set(ctes))),
                "has_where": bool(parsed.find(exp.Where)),
                "has_group_by": bool(parsed.find(exp.Group)),
                "has_order_by": bool(parsed.find(exp.Order)),
                "has_limit": bool(parsed.find(exp.Limit)),
                "has_aggregates": bool(parsed.find(exp.AggFunc)),
                "columns": [c.name for c in parsed.find_all(exp.Column)][:50]
            }
            return metadata
        except:
            return {"error": "SQL parsing failed"}

    async def compute_sql_diff(self, sql_a: str, sql_b: str) -> Dict[str, Any]:
        """Computes structural diff between two SQL queries."""
        meta_a = self._extract_sql_metadata(sql_a)
        meta_b = self._extract_sql_metadata(sql_b)
        
        if "error" in meta_a or "error" in meta_b:
            return {"error": "Could not parse one or both queries"}
            
        diff = {
            "added_tables": list(set(meta_b["tables"]) - set(meta_a["tables"])),
            "removed_tables": list(set(meta_a["tables"]) - set(meta_b["tables"])),
            "added_joins": list(set(meta_b["joins"]) - set(meta_a["joins"])),
            "removed_joins": list(set(meta_a["joins"]) - set(meta_b["joins"])),
            "clause_changes": {
                "where": meta_a["has_where"] != meta_b["has_where"],
                "group_by": meta_a["has_group_by"] != meta_b["has_group_by"],
                "order_by": meta_a["has_order_by"] != meta_b["has_order_by"],
                "limit": meta_a["has_limit"] != meta_b["has_limit"],
                "aggregates": meta_a["has_aggregates"] != meta_b["has_aggregates"]
            }
        }
        return diff

    async def compute_result_diff(self, run_a_id: int, run_b_id: int) -> Dict[str, Any]:
        """Computes summary diff between two query runs."""
        context = get_request_context()
        # Direct session access should also be isolated
        from sqlmodel import select
        res_a = await self.query_repo.session.execute(
            select(SavedQueryRun).where(SavedQueryRun.id == run_a_id).where(SavedQueryRun.workspace_id == context.workspace_id)
        )
        run_a = res_a.scalar_one_or_none()
        
        res_b = await self.query_repo.session.execute(
            select(SavedQueryRun).where(SavedQueryRun.id == run_b_id).where(SavedQueryRun.workspace_id == context.workspace_id)
        )
        run_b = res_b.scalar_one_or_none()
        
        if not run_a or not run_b:
            return {"error": "One or both runs not found or access denied"}
            
        diff = {
            "row_count_diff": (run_b.row_count or 0) - (run_a.row_count or 0),
            "executed_at_diff_seconds": (run_b.executed_at - run_a.executed_at).total_seconds(),
            "snapshot_drift": run_a.result_snapshot_ref != run_b.result_snapshot_ref
        }
        return diff

    async def add_comment(self, query_id: int, body: str) -> QueryComment:
        context = get_request_context()
        # Ensure query belongs to workspace before commenting
        query = await self.query_repo.get_by_id(query_id, context.workspace_id)
        if not query:
            raise ValueError("Query not found or access denied")

        comment = QueryComment(
            workspace_id=context.workspace_id,
            saved_query_id=query_id,
            user_id=context.user_id,
            body=body
        )
        saved = await self.comment_repo.create(comment)
        await self.gov_service.db_service.audit_service.record_event(
            event_type="QUERY_COMMENT_CREATED",
            user_id=context.user_id,
            details={"query_id": query_id, "comment_id": saved.id}
        )
        return saved

    async def delete_comment(self, comment_id: int) -> bool:
        context = get_request_context()
        comment = await self.comment_repo.get_by_id(comment_id, context.workspace_id)
        if not comment:
            return False
        await self.comment_repo.delete(comment)
        await self.gov_service.db_service.audit_service.record_event(
            event_type="QUERY_COMMENT_DELETED",
            user_id=context.user_id,
            details={"comment_id": comment_id}
        )
        return True

    async def list_comments(self, query_id: int) -> List[QueryComment]:
        context = get_request_context()
        return await self.comment_repo.list_by_query(query_id, context.workspace_id)

    async def update_comment(self, comment_id: int, body: str) -> Optional[QueryComment]:
        context = get_request_context()
        comment = await self.comment_repo.get_by_id(comment_id, context.workspace_id)
        if not comment:
            return None
        
        # Only author can edit? For simplicity yes
        if comment.user_id != context.user_id:
            raise ValueError("Only the author can edit this comment")
            
        comment.body = body
        comment.updated_at = datetime.utcnow()
        return await self.comment_repo.update(comment)

    async def save_from_history(self, history_id: int, name: str, description: Optional[str] = None) -> SavedQuery:
        """Creates a saved query from a query history record."""
        context = get_request_context()
        from models.query_model import QueryHistory
        from sqlmodel import select
        
        result = await self.query_repo.session.execute(
            select(QueryHistory)
            .where(QueryHistory.id == history_id)
            .where(QueryHistory.workspace_id == context.workspace_id)
        )
        history = result.scalar_one_or_none()
        
        if not history:
            raise ValueError("Query history not found or access denied")
            
        return await self.save_query(
            name=name,
            sql=history.executed_sql or history.generated_sql,
            prompt=history.original_prompt,
            description=description
        )
