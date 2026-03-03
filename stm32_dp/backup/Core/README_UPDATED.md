# Chương Trình Điều Khiển Xe Cân Bằng STM32F407

## 📝 CẬP NHẬT NGÀY 03/03/2026

### Những thay đổi chính:

1. **Gộp logic MPU6050** – Xóa `MPU6050_scale.c/h`, tất cả logic tích hợp vào `mpu6050.c/h`
2. **Calibration đầy đủ** – Hiệu chỉnh cả accel-pitch offset AND gyro bias
3. **Sạch sẽ module I2C** – Xóa tất cả printf/UART debug khỏi mpu6050 (chỉ giao tiếp I2C)
4. **Python 3D Visualizer** – Chương trình để kiểm tra hướng robot trong không gian 3D
5. **Cập nhật main.c** – Sử dụng `mpu6050_t` instance thay vì global struct
6. **Live Expression variables** – Danh sách biến để debug trong STM32CubeIDE

### Các API MPU6050 chính:

```c
MPU_Init(mpu, hi2c2);           // Khởi tạo sensor với I2C handle
MPU_Calibrate(mpu);              // Hiệu chỉnh gyro bias + accel offset (phải nằm ngang, tĩnh)
MPU_Read_And_Filter(mpu);        // Đọc dữ liệu, scale, trừ bias, chạy complementary filter
```

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

Dùng file `mpu_3d_visualizer.py` để kiểm tra hướng robot trong không gian 3D:

```bash
python mpu_3d_visualizer.py
```

**Hướng dẫn:**
1. Nhập góc **Pitch** (độ): mô phỏng robot tilt trước/sau
2. Nhập góc **Roll** (độ): mô phỏng robot tilt trái/phải
3. Nhập góc **Yaw** (độ): mô phỏng robot xoay quanh trục dọc

Những sai lệch sẽ hiển thị rõ qua mô hình 3D. Các trục màu (đỏ/xanh lá/xanh dương) biểu diễn hướng robot.

### 🎯 Các Bước Điều Chỉnh

- Điều chỉnh PID trong `robot_params.c` hoặc `pid.c`.
- Thay đổi sampling time trong `tim.c` (đảm bảo tương thích với dữ liệu sensor).
- Kiểm tra kết nối I2C và cảm biến MPU6050 bằng cách quan sát giá trị `mpu6050.Pitch` và `Pitch_Offset` trong quá trình calibration.
- Nếu góc liên tục bị lệch ~30°, kiểm tra:
  * Cảm biến có nằm ngang khi calibrate không?
  * Giá trị `Pitch_Offset` và `Gyro_*_Offset` có hợp lý không?
  * Full-scale settings (`FS_GYRO`, `FS_ACCEL`) có đúng không?

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
│   ├── mpu6050.h          ← Module I2C duy nhất cho MPU6050
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
│   ├── mpu6050.c          ← Module I2C duy nhất cho MPU6050
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
└── README_UPDATED.md       ← 🆕 Tài liệu này
```

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

### 3. Xem Hướng Robot trong 3D

```bash
cd Core
python mpu_3d_visualizer.py
```

- Nhập các góc tương ứng với cảm biến MPU6050 của bạn
- Xem mô hình 3D để nhận ra sai lệch

---

## 📌 Ghi Chú Quan Trọng

- **Calibration:** Luôn đặt robot nằm hoàn toàn ngang và tĩnh tại một vị trí trước khi gọi `MPU_Calibrate()`. Biến `Pitch_Offset` sẽ bị sai nếu không.
  
- **Gyro Bias:** Hiệu chỉnh gyro bias được tính tự động trong `MPU_Calibrate()`. Nó được trừ đi ở `MPU_Convert_Data()` nên bạn không cần lo.

- **Tăng/Giảm Gain Bộ Lọc:** Thuộc tính `alpha = 0.98f` trong `MPU_Read_And_Filter()` kiểm soát độ tin cậy gyro vs accel. Tăng `alpha` → tin gyro hơn, nhạy cảm hơn nhưng dễ drift; giảm `alpha` → tin accel hơn, ổn định hơn nhưng chậm.

---


