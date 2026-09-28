# AGENTS.md — <repo>

<Một câu: repo này là gì và KHÔNG chứa gì (trỏ nơi chứa).>

Rules for agents working in this repo:

- Đọc `contracts/` trước: `rules.yml` = bất biến máy-kiểm-được (`ci/check_*.py`), `ratchet.yml` = sổ quyết định
  có ngày + bằng chứng, `runtime.yml` = check trên hệ đang sống.
- Quyết định giữ-nguyên có chủ đích → `contracts/ratchet.yml`, không chỉ comment code.
- Pure logic tách khỏi framework, unit-test được; stdlib-first; reuse helper có sẵn trước khi viết mới.
- Không đọc/ghi `<keys dir>` ngoài <mục đích>. Secret qua <Vault / ESO / env>, không plaintext trong Git.
- Đổi format contract giữa repo (schema, tag) = bump version; không re-tag tag đã deploy.
- Không đụng `.gitlab-ci.yml` / workflow CI trừ khi ticket nói rõ.
