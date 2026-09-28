# App projects — OpenAPI là contract FE↔BE, MCP là adapter cho agent client

Tách FE/BE qua OpenAPI không mới; điểm 2026 là **spec-driven**: spec là gate loop chạy, không phải tài liệu
(spec-first → **spec-anchored** (CI fail khi drift, đích cần đạt) → spec-as-source). Chi tiết: bible §4.2.

```
  FE web / mobile ──HTTP──► OpenAPI  (build-time contract, source of truth duy nhất)
  Agent client    ──MCP───► MCP server: sinh từ CÙNG OpenAPI rồi curate (5–10 intent tool, không 1 tool / endpoint)
                                 ▼
                    operations layer chung, không phụ thuộc protocol — business logic ở đây một lần
```

## Gate deterministic (bước ④, không LLM) — mỗi dòng thành một rule trong `rules.yml`

| Gate | Công cụ gợi ý | FAIL khi |
|---|---|---|
| Spec lint | spectral | sai style / naming / thiếu description |
| Breaking-change diff vs main | oasdiff | có break → mở human door (interface change, bible §8.2) |
| Contract test impl vs spec | schemathesis · specmatic | response lệch schema |
| Mock vs spec (FE dev) | prism · specmatic mock | mock drift khỏi spec |
| Client / mock sinh lại trong CI | openapi-generator · kubb · orval | diff so với commit → FAIL (không sửa tay) |
| MCP tool schema = OpenAPI schema | fastmcp · speakeasy · kubb → validate ở gateway | tool nhận input ngoài schema |

## Rule — mỗi dòng là một rule, không phải khuyến nghị

- Không MCP cho consumer duy nhất không phải agent. FE nói REST; một consumer thì MCP là liability.
- Sinh rồi cắt: 1 endpoint ≠ 1 tool. Nhóm theo workflow; surface lớn → dynamic discovery (search → schema → invoke).
  Đội thật cắt 60–93% tool sinh tự động trước khi agent chạy ổn.
- Description viết lại cho agent: khi nào dùng, kết quả nghĩa gì, edge case. (AutoMCP: 76.5% → 99.9% sau ~19 dòng sửa spec / API.)
- Identity xuyên qua MCP: backend phải thấy end user, không thấy service account của MCP server
  (OAuth pass-through hoặc enforce per-user trong server + audit ở gateway). Role ở tầng data phải sống qua hop này.
- Đổi spec = đổi interface → ratchet entry + door, như migration schema.

## Spike trước khi chốt

- Sinh MCP từ OpenAPI thật → đếm tool → đo agent chọn đúng tool bao nhiêu % trên 20 câu hỏi thật, trước và sau curate.
- Test identity: gọi qua MCP với 2 user khác quyền → backend phải trả kết quả khác nhau.

Nguồn: arXiv 2602.00180 · Specmatic MCP guardrails · WorkOS "MCP vs REST" · Speakeasy / Neon / Xata OpenAPI→MCP ·
arXiv 2603.07473 (caller-identity confusion). MCP spec 2026-07-28 đã stateless — phản bác "MCP stateful" đã cũ.
