SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'helpee_costs';
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM
    information_schema.columns
WHERE
    table_schema = 'public'
ORDER BY
    table_name,
    ordinal_position;
