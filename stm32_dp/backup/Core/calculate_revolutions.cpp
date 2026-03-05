#include <iostream>
#include <iomanip>

using namespace std;

int main() {
    // Thông số encoder từ robot_params.h
    const int ENCODER_PPR = 11;        // xung/vòng/kênh
    const int QUAD_FACTOR = 4;         // quadrature x4
    const float GEAR_RATIO = 30.0f;    // tỷ lệ truyền
    const float TICKS_PER_REV = ENCODER_PPR * QUAD_FACTOR * GEAR_RATIO; // 1320

    long long enc1_counts, enc2_counts;
    float enc1_revs, enc2_revs;

    cout << "========== TÍNH SỐ VÒNG QUAY TỪ ENCODER COUNTS ==========" << endl;
    cout << "Thông số encoder:" << endl;
    cout << "- PPR (xung/vòng/kênh): " << ENCODER_PPR << endl;
    cout << "- Quadrature factor: x" << QUAD_FACTOR << endl;
    cout << "- Gear ratio: " << GEAR_RATIO << endl;
    cout << "- Ticks per revolution: " << TICKS_PER_REV << endl;
    cout << endl;

    cout << "Nhập encoder counts (có thể copy từ read_encoder.py):" << endl;
    cout << "Encoder 1 counts: ";
    cin >> enc1_counts;
    cout << "Encoder 2 counts: ";
    cin >> enc2_counts;

    // Tính số vòng quay
    enc1_revs = enc1_counts / TICKS_PER_REV;
    enc2_revs = enc2_counts / TICKS_PER_REV;

    cout << "\n" << string(60, '=') << endl;
    cout << "KẾT QUẢ TÍNH TOÁN:" << endl;
    cout << fixed << setprecision(3);
    cout << "Encoder 1: " << enc1_counts << " counts = " << enc1_revs << " vòng" << endl;
    cout << "Encoder 2: " << enc2_counts << " counts = " << enc2_revs << " vòng" << endl;

    // Tính khoảng cách di chuyển (nếu cần)
    const float WHEEL_DIAMETER_M = 0.10f; // 10cm
    const float WHEEL_CIRC_M = 3.1415926f * WHEEL_DIAMETER_M;

    float distance1 = enc1_revs * WHEEL_CIRC_M;
    float distance2 = enc2_revs * WHEEL_CIRC_M;

    cout << "\nKhoảng cách di chuyển (ước tính):" << endl;
    cout << "Bánh 1: " << distance1 << " mét" << endl;
    cout << "Bánh 2: " << distance2 << " mét" << endl;
    cout << string(60, '=') << endl;

    return 0;
}