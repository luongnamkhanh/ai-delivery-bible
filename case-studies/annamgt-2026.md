# Cách dùng AI để delivery dự án annamgt — trích xuất phương pháp

> Nguồn: 9 session Claude Code của workspace annamgt (28/06 → 28/09/2026, chỉ lấy lời của bạn, bỏ recap tự sinh),
> `contracts/{rules,runtime,ratchet}.yml` của 4 repo, `CLAUDE.md`/`AGENTS.md`, `docs/spikes`, `docs/plans`, git log.
> Mọi trích dẫn có ngày. Đây là bản chụp cách làm đã xảy ra, viết để mang sang stack/dự án khác — không phải guide.

## 0. Một màn hình

Dự án chạy bằng AI agent qua hàng chục session và nhiều lần compaction; thứ giữ cho agent (và người) không lạc là
**trạng thái dự án sống trong file máy-kiểm-được, không phải trong văn xuôi hay context window**:

| Câu hỏi | Trả lời bằng | Ở đâu |
|---|---|---|
| Cái gì là bất biến? | **contract** — rule có id, evaluator chạy trên mọi MR | `contracts/rules.yml` + `ci/check_*.py` |
| Hệ đang sống có đúng không? | **runtime check** — cmd + expect, chạy tay/agent/cron | `contracts/runtime.yml` + `ci/check_runtime.py` |
| Vì sao quyết định thế, bằng chứng đâu? | **ratchet** — sổ chỉ-thêm, có ngày, OPEN/CLOSED | `contracts/ratchet.yml` |
| Giả định này có thật không? | **spike** — throwaway, timebox, một câu hỏi, evidence | `docs/spikes/YYYY-MM-DD-*.md` |
| Người mới / agent mới tin cái gì? | **bản đồ** — nguồn sự thật + lệch đã biết + luật làm tiếp | `CLAUDE.md`, `AGENTS.md` |
| Kế hoạch đã chạy chưa? | **plan có banner** `ĐÃ THỰC THI — hồ sơ lịch sử, không phải trạng thái` | `docs/plans/` |

Vòng lặp: **hỏi ngược → chốt một dòng → spike → contract → implement qua MR → gate → verify state → ratchet →
(catch ngoài rule → rule mới) → report state → dọn.**
Vai: **AI đề xuất + chứng minh, người chất vấn + phủ quyết.** Phân công tên gọi: bạn đưa nguyên lý và quyết định,
AI đặt tên và vận hành bộ máy (ratchet, evidence, waiver, contract-first đều do AI đặt; bạn chấp nhận bằng cách
tiếp tục dùng, và hỏi lại khi cần: *"ý tưởng là của t mà thực ra t cũng k hiểu hết, ratchet là sao?"* — 22/09).

## 1. Nguyên lý gốc (vì sao làm thế)

**Docs md là snapshot; agent đọc snapshot cũ thì ảo giác.** Bạn nêu khi warm path đã có 12 doc + plan 10 task mà
chưa chạy dòng nào (24/08 04:40):

> "thứ t muốn thử là contractlization toàn bộ, no md docs, only yml file with fully definition -> no guide, only
> test/rule -> because md guideline file force it in a strict path where test make it flexible, the more test the
> more it pass the expectation of biz, but more guide make it halucinate and cant keep up with the right track
> (lot of docs file make it overwhelm and forget the core stuffs)?"

Và khi dọn docs (03/09 11:21): *"vì mình sẽ làm theo contract và spike nên cần dọn đống docs để tránh halucination
sau này mỗi khi claude phải đọc lại context"* → `CLAUDE.md` workspace: *"Phương pháp: contract + spike. Fact mới →
contracts/ratchet; không viết md guide mới."*

Bối cảnh trực tiếp trước đó (07–08/2026): docs ghi Flink 1.18 trong khi cluster đã 2.0; ArgoCD prune xoá PVC; job
drift stateless vs savepoint; CLAUDE.md ghi 4 scope trong khi code có 5; GitOps chết phải làm tay. Mỗi lần "hiện
trạng ≠ docs/Git" là một lần mất tin cậy trước khách kỹ thuật.

**Test thuần sẽ bị agent "game"; cần invariant + reviewer hoài nghi.** Khi AI cảnh báo specification gaming (agent
đổi tên cột `identity_no` → `id_number` để qua test), bạn không lùi mà đẩy sang dạng rule:
> "thì cái này dùng rule còn gì mà rule hoàn toàn có thể define được trong yml file mà?" (24/08 04:48)
→ `pii.yml forbid_raw` + rule R5 soi *token* trong expr; RT3 soi *giá trị* mẫu trong Doris ("chống gaming đổi tên
cột: soi GIÁ TRỊ, không soi tên").

**Spike rẻ hơn tranh luận.** Spike Debezium wire-format tốn ~15 phút, spike built-in CDC một buổi. Mọi quyết định
kiến trúc mua bằng thí nghiệm thật thay vì meeting; feature mới chưa ai viết bài thì càng phải spike.

**Không tin lời khai, chỉ tin kiểm chứng — áp cả vào chính quy trình.** Bạn đòi citation cho từng fact (*"data
source của warmpath là lấy từ postgres nào thế, citiation ở đâu?"* — 03/09), đòi số đo (*"cần có con số cụ thể mới
thuyết phục được client"* — 27/08). AI áp ngược vào mình: MR !21 "merged" giả (26/08), MR !11 patch hụt (31/08) →
luật *"Sau mỗi merge PUT / patch text: verify state (GET lại, assert nội dung)"*.

**Đừng giới hạn model, giới hạn blast radius.** Trong repo/sandbox agent tự trị (*"t trao quyền m làm hết đó"* —
26/08; *"tự tạo MR tự merge luôn đi"* — 23/07). Chặn ở thao tác không undo được: lệnh đổi trạng thái hệ thống phải
hiện trước (*"show chạy thì gimme câu lệnh trc nhé"* — 19/08 → thành mục trong `~/.claude/CLAUDE.md` và banner mọi
plan), phần chạm VM/console bạn tự chạy (*"ok xong rồi, t tự chạy câu đấy bên ngoài r á"*).

**Kiến trúc trước, span out sau.** *"luôn bắt đầu từ architecture design để span out -> flow, feature..."*
(21/07); *"ê cái core viết theo architecture nào vậy? ... luôn đi từ system architecture rồi span out"* (21/07).

## 2. Bốn tầng artifact và cách chúng khớp nhau

```
   spike ─────────► docs/spikes/*.md   "EVIDENCE, không phải guide": câu hỏi · setup · bảng giả định→kết quả→bằng chứng ·
                                        quyết định rút ra · payload nguyên văn · timebox · đã cleanup
                        │ chốt contract bằng bằng chứng
   rules.yml ──► ci/check_*.py ──► CI job contracts:gate (mọi MR, template chung include theo tag)   = BUILD-TIME
   runtime.yml ► ci/check_runtime.py  (cmd + expect_re/expect_not_re/expect_max; thiếu cmd → SKIP có tên) = RUNTIME
   ratchet.yml ► entry {id, date, caught_by, finding, rule_added | hold+why, evidence, sizing, cleanup, status}
                 "mỗi catch ngoài rule phải sinh entry + rule. Catch-rate phải giảm về 0"
   CLAUDE.md ──► bản đồ: nguồn sự thật · lệch đã biết trong docs trước ngày X · phân lớp docs · luật làm tiếp
```

Hiện trạng 28/09/2026:

| Repo | rules | runtime | ratchet | evaluator |
|---|---|---|---|---|
| annamgt-streaming-pipelines | R1–R10 + `pii.yml` + `tables/*.yml` (10 bảng) | — | 5 entry | `check_contracts.py` + test |
| annamgt-streaming-deployments | I1–I9 | RT1–RT8 (RT2, RT4 chạy được) | 6 | `check_infra.py`, `check_runtime.py` + test |
| annamgt-data-deployments | D1–D6 + `version_floor` | RT-D1–D4 | 8 | `check_doris.py` |
| annamgt-streaming-core | không rules.yml — cổng gác là test (mvn, schema/golden, crypto vectors) | — | 6 | golden/schema tests |

Đặc điểm đáng chép:

- **Rule = bất biến + lý do + lineage.** I9: *"Debezium key offset theo prefix, 2 connector chung prefix đè offset
  nhau, hỏng resume (ratchet #3 · pipelines streaming-findings-full-run #1, verified 11/09)"*.
- **Contract-first:** rule I6/I7 cho KafkaConnector viết **trước khi chart tồn tại** → rule là DoD của ticket T2.
  Bạn ép tách tầng ngay ngày đầu: *"mới contract về pipeline thôi hả? còn debezium, kafka connect... the infra?"* (24/08 07:41).
- **Waiver-as-code:** ngoại lệ ghi trong `rules.yml` kèm lý do + điều kiện gỡ (`r7_append_waivers`).
- **Ratchet chỉ thêm, không sửa ngược;** OPEN phải có điều kiện mở lại (*"Mở lại sau khi 4.1.3 chạy ổn ≥1 tuần"*);
  entry CLOSED ghi cả cách thất bại (*"MR !11 là patch hụt ... Bài học verify-content-sau-merge"*).
- **Cleanup là trường bắt buộc** của spike/demo: *"cleanup: DROP JOB ... + delete pod pg-demo; verify slot trên pod đã drop"*.
- **Evidence có lằn ranh:** ảnh thật giữ nguyên hoặc prototype dán nhãn "BẢN MẪU"; *"Toàn bộ số liệu đo trực tiếp
  trên cluster ngày 26/08 — không phải ước lượng"*.
- **Generator over artifact:** diagram = `build-*.mjs`, HTML = `build-proposal.py`, docx = pandoc từ md, table
  contract sinh từ DDL thật. *"flow thì dùng cái skill vẽ diagram mà mình vừa tạo ấy"* (17/07); không sửa tay SVG.
- **Docs phân lớp** (`analytics-agent/CLAUDE.md`): DELIVERABLE / CANONICAL (sửa tại chỗ) / EVIDENCE (bất biến, có
  ngày) / ARCHIVE (không đọc lấy hiện trạng). Bàn giao = *"chỉ report state cuối cùng thôi"* (17/09), không nhật ký dev.
- **Taste đóng gói thành skill nhà** (`annam-docs`, `annam-diagram`, `annam-design`) thay vì nhắc lại mỗi lần;
  preference cá nhân đưa vào config: *"có lưu format câu trả lời vào -> xong thì sửa config đi"* (17/08).

## 3. Vòng lặp delivery (đã chạy thật)

Ngày 24/08 là mẫu đầy đủ; các việc sau lặp cùng khuôn.

1. **Hỏi ngược để AI tự biện luận** — không mô tả yêu cầu dài. *"nên là etl hay elt? tự challenge bản thân đi"*
   (20/08); *"đây là best pattern mà ngoài kia người ta vẫn dùng hả?"* (21/08); *"bro thử search kiến trúc triển
   khai mới theo contracts và spike xem"* (24/08 02:55) — kèm định vị: *"nó là cách build sản phẩm bằng AI agent
   loop flow, not related to any domain in specific"*.
2. **Chốt bằng một dòng mệnh lệnh** — *"ok thế chốt lại là mình sẽ làm ntn? kiến trúc + plan"* → *"ok giờ bắt đầu
   vào build contract, test, rule, spike đi"* (04:53). "ok/ngon/dứt luôn" + động từ = duyệt; "ủa/sao/là sao" = chưa.
3. **Spike trước** — local docker, throwaway trong scratchpad, **đúng config trong plan**, ~15 phút, trả lời đúng
   các giả định đã liệt kê; ghi `docs/spikes/2026-08-24-debezium-wire-format.md`; `compose down -v`.
   Trả lãi ngay: 4 giả định đúng, 1 sai (DELETE với REPLICA IDENTITY DEFAULT bị MoW nuốt) → runbook + rule R7 + ratchet #1.
4. **Contract theo bằng chứng** — `tables/*.yml` đối chứng payload thật, `rules.yml`, `pii.yml`, evaluator; chạy
   baseline lên chart hiện hữu → bắt nợ thật ngay lần đầu (I1: kafka-ui `:latest`).
5. **Implement qua MR, một biến mỗi lần** — tên MR nói rõ lineage (`feat(doris): upgrade bước 1/3 — MS 3.0.3 →
   4.1.3 (thứ tự contract D2)`); merge "inert" khi nguồn chưa sẵn (`provideTmsCdc=false`); cloud trước, local chỉ
   khi thiếu resource (*"cái nào k có resource để build trên cloud thì mới dựng dưới local thôi"* — 10/09).
6. **Gate** — evaluator local → CI `contracts:gate`; golden byte-diff cho chart; test âm cho rule mới.
7. **Verify state sau merge** — GET lại MR/CR/pod; đo live (kubectl, Prometheus); bạn kiểm bằng mắt trên hệ thật:
   *"ê login show 200 nhưng mà doris FE lại báo incorrect username or password"* (28/07).
8. **Runtime check sau roll** — ghi cặp số trước/sau vào ratchet làm bằng chứng nghiệm thu (RT-D2 parity).
9. **Ratchet** — record + evidence + findings + sizing + cleanup.
10. **Catch ngoài rule → rule mới** — chuỗi 25/09: bạn hỏi *"cái data contract đang được áp dụng ntn trong flow
    của mình?"* → AI tự khai hai chỗ lệch → I9, R10, runner runtime → bạn ra thứ tự *"fix cái này trước r tới cái
    đó sau, còn streaming core thì sao? t k thấy contract nào trong đó?"*.
11. **Report state** — *"report state đi"*, *"ok report status rn"*, *"gimme the report for the current status -
    send to client - always in full context - PEEL flow"* (03/09). Format PEEL là luật từ 17/08.
12. **Dọn** — *"just keep in mind to clean after"* (19/07); *"ủa tắt local infra chưa?"* (12/09); *"dọn rác đi"* (17/09).

## 4. Luật bạn áp lên agent

| Luật | Bằng chứng |
|---|---|
| Fact mới → contracts/ratchet; KHÔNG đẻ md guide mới; hiện trạng lấy từ contracts, không từ md | `CLAUDE.md` 03/09 |
| Đọc bản đồ trước khi tin docs; nghi con số → đo trực tiếp | `analytics-agent/CLAUDE.md` |
| Lệnh đổi trạng thái (kubectl apply, DDL, SQL trên VM, terraform) → SHOW trước, chờ go; read-only không cần | 19/08 "show chạy thì gimme câu lệnh trc nhé"; `~/.claude/CLAUDE.md` |
| Sau merge PUT / patch text → verify state | `analytics-agent/CLAUDE.md`; ratchet data #4 |
| Phân tích trước, fix sau | 16/07 "ý là đừng suggest cách fix -> phân tích và giải thích vụ network này cho t trước đã"; 14/07 "dont code, just plan only (analyze and debate if needed, appreciate critical thinking)" |
| Spike/demo throwaway, có cleanup; evidence có ngày, không "cập nhật" | header spike; trường `cleanup:` |
| Đổi một biến mỗi lần | ratchet data #1 (DB upgrade ≠ operator upgrade) |
| Sizing trước khi bật data thật | 26/08 "data thật mà k sizing ổn là bật lên nó chết ngắc mất"; RT6 capacity gate |
| Quyết định giữ-nguyên có chủ đích → ratchet, không chỉ comment | `streaming-core/AGENTS.md` |
| Pure logic tách khỏi framework, unit-test được; stdlib-first; reuse helper có sẵn | `streaming-core/AGENTS.md` |
| Không sửa tay artifact sinh (SVG/JSON/HTML) — sửa generator | `analytics-agent/AGENTS.md` |
| Không đọc/ghi `keys/` ngoài kubeconfig; secret qua Vault/ESO, không plaintext trong Git | `AGENTS.md`; rule I7 |
| Làm đúng ngay từ đầu, ngoại lệ pilot phải gọi tên | 30/06 "bỏ ngay suy nghĩ pilot thì làm gì cũng được đi -> làm đúng ngay từ đầu pls"; 01/07 "sizing HA đang to quá -> riêng cái này thì pilot thôi" |
| Keep it simple; một manifest = một job | 02/07 "keep it simple thôi, nhiều sink thì nhiều yml file -> dễ quản lý"; 21/07 "t vẫn thích là 1 sink 1 pipeline hơn -> k thich fanout" |
| Tự làm trong phạm vi quyền, không phiền devops; cần đụng infra thì hỏi, không đụng iac | 05/07 "cái gì mình có quyền and có thể tự làm được thì làm -> đừng phiền tới devops"; 07/07 "dont touch the iac repo" (sau vụ 3 LB tốn thêm 1.2 triệu) |
| Test với luồng thật, không test giả | 07/07 "có, test thì cũng phải test với luồng thật chứ" |
| Phạm vi repo: *"đừng động lại iac"*; ownership: *"mình đâu owner repo này"* | 12/07, 20/08 |
| Bối cảnh sạch: *"kp dự án VIB -> remove VIB ra khỏi toàn bộ context"* | 20/07 |
| Không attribution AI trong commit/MR; author là email của bạn | `~/.claude/CLAUDE.md`; 23/07 |
| Đã cấp quyền thì không dừng chờ | 28/09 "k tự merge được à, t cho m quyền r mà?" |
| Bị chặn ngoài tầm → làm phần làm được, ghi phần còn lại OPEN | 28/09 "cái nào mình làm được thì làm k được thì thôi"; ratchet infra #6 |
| Trả lời giải thích theo PEEL; báo cáo gọn | 17/08; 21/07 "gọn nữa -> báo cáo qua tin nhắn mà" |
| Minh bạch việc chạy ngầm | 15/07 "what are u running?"; 23/07 "có cái gì đang chạy ngầm trong session này hả?" |

## 5. Vai người vs AI — cách bạn review

- **Câu hỏi "ủa/sao" một dòng nhắm vào mâu thuẫn logic** là cơ chế review chính, không đọc code:
  *"sao chỉ có 1 job flink vậy? t thấy cdc warmpath có 8 kafka topic mà?"* (10/09); *"tại sao FDB cần 5 pods?"*
  (16/07); *"at least once là đúng cho kafka mà, với doris có cơ chế dedup rồi mà?"* (23/07).
- **Dán lại output của AI rồi bác đúng chỗ.** Câu đắt nhất dự án (16/09 10:07): dán 3 "quyết định policy" của AI
  và kết *"-> vô lý -> nếu dim đi theo đường cdc doris builtin nghĩa là nó k có data cần encrypt thì sao luồng
  hotpath lại encrypt nó?"* → `vehicle` chuyển đường 1, policy "đường 2 = chỉ danh mục sạch tuyệt đối".
- **Tự tóm tắt để kiểm tra hiểu:** *"hot path là fleet, warm path type 1 là fleet_ods, type 2 là fleet dim?"* (11/09).
- **Kiểm bằng mắt trên sản phẩm thật, dán ảnh/bảng:** *"why i still see so many thing in that repo? thought it will
  have the core flink only?"* (25/09); *"[Image] -> thế như này thì 2 job cùng màu hả??? monitor sao?"* (20/07).
- **Ngắt khi lạc scope:** *"ê thế khỏi đi -> tập trung vào phần report trước đã"* (03/09) kèm reject tool.
- **Uỷ quyền có điều kiện:** *"be smart and critical -> make ur own choice base on our plan"* (18/07); *"go for
  it, loop until done"* (19/07); *"làm luôn đi, we have enough time"* (10/09).
- **Không chấp nhận stand-in khi sẽ bàn giao:** *"cdc k đổi tên được thì tính sao? ... sửa luôn đi, sửa cho sạch
  còn bàn giao chứ"* (17/09); *"refactor hết, chưa có gì là prod nên cứ tẹt ga, làm đúng chuẩn chỉ từ đầu"* (16/09).
- **Định kỳ bắt AI tự soi:** *"research xíu xem cái này có sota k? có up to date k?"* (18/09); *"có gì hay ... cách
  triển khai 1 dự án bằng AI agent các kiểu mà m thấy hay?"* (18/09) — AI trả 7 pattern, trong đó câu chốt:
  *"CLAUDE.md làm bản đồ, contracts làm luật, ratchet làm sử ký — phần còn lại chỉ là tay chân."*

## 6. Sự cố → ratchet → automation

| Sự cố | Root cause | Đóng gói thành |
|---|---|---|
| FE Doris restart chuỗi 07–08/2026 | kubelet evict: image ship `-Xmx8192m` trên node 8Gi; FE khai 0 requests | D4, D6 heap ≤ 70% request, RT-D4, ratchet data #4 |
| DELETE không tới Doris | REPLICA IDENTITY DEFAULT chỉ mang PK → MoW sequence nuốt | spike 24/08 → R7 + runbook + RT1 + ratchet #1 |
| 2 connector đè offset (11/09) | chung `topic.prefix` | I9 + test âm + ratchet infra #3 |
| Doris từ chối DDL khi chạy thật (10/09) | partition/distribution ngoài KEY; golden gate chỉ check render | R10 + waiver R7 + ratchet `ddl-findings-4.1`; core ratchet #4 OPEN |
| runtime.yml không ai chạy | check không có cmd+expect | `check_runtime.py`, ratchet infra #4 |
| MR "merged" giả (26/08), patch hụt (31/08) | lệnh chain nuốt lỗi; assert bắt nhầm comment | luật verify state sau PUT |
| Kafka broker crash-loop (31/07) | đĩa đầy sau load test; ArgoCD prune xoá PVC | `retention.bytes`, I2, I3 stateful-prune-off |
| WalPositionLocator freeze (11/09) | connector RUNNING mà stream chết | runbook §9.5 → heartbeat topic → alert → panel bắt buộc |
| CI chết từ 17/08 không ai biết (28/09) | GitLab bỏ floating IP; 3 repo không có runner | ratchet infra #5, #6 (phần cần Owner để OPEN) |

Bài học: evaluator có mà không job nào chạy (wire `contracts:gate` 17/09; runner chết từ 17/08) = gate không có
răng. Gate phải **có bằng chứng đã chạy trên mỗi MR**; runtime check phải **chạy được bằng một lệnh**.

## 7. Diễn tiến phương pháp theo thời gian

| Giai đoạn | Cách điều khiển AI | Artifact chủ đạo |
|---|---|---|
| 28/06 → 07/07 | mở bằng catch-up *"read the docs ... then tell me where are we rn"*; *"List it all out, and I will decide which one is gonna be deploy by their devops, which one will contribute by me"*; học khái niệm bằng "đúng k?/là sao?" + *"online research for best pattern"*; ritual **brainstorm → spec → writing-plans → "multiagent -> parallel"** ×6; MR là đơn vị giao hàng duy nhất; sinh luật cá nhân: 3 mode thực thi (*"why u dont ever suggest me this kind of implementation... nhớ baked cái này lại đó"* — 03/07), no AI attribution (03/07), format DE.html cho mọi doc kiến trúc (01/07) | `docs/superpowers/specs|plans`, 4 repo, hot path GPS |
| 27/07 → 28/07 | gần như toàn lệnh; review bằng screenshot + *"k hiểu?"* ba lần tới khi AI thừa nhận idle-alert nằm ngoài runner; Stop hook `/goal` để AI tự chạy tới khi 5 gate pass; *"còn đống crypto này là sao?"* → vá lỗ PII, spec tự đính chính *"§3.2 của doc này đã lỗi"*, `CRYPTO_CONTRACT.md` + test vector cross-language | `AGENTS.md` core, crypto contract |
| 10/07 → 23/07 | *"không làm gì cả -> chỉ phân tích thôi"* → **tickets T01–T25** (Idea/Goal/DoD/Gate, xếp wave) *"để t test looping framework"* → **loopkit** (gate deterministic + HUMAN door) → từ 21/07 **superpowers** brainstorm → spec → writing-plans → subagent-driven (implementer + reviewer per task); golden tests; gói docs nghiệm thu; đúc skill `annam-diagram`/`annam-design` | `docs/tickets`, `docs/superpowers`, `docs/acceptance` |
| 27/07 → 19/08 | chuẩn bị demo, vận hành cluster; build bod-agent; codify luật cá nhân: PEEL, "gimme câu lệnh trc", lưu vào config | `~/.claude/CLAUDE.md`, plans, proposal VI/EN |
| **24/08** | **contractization**: spike → rulepack data (R1–R8) + infra (I1–I7) + runtime spec + 2 sổ ratchet trong một buổi | `contracts/*` |
| 26/08 → 31/08 | *"t trao quyền m làm hết đó"*; resource contract đo live; Doris upgrade theo D1–D6; ratchet dùng đều | ratchet data #1–#4 |
| 03/09 | dọn docs chống hallucination; `CLAUDE.md` bản đồ; đòi citation từng fact | CLAUDE.md, banner snapshot |
| 10/09 → 18/09 | spike built-in CDC → *"client chốt rồi, giờ làm như thật đi, k demo nữa, full luồng"* → refactor 2-layer → wire CI gate → bàn giao; gỡ scaffold: *"dọn mấy cái superpower nữa, mình đâu có đi theo hướng đó nữa đâu"* (17/09) | ratchet #5–#7, R9/R10, ban-giao.docx |
| 22/09 → 28/09 | handover: audit contract, khép ratchet OPEN, dọn core về Flink-only, hồi sinh CI, chuyển giao tri thức | ratchet core #1–#6, infra #3–#6 |

Chuyển dịch cốt lõi: từ **AI đề xuất – người học – người chọn** (06–07) sang **điều khiển bằng quy trình** (skill
scaffold, ticket, loop — 07) rồi sang **điều khiển bằng artifact kiểm được** (08–09). Mức tin cậy tăng dần
(*"loop until done"* → *"t trao quyền m làm hết đó"*), kiểm soát chuyển từ quy trình sang bằng chứng chạy được. Không mất gì: DoD của ticket thành rule (I6/I7 là DoD của T2); HUMAN door của loopkit thành "show lệnh
trước khi chạy"; "verified-live / designed / deferred" của docs nghiệm thu thành status OPEN/CLOSED + evidence
trong ratchet.

## 8. Từ vựng

- **contract / rulepack** — tập rule có id, mỗi rule = một bất biến + lý do + lineage; evaluator biến nó thành exit code.
- **evaluator / gate** — `ci/check_*.py`, chạy local + CI mọi MR; "không guide, chỉ rule: mỗi FAIL in rõ rule id + lý do".
- **golden gate** — render chart so byte với golden; deterministic; mù với lỗi chỉ lòi khi chạy thật.
- **runtime check** — bất biến không kiểm được từ Git, phải hỏi hệ đang sống; có `cmd` + `expect_*`.
- **ratchet** — sổ quyết định chỉ-thêm: `hold/why` (giữ nguyên có chủ đích) hoặc `record/evidence` (đã làm); OPEN có điều kiện mở lại; tên lấy từ "chỉ tiến không lùi" (`version_floor` một chiều).
- **catch ngoài rule** — lỗi mà reviewer/spike/chạy thật bắt được nhưng rulepack không; bắt buộc sinh entry + rule.
- **spike** — thí nghiệm throwaway, timebox, một câu hỏi rủi ro nhất, capture evidence, cleanup.
- **evidence** — file/ảnh/số có ngày, bất biến; đọc như biên bản.
- **waiver-as-code** — ngoại lệ rule ghi trong rules.yml kèm lý do + điều kiện gỡ.
- **contract-first** — rule viết trước khi artifact tồn tại; rule là DoD.
- **verify state** — sau mọi PUT/merge/patch: GET lại, assert nội dung.
- **snapshot có banner** — md nào cũng có ngày + trạng thái (EXECUTED / EVIDENCE / ARCHIVE).
- **bản đồ** — `CLAUDE.md`: nguồn sự thật, lệch đã biết, luật làm tiếp; đọc trước khi tin docs.
- **report state** — bản chụp trạng thái hiện tại + "giờ t cần làm gì", theo PEEL khi gửi client.
- **ticket (T01–T25)** — Idea / Goal / DoD / Gate / Context, xếp wave — đơn vị thi công giai đoạn 07/2026, sau thành ledger.
- **loopkit** — idea → analyst Q&A → ticket (frozen gate) → generate → deterministic gate → skeptical reviewer → HUMAN door.
- **ponytail** — mode "lười có kỷ luật": YAGNI → stdlib → native → có sẵn → một dòng; shortcut ghi `# ponytail:` kèm ceiling.
- **PEEL** — Point → Explain → Example → Link, format bắt buộc cho câu trả lời giải thích.

## 9. Mang sang dự án / stack mới

1. `CLAUDE.md` gốc ≤ 15 dòng: nguồn sự thật, lệch đã biết, phương pháp, luật chạy lệnh. `AGENTS.md` mỗi repo: luật riêng repo.
2. Mỗi repo `contracts/{rules,runtime,ratchet}.yml` + `ci/check_*.py` + test âm; wire vào CI **ngày đầu** và kiểm
   tra pipeline có chạy thật (template chung include theo tag).
3. Giả định kỹ thuật rủi ro → spike trước khi chốt contract; spike doc theo mẫu *câu hỏi / setup / bảng giả định →
   kết quả → bằng chứng / quyết định / payload nguyên văn / cleanup*.
4. Mỗi thay đổi = một MR, tên nói rõ lineage; merge xong verify state; đổi một biến mỗi lần.
5. Sự cố → root cause → ratchet entry → rule hoặc runtime check; đo catch-rate ngoài rule.
6. Docs văn xuôi chỉ cho người ngoài (client, sign-off), sinh từ generator, có ngày + banner; không dùng làm bộ nhớ agent.
7. Permission theo tầng — khớp thiết kế stack mới đang bàn (Orca/Claude Code/Codex): spike agent gần tự trị
   (local, throwaway) · test/gate tự trị · builder tự trị trong workspace/git · prod/deploy/sudo/credential cần người;
   mọi lệnh đổi trạng thái hiện trước.
8. Preference cá nhân (PEEL, show-command, no-attribution, 3 mode thực thi) sống trong config toàn cục, không nhắc lại.
9. Định kỳ hỏi agent *"có gì lệch so với chính nguyên tắc của mình?"* và *"cái này có sota k?"* — nó tự khai.

## 10. Điểm yếu đã lộ

- Evaluator có nhưng CI không chạy ~3 tuần; runner chết từ 17/08 tới 28/09 mới biết → cần check "gate có chạy không" như một runtime check.
- Runtime layer từng chỉ là spec — "check không có cmd+expect thì thực tế không ai chạy".
- Golden gate chỉ check render → 3 bug DDL chỉ lòi khi chạy thật; DDL dry-run trên Doris thật vẫn OPEN.
- "Merged giả", "patch hụt", `kubectl` tay ngoài GitOps (runner) — lỗi của chính quy trình, chỉ lộ vì có verify live.
- Corpus docs phình (12 doc warm path) trước dòng code nào — cú hích sinh contractization, nhưng cũng là chi phí đã trả.
- Hai lần credential được dán thẳng vào chat (06/07, 08/08) dù đã có `keys/` — cần kênh riêng cho secret, và luật "không dán giá trị, chỉ trỏ đường dẫn".
- Ba lần compaction giữa việc; mỗi lần nối lại bằng "Continue from where you left off" — bản đồ `CLAUDE.md` ra đời muộn (03/09) so với nhu cầu.
- Từ vựng phương pháp phần lớn do AI đặt; người chủ phương pháp phải hỏi lại định nghĩa (22/09) — bản này tồn tại để đóng khoảng trống đó.
