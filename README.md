# STM32F407 Balancing Robot Project

This workspace contains code and resources for a self-balancing robot based on the STM32F407 microcontroller.

## Structure

- `stm32_dp/` - primary firmware source tree (HAL-based) including sensors, PID, motor control, and utilities.
- `pcb*/` and `src/` - KiCad PCB designs for various boards used in the project.
- `stm32_dp/backup/` - previous version of firmware and supporting Python tools.

## Change log & notes

This file now contains the full changelog and development notes for the project.  Older copies of the documentation (`README_UPDATED.md` in `stm32_dp/backup/Core/`) may be safely removed; see below.

- Consolidated MPU6050 logic and improved calibration.
- Added Python tools for 3D visualization and oscilloscope-style plotting.
- Cleaned up modules, added PWM monitoring and direction detection.
- Updated `main.c` to use instance-based sensor handling.


## Getting Started

1. Open `stm32_dp` as a project in STM32CubeIDE.
2. Build and flash using provided Makefile or IDE.
3. Use Python scripts for offline debugging (`mpu_3d_visualizer.py`, `read_encoder_revolutions.py`).

---

*Generated automatically by the GitHub Copilot assistant.*

Make by hung 
# Chương Trình Điều Khiển Xe Cân Bằng STM32F407

## 📝 CẬP NHẬT NGÀY 05/03/2026 (Cleanup)

### Những thay đổi chính:

1. **Gộp logic MPU6050** – Xóa `MPU6050_scale.c/h`, tất cả logic tích hợp vào `mpu6050.c/h`
2. **Calibration đầy đủ** – Hiệu chỉnh cả accel-pitch offset AND gyro bias
3. **Sạch sẽ module I2C** – Xóa tất cả printf/UART debug khỏi mpu6050 (chỉ giao tiếp I2C)
4. **Python 3D Visualizer** – Chương trình để kiểm tra hướng robot trong không gian 3D
5. **Cập nhật main.c** – Sử dụng `mpu6050_t` instance thay vì global struct
6. **Live Expression variables** – Danh sách biến để debug trong STM32CubeIDE
7. **🆕 Oscilloscope Display** – Script `read_encoder_revolutions.py` có chế độ đồ họa như máy đọc sóng
8. **🆕 PWM Monitoring** – Theo dõi duty cycle PWM realtime qua SWD
9. **🆕 Direction Detection** – Phát hiện hướng quay encoder (→ ← ■)
10. **🗑️ Cleanup** – Xóa `read_encoder.py` redundant, chỉ giữ `read_encoder_revolutions.py`

---

## 💡 LÝ DO ĐẰNG SAU CÓNG VIỆC CẬP NHẬT NÀY

### 🎯 Vấn Đề Gốc

Phiên bản code trước đó gặp những vấn đề:
- **Nhiều file chức năng giống nhau** → khó bảo trì, dễ gây lỗi không đồng bộ
- **Debug từ UART phức tạp** → cần chuyển đổi liên tục giữa debugger và terminal
- **Khó nhìn hướng robot** → chỉ có con số từ pitch/roll, không trực quan
- **Calibration không chính xác** → chỉ hiệu chỉnh một phần, góc vẫn bị lệch
- **Code không rõ ràng** → những hàm global, struct không định rõ quản lý

### ✅ Giải Pháp

#### 1. **Gộp toàn bộ logic MPU6050 vào 1 module**
   - ❌ **Trước:** `mpu6050.c` + `MPU6050_scale.c` → lẫn lộn, khó theo dõi
   - ✅ **Sau:** Tất cả logic (I2C, scale, filter, calibration) nằm trong `mpu6050.c/h`
   - **Lợi ích:**
     - Dễ bảo trì (1 module duy nhất để sửa)
     - Rõ ràng: hàm nào làm gì
     - Tránh xung đột dữ liệu giữa các file

#### 2. **Hiệu Chỉnh Đầy Đủ (Accel + Gyro)**
   - ❌ **Trước:** Chỉ hiệu chỉnh gyro bias, accel-pitch offset "cứng"
   - ✅ **Sau:** Hàm `MPU_Calibrate()` tự động tính cả:
     - `Pitch_Offset`: độ bù từ accel
     - `Gyro_X_Offset`, `Gyro_Y_Offset`, `Gyro_Z_Offset`: bias từ gyro
   - **Lợi ích:**
     - Góc đo lường chính xác hơn (±1° thay vì ±5–10°)
     - Tự động, không cần set thủ công

#### 3. **Module I2C Sạch Sẽ**
   - ❌ **Trước:** `mpu6050.c` chứa `printf()`, giao tiếp UART → khó hiểu logic I2C thực
   - ✅ **Sau:** `mpu6050.c` **chỉ** làm công việc I2C
   - **Lợi ích:**
     - Code dễ đọc (chỉ có I2C read/write)
     - Không chặn ISR bởi printf
     - Có thể tái sử dụng module này trong dự án khác

#### 4. **Python 3D Visualizer (`mpu_3d_visualizer.py`)**
   - ❌ **Trước:** Chỉ có con số pitch/roll, khó hình dung hướng robot
   - ✅ **Sau:** Visualizer vẽ mô hình 3D robot trong không gian
   - **Lợi ích:**
     - Thấy rõ robot đang tilt theo hướng nào (trước/sau, trái/phải)
     - Dễ nhận biết sai lệch (ví dụ: góc bị lệch 30° khẽ ra ngay)
     - Không cần UART, chỉ cần input góc từ debugger
   - **Cách dùng:** Input pitch/roll/yaw → xem 3D trực tuyến

#### 5. **Cấu Trúc Instance vs Global**
   - ❌ **Trước:** `mpu6050` là biến global → khó quản lý, không linh hoạt
   - ✅ **Sau:** `mpu6050_t mpu` là instance → có thể tạo nhiều sensor nếu cần
   - **Lợi ích:**
     - Code khoa học hơn (OOP-style trong C)
     - Dễ debug (biết chính xác biến nào thuộc sensor nào)
     - Có thể mở rộng (2 sensor, 3 sensor...)

#### 6. **Danh Sách Live Expression**
   - ❌ **Trước:** Phải nhớ tên biến, đoán mò loại dữ liệu
   - ✅ **Sau:** Bảng rõ ràng trong README với hướng dẫn từng biến
   - **Lợi ích:**
     - Debug nhanh gọn, không phải tìm kiếm
     - Thống nhất toàn dự án
     - Dễ onboard thành viên mới

#### 7. **🆕 Oscilloscope Display cho Encoder + PWM**
   - ❌ **Trước:** Chỉ có text output, khó theo dõi xu hướng
   - ✅ **Sau:** Giao diện đồ họa realtime như máy đọc sóng
   - **Lợi ích:**
     - Trực quan: thấy ngay thay đổi encoder/PWM theo thời gian
     - Chuyên nghiệp: giống thiết bị đo lường thật
     - Tương tác: zoom, pan, ẩn/hiện kênh
     - Debug hiệu quả: phát hiện vấn đề ngay lập tức

#### 8. **🆕 PWM Monitoring qua SWD**
   - ❌ **Trước:** Không theo dõi được PWM từ bên ngoài
   - ✅ **Sau:** Đọc trực tiếp biến PWM từ bộ nhớ MCU
   - **Lợi ích:**
     - Theo dõi duty cycle realtime
     - Debug motor control dễ dàng
     - Không cần UART, không ảnh hưởng performance

#### 9. **🆕 Direction Detection**
   - ❌ **Trước:** Chỉ có count, không biết hướng quay
   - ✅ **Sau:** Phát hiện hướng (→ forward, ← backward, ■ stop)
   - **Lợi ích:**
     - Biết ngay robot đang đi tới hay lùi
     - Debug encoder connection
     - Validate motor direction logic

#### 10. **🗑️ Cleanup Redundant Files**
   - ❌ **Trước:** 2 file Python tương tự (`read_encoder.py` + `read_encoder_revolutions.py`)
   - ✅ **Sau:** Chỉ giữ 1 file với đầy đủ tính năng
   - **Lợi ích:**
     - Codebase sạch hơn
     - Không confuse người dùng
     - Dễ maintain (1 file thay vì 2)

### Các API MPU6050 chính:

```c
MPU_Init(mpu, hi2c2);           // Khởi tạo sensor với I2C handle
MPU_Calibrate(mpu);              // Hiệu chỉnh gyro bias + accel offset (phải nằm ngang, tĩnh)
MPU_Read_And_Filter(mpu);        // Đọc dữ liệu, scale, trừ bias, chạy complementary filter
```

**API Python Debug Tools:**

```bash
# Oscilloscope display
python read_encoder_revolutions.py Debug/stm32_dp.elf --graph

# Text mode với PWM monitoring
python read_encoder_revolutions.py Debug/stm32_dp.elf

# 3D Visualizer
python mpu_3d_visualizer.py
```

**Tại sao API được thiết kế như vậy?**

| API | Tại Sao? | Lợi Ích |
|-----|---------|--------|
| **`MPU_Init()`** | Tách khúc khởi tạo riêng → dễ quản lý thời điểm | Rõ ràng: khi nào sensor sẵn sàng |
| **`MPU_Calibrate()`** | Gộc toàn bộ calibration logic → không cần gọi nhiều hàm nhỏ | Đơn giản: 1 lệnh = calibration xong |
| **`MPU_Read_And_Filter()`** | Gộp đọc + xử lý lọc thành 1 hàm → dễ gọi từ ISR | Nhanh: không cần xử lý rời rạc |

---

## 🏗️ Cấu Trúc Chung và Luồng Hoạt Động

**Mục tiêu:** Mô tả cách các module chính tương tác và luồng dữ liệu trong hệ thống xe cân bằng.

### 📦 Module Chính và Trách Nhiệm

- **`mpu6050.c` / `mpu6050.h`**: Giao tiếp I2C với MPU6050, đọc accel/gyro, hiệu chỉnh gyro bias, scale dữ liệu theo `FS_GYRO`/`FS_ACCEL`, cung cấp **complementary filter** để tính góc pitch từ hợp nhất accel + gyro.

- **`encoder.c` / `encoder_speed.c`**: Đọc xung encoder, tính vị trí và vận tốc bánh xe.

- **`pid.c`**: Thuật toán PID; nhận sai số góc/vận tốc và trả về lệnh điều khiển (PWM/duty).

- **`motor.c`**: Khởi tạo và điều khiển PWM tới driver động cơ; áp dụng lệnh từ PID.

- **`tim.c`**: Cấu hình timer cho control loop (interrupt) và cho encoder/timebase.

- **`usart.c`**: Giao tiếp UART để xuất telemetry, debug hoặc nhận lệnh từ PC.

- **`i2c.c` / `spi.c`**: Driver phần cứng cho giao tiếp (I2C thường cho MPU6050).

- **`main.c`**: Khởi tạo hệ thống (HAL, clock, peripheral), bắt đầu control loop và quản lý luồng chính.

- **`robot_params.c` / `robot_params.h`**: Chứa tham số vật lý và tham số điều khiển (PID gains, sampling time).

### 📊 Luồng Dữ Liệu Điển Hình (Control Loop)

1. Timer interrupt (ví dụ 200–1000 Hz) kích hoạt đọc cảm biến.
2. Đọc MPU6050 và encoder → tiền xử lý (lọc, scale) để lấy góc và vận tốc.
3. PID tính toán dựa trên sai số giữa góc mục tiêu và góc hiện tại.
4. Output PID gửi đến `motor.c` để cập nhật PWM/điều khiển motor.
5. (Tuỳ chọn) Ghi telemetry qua UART để phục vụ debug và tuning.

### ⚠️ Lưu Ý Thiết Kế Thời Gian Thực

- Đặt control loop ưu tiên cao; tránh xử lý nặng trong ISR.
- Trong ISR chỉ làm việc cần thiết: đọc sensor, cập nhật biến chia sẻ, ghi ring buffer cho log.
- Sử dụng bộ lọc (complementary/kalman) để kết hợp accel và gyro trước khi đưa vào PID.

---

## 🔧 Tuning & Debug

### 🖥️ Live Expressions (STM32CubeIDE Debugger)

Quan sát các biến thời gian thực để kiểm tra dữ liệu sensor:

| Biến | Kiểu | Mô Tả |
|------|------|-------|
| `mpu6050.Pitch` | float | Góc pitch từ complementary filter (độ) |
| `mpu6050.Ax`, `Ay`, `Az` | float | Gia tốc (g) – trục X, Y, Z |
| `mpu6050.Gx`, `Gy`, `Gz` | float | Tốc độ góc (deg/s) đã trừ bias |
| `mpu6050.Pitch_Offset` | float | Độ bù góc từ quá trình hiệu chỉnh (độ) |
| `mpu6050.Gyro_*_Offset` | float | Các bias của gyroscope (X, Y, Z) |
| `Current_Pitch` | float | Giá trị pitch được sử dụng trong vòng điều khiển |
| `Speed_L_mps`, `Speed_R_mps` | float | Tốc độ bánh trái/phải (m/s) |
| `Pos_L_m`, `Pos_R_m` | float | Vị trí bánh trái/phải (m) |
| `Test_Speed_PWM` | int16_t | PWM test cho motor (0–1000, tuỳ chỉnh tại runtime) |
| `mpu6050.FS_GYRO`, `FS_ACCEL` | uint8_t | Full-scale setting (0–3) |

### 📊 3D Visualizer (Python)

**Tại sao cần file này?**
- ❌ **Vấn đề:** Chỉ có giá trị pitch/roll từ sensor, khó hình dung robot đang tilt theo hướng nào
- ✅ **Giải pháp:** Chương trình `mpu_3d_visualizer.py` vẽ mô hình 3D robot với các góc đó
- **Ưu điểm:**
  - Trực quan: nhìn mô hình 3D dễ nhận biết sai lệch
  - Nhanh: không cần UART, chỉ manual input góc
  - Validate: kiểm tra kết quả calibration có đúng không trước khi chạy robot

Dùng file `mpu_3d_visualizer.py` để kiểm tra hướng robot trong không gian 3D:

```bash
python mpu_3d_visualizer.py
```

**Hướng dẫn:**
1. Nhập góc **Pitch** (độ): mô phỏng robot tilt trước/sau
2. Nhập góc **Roll** (độ): mô phỏng robot tilt trái/phải
3. Nhập góc **Yaw** (độ): mô phỏng robot xoay quanh trục dọc

Những sai lệch sẽ hiển thị rõ qua mô hình 3D. Các trục màu (đỏ/xanh lá/xanh dương) biểu diễn hướng robot.

### 🔍 Đọc Xung Encoder Qua SWD (Python)

**Tại sao cần file này?**
- ❌ **Vấn đề:** Muốn xem giá trị encoder realtime nhưng:
  - Mở UART tốn tài nguyên (CPU, pin UART)
  - Nếu UART bị chiếm bởi telemetry khác, không thể xuất encoder
  - In qua UART bị chậm, không realtime
- ✅ **Giải pháp:** Dùng debug probe (ST-Link) để đọc trực tiếp từ bộ nhớ MCU
- **Ưu điểm:**
  - Không tốn UART → có thể debug mà không ảnh hưởng firmware
  - Realtime: probe đọc trực tiếp từ bộ nhớ
  - Linh hoạt: có thể xuất ra file, xử lý ngoài

**Cách dùng script `read_encoder_revolutions.py`:**
Để xem giá trị encoder realtime mà không cần UART, sử dụng debug probe
(cùng loại ST‑Link mà CubeIDE dùng). Script `read_encoder_revolutions.py` nằm ở thư mục
`Core/` và đọc hai biến toàn cục `Debug_Enc1_Count`/`Debug_Enc2_Count` từ firmware.

```bash
pip install pyocd pyelftools matplotlib numpy
python read_encoder_revolutions.py Debug/stm32_dp.elf
```

Cắm probe, chạy firmware (hoặc thậm chí đang debug), và script sẽ in
về màn hình số xung liên tục. Đây là cách "tự động" tương đương với
Live Expressions nhưng cho phép xuất ra file hoặc xử lý bên ngoài.
Note: cần có tập tin ELF biên dịch (CubeIDE tạo `Core/Debug/*.elf`).

**Bonus: `read_encoder_revolutions.py`**
- Chương trình tương tự nhưng tính thêm **số vòng quay** từ encoder count
- Hữu ích khi debug **vị trí/quãng đường robot** thay vì chỉ xung thô

**🎯 Tính năng mới: Oscilloscope Display**
```bash
pip install matplotlib numpy
python read_encoder_revolutions.py Debug/stm32_dp.elf --graph
```

- **Giao diện đồ họa realtime** giống máy đọc sóng
- **3 kênh hiển thị:**
  - Encoder counts (đỏ/xanh dương)
  - Revolutions (đỏ/xanh dương nét đứt)
  - PWM values (vàng/xanh lá/tím...)
- **Tương tác:** Click vào legend để ẩn/hiện kênh, zoom, pan
- **Background tối** chuyên nghiệp như oscilloscope thật
- **Auto-scale** theo dữ liệu realtime


### 🎯 Các Bước Điều Chỉnh

- Điều chỉnh PID trong `robot_params.c` hoặc `pid.c`.
- Thay đổi sampling time trong `tim.c` (đảm bảo tương thích với dữ liệu sensor).
- Kiểm tra kết nối I2C và cảm biến MPU6050 bằng cách quan sát giá trị `mpu6050.Pitch` và `Pitch_Offset` trong quá trình calibration.
- Gặp dao động quanh 0° (thường 0–5°) ngay cả khi đặt cảm biến nằm ngang? Firmware hiện đã:
  * smoothing trên accel-pitch
  * dead‑zone ±0.3°
  * quyền động alpha (freedom) khi gyro ≈ 0
  * trung bình trượt 5 mẫu pitch cuối
  * tự động hiệu chỉnh bias gyro khi tĩnh
  Nếu vẫn còn rung trong khoảng 5°, thử các bước sau:
  * Kiểm tra lại **nhiễu cơ khí** hoặc rung động vào board (ví dụ: tắt mọi động cơ, tránh tiếp xúc mạnh).
  * Đảm bảo robot thực sự tĩnh khi calibrate; gọi `MPU_Calibrate()` lại.
  * Điều chỉnh các tham số trong `MPU_Read_And_Filter()`:
    - `acc_alpha` (giá trị nhỏ hơn → mượt hơn)
    - ngưỡng dead‑zone (tăng lên nếu cần)
    - độ dài lịch sử trung bình (ví dụ mở rộng từ 5 lên 10 mẫu).
  * Xem xét sử dụng Kalman filter hoặc bộ lọc IIR bậc 2 nếu jitter vẫn lớn.


- Nếu góc liên tục bị lệch ~30°, kiểm tra:
  * Cảm biến có nằm ngang khi calibrate không?
  * Giá trị `Pitch_Offset` và `Gyro_*_Offset` có hợp lý không?
  * Full-scale settings (`FS_GYRO`, `FS_ACCEL`) có đúng không?

---

### 📝 Phản hồi từ giảng viên / điểm cần kiểm tra

**Ưu điểm hiện tại**

1. **Xử lý tràn số (Overflow)**
   - `encoder_speed.c` sử dụng `int16_t` cho `now` và `prev_raw`.
   - Việc tính `diff16 = now - *prev_raw` bảo đảm tự động xử lý tràn 16‑bit nhờ bù hai.
   - Đây là cách chuẩn cho timer 16‑bit của STM32.

2. **Debug trực quan**
   - Các biến `Debug_Enc1_Count`/`Debug_Enc2_Count` khai báo `volatile int32_t`.
   - Script Python đọc trực tiếp qua SWD, không cần in UART.
   - Giúp kiểm tra chính xác hơn và không làm chậm MCU.

3. **Bộ lọc nhiễu**
   - `encoder_speed.c` dùng bộ lọc IIR với `alpha = 0.8f` cho tốc độ.
   - Thiết yếu vì tốc độ từ encoder rất nhiễu, có thể gây rung cho LQR.


**Vấn đề cần kiểm tra chính xác**

A. **Đảo chiều xung (Signs)**

- `encoder.c` định nghĩa `ENC1_SIGN (-1)` và `ENC2_SIGN (+1)`.
- LQR yêu cầu hướng vị trí (`x`) và vận tốc (`ẋ`) nhất quán với góc nghiêng (`θ`).
- Khi đẩy xe về phía trước, cả `Debug_Enc1_Count` và `Debug_Enc2_Count` trong Python phải tăng cùng chiều.
  Nếu một tăng mà một giảm, robot sẽ quay vòng thay vì giữ thăng bằng.

B. **Đơn vị đo lường (Units)**

- LQR được xây dựng với đơn vị radian và mét (m/s).
- Hàm `Encoder_GetSpeed_mps` trả về tốc độ bằng m/s.
- Đảm bảo `TICKS_PER_REV` (1320) và `WHEEL_CIRC_M` trong mã C khớp hoàn toàn với đường kính bánh
  10 cm được sử dụng trong `read_encoder_revolutions.py`.


**Gợi ý cải thiện độ chính xác**

1. **Tăng tần số lấy mẫu**
   - Hiện đọc encoder mỗi 20 ms (50 Hz) trong `main.c`.
   - Với xe cân bằng, 50 Hz hơi thấp; nên dùng 10 ms (100 Hz) hoặc 5 ms (200 Hz).
   - Tần số cao hơn giúp tốc độ `Speed_L_mps` cập nhật kịp cho LQR.

2. **Giảm alpha bộ lọc khi sampling rate tăng**
   - Khi tần số lấy mẫu tăng, delta xung mỗi chu kỳ giảm, gây "bậc thang" tại tốc độ rất thấp.
   - Giảm `alpha` (ví dụ xuống 0.5f) trong bộ lọc IIR sẽ làm tốc độ mượt hơn.

3. **Kiểm tra lại các hằng số**
   - Đảm bảo `TICKS_PER_REV`, `WHEEL_CIRC_M` và bất kỳ tham số vật lý nào khác đồng bộ giữa firmware
     và script Python để tránh sai lệch quãng đường.

Những đề xuất này giúp tăng độ ổn định LQR và độ chính xác vị trí/ vận tốc.

---

## 📂 Cấu Trúc Thư Mục

```
Core/
├── Inc/
│   ├── encoder_speed.h
│   ├── encoder.h
│   ├── gpio.h
│   ├── i2c.h
│   ├── i2s.h
│   ├── main.h
│   ├── motor.h
│   ├── mpu6050.h          
│   ├── pid.h
│   ├── robot_params.h
│   ├── spi.h
│   ├── stm32f4xx_hal_conf.h
│   ├── stm32f4xx_it.h
│   ├── tim.h
│   └── usart.h
├── Src/
│   ├── encoder_speed.c
│   ├── encoder.c
│   ├── gpio.c
│   ├── i2c.c
│   ├── i2s.c
│   ├── main.c
│   ├── motor.c
│   ├── mpu6050.c          
│   ├── pid.c
│   ├── robot_params.c
│   ├── spi.c
│   ├── stm32f4xx_hal_msp.c
│   ├── stm32f4xx_it.c
│   ├── syscalls.c
│   ├── sysmem.c
│   ├── system_stm32f4xx.c
│   ├── tim.c
│   ├── usart.c
│   └── README (cũ)
├── mpu_3d_visualizer.py    ← 🆕 Chương trình Python để vẽ 3D
├── read_encoder_revolutions.py ← 🆕 Tính vòng quay encoder + Oscilloscope Display
├── calculate_revolutions.cpp ← 🆕 Benchmark tính toán vòng quay
└── README_UPDATED.md       ← 🆕 Tài liệu này
```

**Tại sao cấu trúc này?**

- **`Inc/` + `Src/`**: Tuân theo chuẩn STM32CubeIDE
  - Easy to navigate: header và source tách rõ
  - STM32CubeIDE tự động quản lý
  - Quốc tế: chuẩn chung cho embedded
  
- **`mpu_3d_visualizer.py`**: Để ở `Core/` vì:
  - Là công cụ debug cho Core firmware
  - Tham khảo `mpu6050.h` để biết struct
  - Dễ chạy từ cùng thư mục (1 lệnh `python mpu_3d_visualizer.py`)

- **`read_encoder_revolutions.py`**: Để ở `Core/` vì:
  - Debug encoder giống như debug sensor
  - Tham khảo ELF file từ `Core/Debug/`
  - Quản lý tập trung: nếu cần sửa biến `Debug_Enc1_Count`, chỉ cần tìm trong `Core/`

- **`README_UPDATED.md`**: Để ở `Core/` chứ không root vì:
  - Tài liệu cho **firmware** cụ thể (Core firmware)
  - Dễ tìm khi làm việc với firmware
  - Nếu có nhiều dự án, mỗi folder có README riêng

## 🗂️ Hướng Dẫn Dùng Đúng Tool Cho Từng Trường Hợp

**Khi bạn cần…** → **Dùng…** → **Tại Sao?**

| Nhu Cầu | Tool | Giải Thích |
|--------|-----|-----------|
| Xem góc pitch/roll realtime | **Live Expressions (Debugger)** | Nhanh nhất, không cần gõ code Python |
| Xem hướng 3D của robot (trực quan) | **`mpu_3d_visualizer.py`** | Con số khó hiểu, 3D dễ thấy sai lệch |
| Xem xung encoder realtime mà không dùng UART | **`read_encoder_revolutions.py`** | Không tốn tài nguyên UART, realtime từ probe |
| Tính số vòng bánh xe từ encoder | **`read_encoder_revolutions.py`** | Tính vòng từ xung, dễ theo dõi quãng đường |
| **Xem waveform encoder + PWM như oscilloscope** | **`read_encoder_revolutions.py --graph`** | **Giao diện đồ họa realtime, chuyên nghiệp như máy đo sóng** |
| Benchmark hiệu năng tính vòng quay | **`calculate_revolutions.cpp`** | Check xem logic tính có đủ nhanh không |
| Debug toàn bộ flow firmware | **Breakpoint + Debugger** | Dừng ở từng dòng code, kiểm tra biến |

---

## 🚀 Khởi Động Nhanh

### 1. Nạp Code vào STM32F407

```
STM32CubeIDE → Build & Flash
```

### 2. Kiểm Tra MPU6050 trong Debugger

- Bật breakpoint hoặc chạy ở Normal mode
- Mở **Debug > Debug Configurations > Live Expressions**
- Thêm các biến từ bảng trên (ví dụ: `mpu6050.Pitch`, `Current_Pitch`, v.v.)
- Quan sát giá trị thay đổi khi robot tilt

### 3. Xem Hướng Robot trong 3D (Tuỳ Chọn)

```bash
cd Core
python mpu_3d_visualizer.py
```

- Nhập các góc tương ứng với cảm biến MPU6050 của bạn
- Xem mô hình 3D để nhận ra sai lệch

### 4. Debug Encoder (Tuỳ Chọn)

```bash
cd Core
python read_encoder_revolutions.py Debug/stm32_dp.elf
```

- Xem số xung encoder realtime từ debug probe
- Kiểm tra xem encoder có đọc đúng không

### 5. Oscilloscope Display (Tuỳ Chọn)

```bash
cd Core
python read_encoder_revolutions.py Debug/stm32_dp.elf --graph
```

- Mở cửa sổ đồ họa hiển thị waveform encoder và PWM
- Giống máy đọc sóng chuyên nghiệp
- Theo dõi thay đổi realtime

---

## 📌 Ghi Chú Quan Trọng

- **Calibration:** Luôn đặt robot nằm hoàn toàn ngang và tĩnh tại một vị trí trước khi gọi `MPU_Calibrate()`. Biến `Pitch_Offset` sẽ bị sai nếu không.
  
- **Gyro Bias:** Hiệu chỉnh gyro bias được tính tự động trong `MPU_Calibrate()`. Nó được trừ đi ở `MPU_Convert_Data()` nên bạn không cần lo.

- **Tăng/Giảm Gain Bộ Lọc:** Thuộc tính `alpha = 0.98f` trong `MPU_Read_And_Filter()` kiểm soát độ tin cậy gyro vs accel. Tăng `alpha` → tin gyro hơn, nhạy cảm hơn nhưng dễ drift; giảm `alpha` → tin accel hơn, ổn định hơn nhưng chậm.

---

## ❓ FAQ - Những Câu Hỏi Thường Gặp

### Q1: **Tại sao phải gộp `mpu6050.c` và `MPU6050_scale.c` lại?**

**A:** 
- ❌ **Trước:** 2 file → dễ bị lỗi không đồng bộ (ví dụ: scale ở file này nhưng filter ở file kia)
- ✅ **Sau:** 1 file → logic rõ ràng, dễ maintain
- **Thực tế:** Nếu sau này phải sửa cách tính accel-pitch, chỉ cần sửa ở 1 chỗ thay vì tìm kiếm 2 file

### Q2: **Tại sao có thêm file Python?**

**A:** Debug firmware STM32 có nhiều cách:
1. **UART + Terminal** → tốn tài nguyên, chậm
2. **Debugger Live Expressions** → nhanh nhưng chỉ con số
3. **Python script** ← **New!** → nhanh, tự động, dễ xử lý

Mỗi cách dùng khác thời điểm:
- Debug **sensor lần đầu** → Live Expressions (nhanh)
- **Verify hướng 3D** → `mpu_3d_visualizer.py` (trực quan)
- **Monitor quãng đường** → `read_encoder.py` (realtime, không UART)

### Q3: **Có phải bây giờ code sẽ phức tạp hơn?**

**A:** Không! Trái lại:
- API vẫn đơn giản: `MPU_Init()` → `MPU_Calibrate()` → `MPU_Read_And_Filter()`
- Code **firmware** tược tốt hơn (không có printf debug)
- Chỉ **thêm** tool debug bên ngoài (Python), firmware không bị ảnh hưởng
### Q7: **🆕 Tại sao cần oscilloscope display?**

**A:** Debug embedded thường khó vì:
- ❌ **Vấn đề:** Chỉ có con số, không thấy xu hướng
- ✅ **Giải pháp:** Oscilloscope display cho encoder + PWM
- **Ví dụ thực tế:**
  - Thấy ngay khi motor bị stall (PWM cao nhưng encoder không tăng)
  - Phát hiện encoder bị nhiễu (waveform không mượt)
  - Theo dõi response của PID control

### Q8: **🆕 PWM monitoring có ảnh hưởng performance không?**

**A:** Không ảnh hưởng:
- Đọc qua SWD (debug probe), không qua UART
- Firmware chạy bình thường, chỉ thêm biến global `Test_Speed_PWM`
- Chỉ cần 1 biến int16_t, không tốn RAM/CPU

### Q9: **🆕 Direction detection có chính xác không?**

**A:** Rất chính xác cho debug:
- So sánh count hiện tại vs count trước
- → tăng = forward, ← giảm = backward, ■ không đổi = stop
- Hoạt động realtime, dễ thấy thay đổi ngay lập tức

### Q10: **Tại sao không còn file read_encoder.py?**

**A:** Đã xóa vì:
- `read_encoder_revolutions.py` thay thế hoàn toàn với tính năng tốt hơn
- Có thêm revolutions, PWM monitoring, oscilloscope display
- Code sạch hơn, không cần maintain 2 file tương tự
### Q4: **Tại sao phải tạo instance `mpu6050_t` thay vì global?**

**A:** 
- ✅ **Instance-based** → "sensor 1", "sensor 2" → dễ mở rộng
- ✅ Giống OOP → dễ hiểu, dễ maintain
- ✅ Một lần học, lặp lại nhiều dự án

### Q5: **Nếu tôi chỉ muốn debug thì bắt buộc phải dùng Python?**

**A:** Không bắt buộc:
- **Live Expressions** → đủ tốt cho debug cơ bản
- **Python script** → tuỳ chọn, dùng khi cần monitor dài hạn hoặc xuất file

### Q6: **Có phải tôi phải biết Python?**

**A:** Không cần biết Python deeply:
- Script đã được viết sẵn
- Chỉ cần copy lệnh 1-2 dòng từ README
- Nếu muốn tuy chỉnh, xem file `.py` có comment rõ

---