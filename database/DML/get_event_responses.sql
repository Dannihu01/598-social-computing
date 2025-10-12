SELECT r.entry
FROM events AS e
LEFT JOIN responses AS r ON r.event_id = e.id
WHERE e.id = %s