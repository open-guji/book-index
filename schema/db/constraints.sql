-- constraints.sql：灌库（COPY）之后再执行。NOT VALID＝不检查已灌入的存量，只拦之后的写入；
-- 悬空清单由 checks.sql 出，清干净后逐条 ALTER TABLE … VALIDATE CONSTRAINT。

ALTER TABLE book  ADD FOREIGN KEY (work_id)     REFERENCES work(id)       NOT VALID;
ALTER TABLE authorship ADD FOREIGN KEY (entity_id) REFERENCES entity(id)  NOT VALID;
ALTER TABLE member_of ADD FOREIGN KEY (collection_id) REFERENCES collection(id) NOT VALID;
ALTER TABLE work_relation ADD FOREIGN KEY (src) REFERENCES work(id) NOT VALID;
-- work_relation.dst 可指 Collection（collected_in 80、studies 1），不加外键，checks.sql 合查两表
ALTER TABLE entity_relation ADD FOREIGN KEY (dst) REFERENCES entity(id) NOT VALID;
ALTER TABLE person ADD FOREIGN KEY (native_place_entity_id) REFERENCES entity(id) NOT VALID;
ALTER TABLE office ADD FOREIGN KEY (base_office_id) REFERENCES entity(id) NOT VALID;
-- index_entry.source_bid 实测全部指 Work、悬空 0（S3 报告 E10），可直接 VALIDATE
ALTER TABLE index_entry ADD FOREIGN KEY (source_bid) REFERENCES work(id) NOT VALID;

ALTER TABLE place_history_dynasty ADD FOREIGN KEY (dynasty_id) REFERENCES entity(id) NOT VALID;
ALTER TABLE collection ADD FOREIGN KEY (work_id) REFERENCES work(id) NOT VALID;
ALTER TABLE related_collection ADD FOREIGN KEY (dst) REFERENCES collection(id) NOT VALID;
