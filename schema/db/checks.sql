-- 悬空与口径检查（灌库后、VALIDATE 前跑；每条应返回 0 行）
SELECT 'book.work_id 悬空' chk, b.id FROM book b LEFT JOIN work w ON w.id=b.work_id WHERE w.id IS NULL;
SELECT 'authorship.entity_id 悬空', a.owner_id FROM authorship a LEFT JOIN entity e ON e.id=a.entity_id WHERE a.entity_id IS NOT NULL AND e.id IS NULL;
SELECT 'member_of 悬空', m.member_id FROM member_of m LEFT JOIN collection c ON c.id=m.collection_id WHERE c.id IS NULL;
SELECT 'work_relation 悬空', r.src FROM work_relation r WHERE NOT EXISTS (SELECT 1 FROM work w WHERE w.id=r.dst) AND NOT EXISTS (SELECT 1 FROM collection c WHERE c.id=r.dst);
SELECT 'index_entry.source_bid 悬空', i.owner_id FROM index_entry i LEFT JOIN work w ON w.id=i.source_bid WHERE i.source_bid IS NOT NULL AND w.id IS NULL;
-- owner_type 与 id 实际所在主表一致
SELECT 'authorship.owner_type 不符', a.owner_id FROM authorship a WHERE NOT ((a.owner_type='W' AND EXISTS(SELECT 1 FROM work w WHERE w.id=a.owner_id)) OR (a.owner_type='B' AND EXISTS(SELECT 1 FROM book b WHERE b.id=a.owner_id)) OR (a.owner_type='C' AND EXISTS(SELECT 1 FROM collection c WHERE c.id=a.owner_id)));
-- 正式 id 与草稿 id 不得相同（硬门禁）
SELECT 'id 跨类重复', id FROM (SELECT id FROM work UNION ALL SELECT id FROM book UNION ALL SELECT id FROM collection UNION ALL SELECT id FROM entity) t GROUP BY id HAVING count(*)>1;
-- book-text 悬空（只报，不加外键）
SELECT 'bt_section.work_id 悬空', s.item_id, s.work_id FROM bt_section s WHERE s.work_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM work w WHERE w.id=s.work_id);
SELECT 'bt_entity_span_target 悬空', t.item_id, t.target_id FROM bt_entity_span_target t WHERE NOT EXISTS (SELECT 1 FROM entity e WHERE e.id=t.target_id) AND NOT EXISTS (SELECT 1 FROM work w WHERE w.id=t.target_id);
