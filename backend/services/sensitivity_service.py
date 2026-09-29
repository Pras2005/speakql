from repositories.sensitivity_repository import SensitivityRepository
from models.sensitivity_model import SensitivityRule, MaskingStrategy
from typing import List, Dict, Any, Optional

class SensitivityService:
    def __init__(self, sensitivity_repo: SensitivityRepository):
        self.sensitivity_repo = sensitivity_repo

    async def get_applicable_rules(self, workspace_id: int, table_names: List[str]) -> Dict[str, List[SensitivityRule]]:
        """
        Returns a mapping of table_name -> list of sensitivity rules.
        """
        rules_map = {}
        for table in table_names:
            rules = await self.sensitivity_repo.get_rules_for_table(workspace_id, table)
            if rules:
                rules_map[table] = rules
        return rules_map

    def resolve_masking_requirement(
        self, 
        rules: List[SensitivityRule], 
        column_name: str, 
        user_role: str
    ) -> Optional[MaskingStrategy]:
        """
        Determines the masking strategy for a specific column and user role.
        """
        # Rules are ordered by priority (descending)
        for rule in rules:
            if rule.column_name == column_name:
                # If restricted_roles is defined, check if user's role is in it
                if not rule.restricted_roles or user_role in rule.restricted_roles:
                    return rule.masking_strategy
        
        # Default behavior: No masking if no rule matches
        return MaskingStrategy.NONE
