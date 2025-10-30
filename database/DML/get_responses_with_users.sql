SELECT u.slack_id, r.entry 
FROM responses r
JOIN users u ON r.user_id = u.id
WHERE r.event_id = %s AND r.entry IS NOT NULL
ORDER BY r.submitted_at ASC
