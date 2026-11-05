-- book-text 悬空检查（只报，不加外键；book-text 各表进库前手写，第 4 步再并进映射）
-- book-text 悬空（只报，不加外键）
SELECT 'bt_section_work.work_id 悬空', s.item_id, s.work_id FROM bt_section_work s WHERE NOT EXISTS (SELECT 1 FROM work w WHERE w.id=s.work_id);
SELECT 'bt_entity_span_target 悬空', t.item_id, t.target_id FROM bt_entity_span_target t WHERE NOT EXISTS (SELECT 1 FROM entity e WHERE e.id=t.target_id) AND NOT EXISTS (SELECT 1 FROM work w WHERE w.id=t.target_id);
