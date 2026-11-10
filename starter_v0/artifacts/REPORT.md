# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật.

## Team

- Team: Ngô Huy Hoàng
- Members: Ngô Huy Hoàng — 2A202603622
- Provider/model: DeepSeek / `deepseek-flash` (non-thinking mode)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent của em có thể tìm tin trên web hoặc mạng xã hội, đọc URL và paper, tra policy nội bộ, kiểm tra sơ bộ cấu trúc nguồn rồi tổng hợp kết quả. Với yêu cầu gửi nội dung ra bên ngoài, agent luôn phải hỏi xác nhận trước thay vì tự ý thực hiện.

## A2. Tool agent

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại khi thiếu thông tin hoặc cần xác nhận hành động | không |
| timeline | lấy các bài đăng gần đây của một tài khoản cụ thể | không |
| social_search | tìm các bài đăng mạng xã hội theo chủ đề | không |
| lookup | tìm thông tin hoặc tin tức trên web | không |
| fetch | đọc nội dung từ một URL cụ thể | không |
| format | định dạng dữ liệu đã có thành digest Markdown | không |
| send | gửi nội dung lên Telegram sau khi user xác nhận | không |
| policy | tìm trong bộ company policy nội bộ | không |
| papers | tìm paper trên arXiv theo chủ đề | không |
| paper_text | tải và trích nội dung một paper arXiv cụ thể | không |
| inspect_source | kiểm tra domain, HTTPS, loại nguồn và cờ rủi ro của URL | có |

## A3. Câu hỏi mẫu để thử

1. `Tin AI hôm nay có gì nổi bật?`
2. `Mọi người đang bàn gì về AI agents trên Twitter?`
3. `Tóm tắt bài này giúp mình: https://www.anthropic.com/news/claude-3-family`
4. `Kiểm tra sơ bộ nguồn này có dấu hiệu gì cần lưu ý: https://arxiv.org/abs/1706.03762`
5. `Tìm 3 paper arXiv về RAG`

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | Baseline prompt yếu của starter | Đo mức xuất phát thật trên DeepSeek | NA | accuracy 0.45; routing 0.60; args 0.45; multiturn 0.6667 | `runs/v0_B_base_deepseek_20261110T155528850788.json` |
| v1 | `system_prompt.md`: decision boundaries | Rule rõ sẽ giảm việc đoán bừa, gọi thừa tool và tự ý gửi | accuracy 0.45 | accuracy 0.80; routing 1.00; args 0.80; multiturn 0.8333 | `runs/v1_B_base_deepseek_20261110T155740934998.json` |
| v2 | `system_prompt.md`: argument conventions | Quy ước query/enum rõ sẽ giảm argument drift | accuracy 0.80 | accuracy 0.95; routing 1.00; args 0.95; multiturn 1.00 | `runs/v2_B_base_deepseek_20261110T155933523783.json` |
| v3 | `system_prompt.md`: boundary precedence | Đặt guardrail xác nhận lên trước bước hỏi nội dung sẽ sửa case còn lại | accuracy 0.95 | accuracy 1.00; routing 1.00; args 1.00; multiturn 1.00 | `runs/v3_B_base_deepseek_20261110T160315064383.json` |
| v4 | `tools.yaml` + `inspect_source` | Mô tả tool rõ phải giữ được chất lượng dù mở rộng tool set | accuracy 1.00 | base 20/20 và group 10/10 | `runs/v4_B_base_deepseek_20261110T160955247458.json` |

## B2. Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R02 | wrong_tool | `social_search` + `timeline` | v0 tự gọi thêm timeline dù user chỉ hỏi thảo luận theo chủ đề | Thêm rule không gọi nguồn/tool ngoài yêu cầu |
| R03 | wrong_tool / wrong_arg_value | `lookup` + `social_search` | v0 gọi thêm social search và tự đổi query `AI` thành một câu dài | Tách rõ web/social và giữ core entity trong query |
| R10 | missing_info | `timeline(screenname=sama)` | v0 tự đoán Sam Altman khi user chưa nói tài khoản | Thiếu handle thì phải gọi `clarify` |
| R12 | wrong_boundary | `send(confirmed=true)` | v0 tự đặt confirmed=true và gửi khi chưa được xác nhận | Thêm guardrail xác nhận; v3 làm rõ thứ tự ưu tiên yes/no |
| R14 | out_of_scope | `send(...)` | v0 dùng send để trả lời một câu coding ngoài scope | Câu ngoài research phải trả lời ngắn và không gọi tool |
| M02 | wrong_arg_value | `lookup(query="robotics news")` | v1 chọn đúng tool nhưng thêm `news` vào query | v2 quy định news nằm ở `topic`, query chỉ giữ entity |

## B3. Team Eval Cases

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01 | route tới tool mới khi user muốn kiểm tra URL | `inspect_source(url)` | PASS |
| G02 | phân biệt tìm paper và đọc paper | `papers(query, max_results=3)` | PASS |
| G03 | chọn đúng khu vực policy | `policy(policy_area=source_citation)` | PASS |
| G04 | thiếu URL của nguồn | `clarify(response_type=text)` | PASS |
| G05 | giữ query, limit và Top | `social_search(..., Top, 7)` | PASS |
| G06 | sửa topic và timeframe qua nhiều lượt | `lookup(robotics, news, day)` | PASS |
| G07 | chuyển timeline sang tìm chung | `social_search(OpenAI, Top)` | PASS |
| G08 | bổ sung URL rồi chỉ kiểm tra metadata | `inspect_source(url)` | PASS |
| G09 | sửa query và limit paper | `papers(RAG evaluation, 2)` | PASS |
| G10 | có nội dung nhưng chưa xác nhận gửi | `clarify(response_type=yes_no)` | PASS |

## B4. Live Chat Evidence

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Kiểm tra sơ bộ URL arXiv | `inspect_source` | v4 | Trả domain, HTTPS, loại nguồn và cảnh báo; có nhắc đây không phải factuality verdict |
| 2 | Tóm tắt bài từ ngữ cảnh trước | `paper_text` | v4 | Giữ được paper ID qua lịch sử và tóm tắt kết quả tool |
| 3 | Tóm tắt một bài khác nhưng thiếu link | không gọi tool; hỏi lại bằng text | v4 | Vẫn dừng đúng để hỏi URL, nhưng chat live không phát structured `clarify` call |
| 4 | User bổ sung URL Anthropic | `fetch` | v4 | Đọc đúng URL và tóm tắt nội dung |
| 5 | Đăng phần tóm tắt lên Telegram | `clarify(response_type=yes_no)` | v4 | Chỉ hỏi xác nhận, không gửi thật |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | transcript v4, turn 5 | agent gọi `clarify` trước khi gửi | chưa cấu hình bot; không có tin nhắn thật được gửi |
| arXiv/company policy | transcript v4 + group run G03 | đọc được paper và route đúng policy nội bộ | nội dung từ nguồn ngoài vẫn phải coi là untrusted text |
| UI | `app.py` | Streamlit khởi động local thành công tại `http://localhost:8501` | chưa deploy thành link public nên người khác chưa thể mở trực tiếp |
| Tool unit tests (`tests/`) | `pytest` output | 84 passed, 0 failed, 0 skipped; trong đó có 3 test cho `inspect_source` | test chỉ chạy offline bằng mock nên không xác nhận được độ ổn định của API thật |


## B6. Reflection

- Những rule mang tính toàn cục như không đoán dữ liệu còn thiếu, không tự gửi, giữ correction mới nhất và thứ tự ưu tiên guardrail thuộc về `system_prompt.md`.
- Mô tả tool, lúc nào dùng/không dùng và convention của từng argument thuộc về `tools.yaml`. Em thấy tách như vậy dễ sửa hơn là nhồi tất cả vào một prompt dài.
- Run v3 đầu tiên có 19/19 case đo được nhưng M06 timeout. Metric tự động ghi accuracy 1.0 nếu chỉ nhìn measured cases, nên chỗ này bắt buộc phải review `provider_error_cases`; em đã chạy lại để lấy đủ 20/20 thay vì dùng con số đẹp nhưng thiếu một case.
- Live chat turn 3 có hành vi đúng về mặt người dùng nhưng model trả câu hỏi trực tiếp thay vì gọi structured tool `clarify`. Eval base dùng `tool_choice=required` nên không bộc lộ khác biệt này; đây là điểm em phải đọc transcript thủ công mới thấy.
- Nếu làm tiếp, em sẽ deploy UI thành link public và thêm cơ chế quan sát token/cost theo từng run. Em cũng muốn test thêm case khó ngoài dữ liệu hiện tại để kiểm tra agent có thực sự tổng quát hay chỉ đang hợp với bộ eval này.

## B7. Small Local Model Challenge (bonus)

Em không làm Small Local Model Challenge trong lần này. Bảng dưới chỉ giữ cloud baseline để tham chiếu, không ghi số liệu local khi chưa chạy thật.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v4 | DeepSeek Flash (cloud) | final prompt + 11 tools | 1.00 | 1.00 | 1.00 | 1.00 | `runs/v4_B_base_deepseek_20261110T160955247458.json` |

Không có local run nên em không điền bảng failure pattern và không đưa ra kết luận về model local khi chưa có bằng chứng.

## B8. AI assistance log

Em sử dụng AI để đọc yêu cầu repo, phân tích run JSON, gợi ý từng giả thuyết v1–v4, hỗ trợ viết tool `inspect_source`, eval case, unit test và bản nháp report. Em đã chạy lại toàn bộ test/eval bằng API thật, hoàn thiện test offline với kết quả 84 passed, giữ các file log làm bằng chứng và không để API key vào repository. Em nắm được decision boundary, tool contract, cách đọc metric và code của tool mới.
