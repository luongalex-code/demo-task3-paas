# CLOUD COMPUTING – TASK 03

Ứng dụng Python Flask minh họa triển khai theo mô hình **PaaS (Platform as a Service)** trên **Render**. Với PaaS, người phát triển cung cấp mã nguồn và lệnh chạy; nền tảng cung cấp môi trường thực thi và vận hành dịch vụ web.

Ứng dụng có một trang giới thiệu và một nút gọi backend để kiểm tra hoạt động. Không sử dụng cơ sở dữ liệu, Docker, API bên ngoài hoặc dịch vụ cloud khác trong ứng dụng.

## 1. Cấu trúc dự án

```text
paas-task03/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
├── static/
│   └── style.css
└── README.md
```

`app.py` định nghĩa hai endpoint. `index.html` chứa giao diện và JavaScript gọi `/health`. `style.css` tạo giao diện responsive bằng CSS thuần, không dùng font hoặc thư viện từ CDN.

## 2. Cài đặt và chạy trên Windows

1. Cài Python 3.11 trở lên từ [python.org](https://www.python.org/downloads/windows/). Nếu trình cài đặt có tùy chọn **Add Python to PATH**, hãy bật tùy chọn đó.
2. Mở PowerShell và kiểm tra `python --version`. Nếu máy dùng Python Launcher, có thể thay `python` bằng `py` ở lệnh tạo môi trường.
3. Chạy lần lượt:

```powershell
cd "C:\Class\Cloud\paas-task03"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Không cần activate môi trường, vì các lệnh gọi trực tiếp Python trong `.venv`. Mở **http://127.0.0.1:5000**. Dừng ứng dụng bằng **Ctrl+C** tại PowerShell.

Nếu cổng 5000 đang được dùng, đổi cổng bằng biến môi trường:

```powershell
$env:PORT = "5001"
.\.venv\Scripts\python.exe app.py
```

Khi đó mở **http://127.0.0.1:5001**. Muốn trở về cổng mặc định:

```powershell
Remove-Item Env:PORT -ErrorAction SilentlyContinue
```

**Windows chạy local bằng `python app.py`. Render chạy bằng `gunicorn app:app`.** Gunicorn không chạy trực tiếp trên Windows; nó được sử dụng trong môi trường Linux của Render. Cài được gói Gunicorn trên Windows không có nghĩa là có thể khởi chạy nó tại đây. Tham khảo [tài liệu Flask về Gunicorn](https://flask.palletsprojects.com/en/stable/deploying/gunicorn/).

## 3. Kiểm tra ứng dụng

| Phương thức | Đường dẫn | Kết quả mong đợi |
| --- | --- | --- |
| GET | `/` | HTTP 200 và giao diện HTML |
| GET | `/health` | HTTP 200 và JSON trạng thái |

JSON của `/health`:

```json
{
  "status": "ok",
  "message": "Python Flask application is running successfully"
}
```

Trên giao diện, nhấn **Kiểm tra ứng dụng**. JavaScript gửi `fetch('/health')` đến chính Flask đang phục vụ website. Khung phản hồi hiển thị JSON thực nhận và mã HTTP 200. Nếu không kết nối được hoặc quá thời gian chờ, trang hiển thị thông báo lỗi và cho phép thử lại.

Có thể kiểm tra trong PowerShell khác khi server đang chạy:

```powershell
(Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -UseBasicParsing).StatusCode
Invoke-RestMethod -Uri "http://127.0.0.1:5000/health"
```

Kiểm tra cú pháp Python:

```powershell
.\.venv\Scripts\python.exe -m py_compile app.py
```

Thứ tự hai khóa trong JSON không ảnh hưởng ý nghĩa của phản hồi.

## 4. Đẩy mã nguồn lên GitHub

Cài Git từ [git-scm.com](https://git-scm.com/downloads), đăng nhập GitHub và tạo một repository trống, ví dụ `paas-task03`. Không khởi tạo README riêng trên GitHub nếu đã có README local.

Trong thư mục `C:\Class\Cloud\paas-task03`, chạy:

```powershell
git init
git add app.py requirements.txt templates/index.html static/style.css README.md
git commit -m "Create Flask PaaS demo for Task 03"
git branch -M main
git remote add origin https://github.com/luongalex-code/demo-task3-paas.git
git push -u origin main
```

Git có thể yêu cầu đăng nhập bằng trình duyệt. Nếu Git yêu cầu danh tính, cấu hình tên/email của bạn trước khi commit. Các lệnh `git add` chỉ chọn mã nguồn; không đưa `.venv` hoặc `__pycache__` lên GitHub.

Với cách này, `app.py` và `requirements.txt` nằm ngay ở thư mục gốc repository.

## 5. Triển khai lên Render

1. Đăng nhập [Render Dashboard](https://dashboard.render.com/).
2. Chọn **New → Web Service**.
3. Kết nối GitHub và chọn repository `demo-task3-paas`.
4. Điền cấu hình:

| Mục | Giá trị |
| --- | --- |
| Name | Tên duy nhất bạn chọn, ví dụ `paas-task03-demo` |
| Language / Runtime | Python 3 |
| Branch | `main` |
| Root Directory | Để trống khi `app.py` ở gốc repository |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Health Check Path | `/health` |

Nếu đẩy cả thư mục `paas-task03` vào bên trong một repository khác, đặt **Root Directory** thành `paas-task03` tương ứng với vị trí thực tế trong repository.

5. Chọn gói phù hợp cho bài thực hành. Nếu Render có tùy chọn **Free**, có thể dùng gói đó và xem giới hạn được hiển thị trên dashboard.
6. Chọn **Create Web Service**, theo dõi build/deploy logs. Chờ dịch vụ báo **Live** rồi mở URL mà Render cấp.

Hai lệnh trên theo [hướng dẫn triển khai Flask của Render](https://render.com/docs/deploy-flask). `app:app` nghĩa là import biến Flask `app` từ tệp `app.py`.

Không cần đặt cứng cổng trong cấu hình triển khai. Render cung cấp biến `PORT`; Gunicorn sử dụng cấu hình bind mặc định theo biến này. Khi chạy local bằng `python app.py`, mã nguồn đọc `PORT` nếu có, ngược lại dùng cổng 5000. Tham khảo [yêu cầu port binding của Render](https://render.com/docs/web-services#port-binding).

## 6. Kiểm tra sau deploy

Thay `<ten-dich-vu>` bằng tên/URL thực tế do Render cấp:

1. Mở `https://<ten-dich-vu>.onrender.com/` và kiểm tra giao diện.
2. Nhấn **Kiểm tra ứng dụng**, xác nhận có `200 OK` và JSON đúng cấu trúc.
3. Mở trực tiếp `https://<ten-dich-vu>.onrender.com/health` để kiểm tra JSON.
4. Có thể mở Developer Tools → **Network**, nhấn nút và kiểm tra yêu cầu `/health` trả HTTP 200.

Nếu website chưa tải, kiểm tra trạng thái deploy và logs trên Render. Nếu dùng gói có cơ chế tạm nghỉ khi không hoạt động, lần truy cập đầu có thể cần chờ dịch vụ khởi động rồi thử lại.

Nếu báo `ModuleNotFoundError: app`, kiểm tra Root Directory và vị trí `app.py`. Nếu thiếu Flask/Gunicorn, kiểm tra Build Command và `requirements.txt` đã được đẩy lên GitHub.

## 7. Ảnh minh chứng cần chụp

- Giao diện chạy local với URL `127.0.0.1` trên thanh địa chỉ.
- Local sau khi nhấn nút: có `200 OK` và JSON phản hồi.
- Repository GitHub hiển thị đủ các tệp nguồn.
- Trang cấu hình Render: Python, Build Command, Start Command và Root Directory.
- Logs build thành công và khởi chạy Gunicorn trên Render.
- Dashboard có trạng thái **Live** và URL được cấp.
- Giao diện mở bằng URL Render sau khi nhấn **Kiểm tra ứng dụng**.
- Endpoint `/health` trên URL Render trả JSON đúng, hoặc Network ghi HTTP 200.

Chỉ ghi nhận triển khai thành công sau khi đã mở URL Render và kiểm tra thực tế. Mã nguồn và ảnh local không phải bằng chứng ứng dụng đã chạy trên cloud.

## 8. Nội dung trình bày ngắn với giảng viên

“Em sử dụng Flask để tạo trang web và endpoint kiểm tra `/health`. Mã nguồn được lưu trên GitHub. Render lấy mã nguồn, cài thư viện bằng pip và khởi chạy ứng dụng bằng Gunicorn. Khi nhấn nút kiểm tra, trình duyệt gửi yêu cầu đến backend và nhận JSON. Đây là ví dụ PaaS vì em triển khai mã nguồn lên môi trường do nền tảng cung cấp, thay vì tự cấu hình máy chủ.”

Các công cụ cài đặt, GitHub và Render phục vụ quá trình phát triển/triển khai; khi hoạt động, ứng dụng chỉ sử dụng chính Flask và các tệp HTML/CSS/JavaScript của dự án.
