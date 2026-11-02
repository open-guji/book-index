-- 悬空与口径检查（灌库后、VALIDATE 前跑；每条应返回 0 行）
SELECT 'book.work_id 悬空' chk, b.id FROM book b LEFT JOIN work w ON w.id=b.work_id WHERE w.id IS NULL;
SELECT 'authorship.entity_id 悬空', a.owner_id FROM authorship a LEFT JOIN entity e ON e.id=a.entity_id WHERE a.entity_id IS NOT NULL AND e.id IS NULL;
SELECT 'member_of 悬空', m.member_id FROM member_of m LEFT JOIN collection c ON c.id=m.collection_id WHERE c.id IS NULL;
SELECT 'work_relation 悬空', r.src FROM work_relation r LEFT JOIN work w ON w.id=r.dst WHERE w.id IS NULL;
SELECT 'index_entry.source_bid 悬空', i.owner_id FROM index_entry i LEFT JOIN work w ON w.id=i.source_bid WHERE i.source_bid IS NOT NULL AND w.id IS NULL;
-- owner_type 与 id 实际所在主表一致
SELECT 'authorship.owner_type 不符', a.owner_id FROM authorship a WHERE NOT ((a.owner_type='W' AND EXISTS(SELECT 1 FROM work w WHERE w.id=a.owner_id)) OR (a.owner_type='B' AND EXISTS(SELECT 1 FROM book b WHERE b.id=a.owner_id)) OR (a.owner_type='C' AND EXISTS(SELECT 1 FROM collection c WHERE c.id=a.owner_id)));
-- 正式 id 与草稿 id 不得相同（硬门禁）
SELECT 'id 跨类重复', id FROM (SELECT id FROM work UNION ALL SELECT id FROM book UNION ALL SELECT id FROM collection UNION ALL SELECT id FROM entity) t GROUP BY id HAVING count(*)>1;
