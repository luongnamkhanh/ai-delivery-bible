# <workspace> — bản đồ (≤ 15 dòng; agent đọc trước khi tin bất kỳ doc nào)

- Hiện trạng: `contracts/{rules,runtime,ratchet}.yml` trong <repo A>, <repo B> — KHÔNG lấy hiện trạng từ file md.
- Hệ thật: <kubeconfig / endpoint / DB>. Nghi con số nào trong docs → đo trực tiếp, đừng tin docs.
- Lệch đã biết trong docs viết trước <ngày>: <1–3 dòng, hoặc "chưa có">.
- Phương pháp: contract + spike. Fact mới → contracts/ratchet; không viết md guide mới.
- Lệnh đổi trạng thái (kubectl apply, DDL, terraform, deploy) → SHOW trước, chờ go. Read-only không cần.
- Sau mỗi merge / PUT / patch: verify state (GET lại, assert nội dung).
- Deliverable cho người ngoài: <thư mục> — sinh bằng generator, có ngày + banner; không sửa tay artifact.
- Không attribution AI trong commit/MR. Author: <email>.
- Bible: github.com/luongnamkhanh/ai-delivery-bible
