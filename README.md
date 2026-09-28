# ai-delivery-bible

Cách triển khai dự án bằng AI agent mà không lạc: **trạng thái dự án sống trong file máy kiểm được**
(contract · runtime check · ratchet · spike evidence), agent đề xuất và chứng minh, người chất vấn và
phủ quyết. Rút từ 3 tháng chạy thật trên một data platform (07→09/2026) và nghiên cứu loop engineering.

> Repo **PUBLIC** (ratchet #1): `case-studies/` đã quét trước khi đẩy — không IP/email/hostname/token/tên người;
> còn tên db/bảng, số MR, id session của một dự án thật, chủ repo chấp nhận. Thêm case study mới → quét lại như vậy.

## Đọc gì trước

| Bạn cần | Đọc |
|---|---|
| Nguyên lý, vòng lặp 8 bước, gate, autonomy — **bible chính** | `docs/loop-framework-flow.md` (v2, 2026-09-28) |
| Phương pháp đã chạy thật, có trích dẫn và ngày | `case-studies/annamgt-2026.md` |
| Vì sao loop cần evaluator riêng và memory trên đĩa | `research/loop-engineering-overview.md` |
| Copy vào dự án mới | `templates/` |
| Quyết định về chính bible này | `ratchet.yml` |

## Áp vào dự án mới — một buổi

1. Copy `templates/CLAUDE.md` vào root workspace, `templates/AGENTS.md` vào từng repo. Điền, giữ ≤ 15 dòng.
2. Mỗi repo: `mkdir contracts ci`, copy `templates/contracts/*.yml` + `templates/ci/check_contracts.py`,
   `check_runtime.py` và hai file test. Đổi rule ví dụ thành bất biến thật đầu tiên của repo
   (thường là: pin version, không secret plaintext, requests bắt buộc).
3. Wire gate vào CI **ngày đầu** (`templates/ci/gitlab-contracts-gate.yml` hoặc `github-contracts-gate.yml`)
   và kiểm tra pipeline có **chạy thật** (runner sống). Gate không có bằng chứng chạy không phải gate.
4. Giả định kỹ thuật rủi ro nhất → spike theo `templates/docs/spikes/TEMPLATE.md` **trước** khi viết contract.
5. Dự án có FE/BE hoặc agent client → `templates/openapi/README.md`.

## Vòng lặp hằng ngày

hỏi ngược → chốt một dòng → spike → contract → MR (một biến mỗi lần) → gate → **verify state sau merge**
→ ratchet → catch ngoài rule → rule mới → report state → dọn. Chi tiết: bible §2, §4.1.

## Luật cho agent (copy nguyên vào CLAUDE.md nếu thiếu)

- Fact mới → contracts/ratchet, không viết md guide mới. Hiện trạng lấy từ contracts, không từ md.
- Lệnh đổi trạng thái hệ thống → show trước, chờ go. Read-only không cần.
- Sau merge / PUT / patch → GET lại, assert nội dung.
- Spike và demo phải throwaway, có timebox, có cleanup ghi lại.
- Mỗi catch ngoài rule = một ratchet entry + một rule hoặc runtime check. Mục tiêu: catch-rate → 0.
- Không attribution AI trong commit/MR.

## Cấu trúc

```
docs/loop-framework-flow.md     bible chính (loop 8 bước · contract layer §4.1 · OpenAPI/MCP §4.2 · autonomy §5 · field notes §11)
case-studies/annamgt-2026.md    phương pháp đã chạy thật: 10 mục, trích dẫn có ngày, điểm yếu đã lộ
research/                       loop engineering: overview · notes · ComPilot summary
templates/
  CLAUDE.md · AGENTS.md         bản đồ workspace · luật repo
  contracts/{rules,runtime,ratchet}.yml
  ci/check_contracts.py · check_runtime.py · test_*.py
  ci/gitlab-contracts-gate.yml · github-contracts-gate.yml
  docs/spikes/TEMPLATE.md
  openapi/README.md             gate + rule cho FE↔BE (OpenAPI) và agent↔BE (MCP)
ratchet.yml                     quyết định về chính bible
```

## Lineage

02/07/2026 `loop-framework-flow` v1 (loop Slack-native, research) → 24/08 contractization trên annamgt →
28/09 v2 + đóng gói. Đổi bible = sửa file + một entry trong `ratchet.yml`; bằng chứng mới từ dự án đang
áp dụng → thêm vào `case-studies/`.
