export const MOCK_SQL = `SELECT 
  t1.id, 
  t1.user_id, 
  t1.amount, 
  t1.currency, 
  t2.name as user_name 
FROM transactions t1
JOIN users t2 ON t1.user_id = t2.id
WHERE t1.amount > 1000 
  AND t1.status = 'completed'
ORDER BY t1.created_at DESC
LIMIT 50;`;

export const MOCK_RESULTS = [
  { id: 1024, user_id: 55, amount: 1250.00, currency: 'USD', user_name: 'Alice Smith' },
  { id: 1025, user_id: 82, amount: 5400.00, currency: 'EUR', user_name: 'Bob Johnson' },
  { id: 1026, user_id: 12, amount: 320.50, currency: 'USD', user_name: 'Charlie Brown' },
  { id: 1027, user_id: 44, amount: 980.00, currency: 'GBP', user_name: 'Diana Prince' },
  { id: 1028, user_id: 91, amount: 15000.00, currency: 'USD', user_name: '[ masked · PII ]' },
];

export const MOCK_EXPLAINABILITY = {
  risk_score: 42,
  risk_level: 'MEDIUM',
  flags: ['high_value_transaction', 'masked_pii_access'],
  sql_rationale: 'Fetching recent high-value transactions with user names. Some columns were masked per PII policy.',
  policy_outcome: {
    decision: 'allow',
    rules_applied: ['pii_masking_rule', 'row_limit_rule']
  }
};
