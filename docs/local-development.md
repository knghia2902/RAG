# Vận hành local

Docker Desktop Linux containers and Compose are required. Administration has no OpenAI dependency; no key is needed for Phase 1. Files and database persist locally; future generation sends selected context and embeddings send chunks/queries to the configured external provider.

Từ PowerShell tại thư mục gốc repo, chỉ copy nếu chưa có `.env`:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
docker compose up --build -d frontend
docker compose ps -a
docker compose exec -T backend python -m alembic current
docker compose exec -T backend python -c "import urllib.request; assert urllib.request.urlopen('http://localhost:8000/health/ready').status == 200"
docker compose exec -it backend python -m scripts.bootstrap_admin
```

Trong editor, thay placeholder `POSTGRES_PASSWORD` bằng mật khẩu mạnh URL-safe (ký tự chữ/số hoặc `-._~`), giữ `APP_ORIGIN=http://localhost:3000`. Không in `.env`, không commit, không gửi screenshot secrets. Để `OPENAI_API_KEY=` trống cho Phase 1. Key tùy chọn chỉ nằm server-side; Web hiển thị trạng thái boolean, không hiển thị/chỉnh key. Không cần cài dependency ứng dụng trên host: image dùng lockfiles và digests.

`migrate` phải thoát 0, backend/frontend phải healthy; Alembic hiện `0001_access_control (head)`. Bootstrap tương tác nhập username và hai lần mật khẩu tài khoản 8–128 ký tự; mật khẩu không echo. Chạy lại không thay Admin hiện có. Mở http://localhost:3000/login: Admin vào Tài khoản. Chỉ frontend publish `127.0.0.1:3000`; API/PostgreSQL không publish.

Seed là lệnh riêng, tùy chọn, sau bootstrap:

```powershell
docker compose exec -it backend python -m scripts.seed_demo
```

Nhập mật khẩu riêng cho `demo-granted` và `demo-ungranted`. Seed chỉ thêm metadata Demo WMS chưa có tài liệu và hai Kỹ thuật viên, chỉ cấp quyền ban đầu cho tài khoản vừa tạo. Chạy lại giữ nguyên mật khẩu, role, metadata và quyền đã thu hồi. Kỹ thuật viên phải đổi mật khẩu trước khi vào Dataset; tài khoản chưa được cấp quyền thấy hướng dẫn liên hệ Admin. Admin dùng panel Tài khoản để cấp mật khẩu tạm/vô hiệu hóa; thao tác này thu hồi phiên hiện có. Đăng xuất dùng nút Web, không xóa cookie thủ công để mô phỏng thu hồi.

Startup order: postgres healthy → migrate successfully applies Alembic → backend readiness checks actual head → frontend. Database uses named volume `postgres-data`, uploads `data/uploads`, storage `storage`; source directories are never public static routes. Do not delete volumes to troubleshoot ordinary startup failures.

PostgreSQL healthcheck dùng TCP `127.0.0.1` để chờ server cuối. Server khởi tạo tạm của image chỉ mở Unix socket, nên `pg_isready` không có `-h` có thể báo healthy trước khi tạo database xong. Kiểm thử riêng: `powershell -NoProfile -File tools/tests/postgres-readiness.Tests.ps1` dùng container tmpfs và barrier khởi tạo, không dùng volume vận hành.

Frontend tham gia cả mạng `local` internal để gọi API và mạng `web` bridge để Docker có thể publish loopback. Backend/PostgreSQL chỉ tham gia `local`; test services chỉ tham gia `test` internal. Chỉ gắn frontend vào internal bridge có thể tạo HostConfig binding nhưng không tạo effective port mapping; runner kiểm tra NetworkSettings và host listener để phát hiện trường hợp này. [Docker multiple networks](https://docs.docker.com/engine/network/#connecting-to-multiple-networks) mô tả topology frontend/public và backend/private.

## Khôi phục và backup

Nếu startup/migration lỗi, xem `docker compose ps -a` và `docker compose logs migrate` tại máy local (không chia sẻ output chứa dữ liệu vận hành/secrets). Sửa cấu hình/nguyên nhân trước khi chạy lại `docker compose up --build -d frontend`; không xóa volume, không reset schema và không chạy seed để sửa quyền. Retry Alembic/seed/bootstrap đã có kiểm tra replay, nhưng migration mới vẫn cần backup trước khi upgrade. Restart thường dùng `docker compose restart postgres backend frontend`, rồi kiểm tra health như trên; không dùng `down -v` trên project vận hành.

Backup PostgreSQL dạng binary qua file bên trong container rồi copy ra host (tránh PowerShell 5 redirection làm hỏng binary):

```powershell
docker compose exec -T postgres pg_dump -U rag -d rag -Fc -f /tmp/rag-backup.dump
docker compose cp postgres:/tmp/rag-backup.dump ./rag-backup.dump
```

Lưu backup ở nơi được kiểm soát, ngoài Git, cùng bản sao `data/uploads`, `storage`, cấu hình và image/lock revisions. Dump chứa dữ liệu tài khoản/hash: không chia sẻ, không dùng làm fixture. Thử restore vào database riêng trước khi khôi phục vận hành; dừng ghi trong lúc chụp bản sao file liên quan. Không đổi Docker storage hoặc prune để khắc phục lỗi ứng dụng.

## Nghiệm thu disposable stack

```powershell
powershell -NoProfile -File tools/verify-local.ps1 -TestProject rag-phase1-acceptance
```

Runner thêm ID ngẫu nhiên vào tên project cho mỗi lần chạy, kiểm tra mọi tên volume/network chính xác bất kể nhãn, và từ chối cả tên cũ dạng `<TestProject>_<resource>` đã tồn tại. Nó tạo trước tài nguyên riêng rồi xác minh nhãn `com.logistics-rag.acceptance-run` trước khi gắn vào container. Cleanup chỉ xóa các container/volume/network được xác minh thuộc lần chạy này; không dùng `down --volumes` hoặc xóa orphan. Nếu bị ngắt, kiểm tra cả nhãn run và project trước khi tự quyết định xử lý tài nguyên còn lại. Runner dùng config tạm không đọc `.env` vận hành, credentials ngẫu nhiên, named volumes riêng thay mọi operational bind mount, port thử `127.0.0.1:33071`, database test `postgres-test/rag_test`. Môi trường và file credentials tạm được khôi phục/xóa kể cả khi Docker cleanup thất bại; lỗi acceptance và teardown đều được báo và làm exit nonzero. Nó kiểm tra database rỗng, real Alembic head/vector/constraints/replay, migration cố ý lỗi chặn backend/frontend, bootstrap/seed độc lập/concurrency/SIGKILL/retry, snapshot restart chính xác, pip check, actual Docker bindings và host IPv4/IPv6 listeners. Mỗi bước có PASS; lỗi hoặc 0 tests làm exit nonzero. Không in giá trị snapshot/password/hash/key.

Kiểm thử an toàn runner: `powershell -NoProfile -File tools/tests/verify-local.Tests.ps1` dùng Docker giả lập; `powershell -NoProfile -File tools/tests/verify-local-sentinel.Tests.ps1` tạo volume sentinel không nhãn với tên ngẫu nhiên riêng, xác nhận runner từ chối và giữ nguyên nội dung, rồi chỉ xóa volume do kiểm thử này tạo.

Binding trong Compose không tự chứng minh LAN isolation. Runner kiểm tra effective host listener và yêu cầu Engine >=28 vì Docker cũ có hạn chế L2 localhost publishing. Windows Firewall, WSL/network forwarding, VPN và routing tùy máy vẫn cần người vận hành xác nhận: giữ firewall bật, không thêm LAN allow rule/port forwarding, và từ máy LAN khác thử truy cập IP LAN của host ở port 3000 phải thất bại. Runner không tự sửa firewall và không thể chứng minh thử nghiệm từ máy thứ hai. [Docker port publishing](https://docs.docker.com/engine/network/port-publishing/) giải thích version/direct-routing limits; [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/) giải thích dependency health/completion gate.

## Automated isolated checks

From the repository root, unattended commands:

```
docker compose run --rm frontend-test npm run test:e2e -- phase1.spec.ts --grep tracer
docker compose run --rm frontend-test npm run test:e2e -- phase1.spec.ts --grep ui-smoke
docker compose run --rm backend-test python -m pytest -q
docker compose run --rm frontend npm run typecheck
docker compose run --rm frontend npm run build
docker compose run --rm frontend npm run lint
```

First build test images with `docker compose build backend-test next-test frontend-test`. No profiles are required. Health dependencies start postgres-test/rag_test → migrate-test → api-test → next-test → frontend-test. Backend tests and browser setup use the same migrated rag_test database and separate `postgres-test-data` volume, with no host ports and no operational network access. Next test target is selected during image build (`API_TARGET=http://api-test:8000`), not a runtime public variable. Test settings reject operational database hosts, fixtures reset only rag_test, and the production API has no test fixture routes. Test services cannot access operational PostgreSQL and have no outbound AI network path. Run suites sequentially because fixtures share rag_test.

`ui-smoke` dùng một worker, real login/role landing/labelled controls/logout, không fixed sleep; target warm test <=30s, tách khỏi build/container startup. Full browser suite vẫn là final gate. Phần runner disposable sẽ rebuild image trước kiểm tra để không dùng test code cũ. Production build/typecheck/lint chạy riêng như trên; không suy ra chúng pass chỉ từ E2E.

Tests never clear operational/demo data. Browser proof asserts its session digest and dataset through api-test; backend-test can query the same database. Operational database checks must show no `Browser WMS` row. Python requirements are fully hash locked for Python 3.12, npm uses package-lock, and base images include exact digests. `pip check`, typecheck, lint and production build validate compatibility rather than assuming registry metadata proves it.

Authentication uses Argon2, opaque SHA-256-digested sessions, HttpOnly host-only Strict cookies. HTTP loopback alone permits Secure=false. Login requires exact Origin/Host, JSON and custom header; authenticated mutations additionally require synchronizer CSRF. No tokens in localStorage. Username is normalized immutable ASCII; account passwords contain 8–128 Unicode characters without trimming. The PostgreSQL `POSTGRES_PASSWORD` remains a separate database-secret requirement in `.env`.

Sessions reject at 30 minutes idle or 8 hours absolute, including equality. GET polling is passive. Visible navigation, key and pointer actions send a CSRF-protected activity request at most once per minute; no heartbeat timer renews idle. Logout and activity serialize through row locks; conditional activity also rejects a snapshot read before another transaction committed revocation. An already-authorized response cannot be recalled. Next rewrites change Host to the exact internal backend destination; the API accepts only that destination or the configured browser Host, alongside the exact browser Origin, and does not trust arbitrary forwarded headers.
