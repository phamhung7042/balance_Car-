#include "mpu6050.h"
#include <math.h>

void MPU_Init(MPU6050_t *mpu, I2C_HandleTypeDef *hi2c) {
    mpu->hi2c = hi2c;
    uint8_t data = 0;
    HAL_I2C_Mem_Write(mpu->hi2c, MPU6050_ADDR, 0x6B, 1, &data, 1, 100);
    mpu->Pitch = 0.0f;
    mpu->Pitch_Accel = 0.0f;
    mpu->Pitch_Offset = 0.0f;
}

void MPU_Calibrate(MPU6050_t *mpu) {
    float sum = 0;
    for(int i=0; i<100; i++) {
        MPU_Read_And_Filter(mpu);
        if(mpu->Ax != 0) {
             float temp = atan2(-mpu->Ax, sqrt(mpu->Ay*mpu->Ay + mpu->Az*mpu->Az)) * RAD_TO_DEG;
             sum += temp;
        }
        HAL_Delay(5);
    }
    mpu->Pitch_Offset = sum / 100.0f;
}

void MPU_Read_And_Filter(MPU6050_t *mpu) {
    uint8_t buf[14];
    if (HAL_I2C_Mem_Read(mpu->hi2c, MPU6050_ADDR, 0x3B, 1, buf, 14, 20) == HAL_OK) {
        mpu->Accel_X_Raw = (int16_t)((buf[0] << 8) | buf[1]);
        mpu->Accel_Y_Raw = (int16_t)((buf[2] << 8) | buf[3]);
        mpu->Accel_Z_Raw = (int16_t)((buf[4] << 8) | buf[5]);
        mpu->Gyro_Y_Raw  = (int16_t)((buf[10] << 8) | buf[11]); 

        mpu->Ax = (float)mpu->Accel_X_Raw / 16384.0f;
        mpu->Ay = (float)mpu->Accel_Y_Raw / 16384.0f;
        mpu->Az = (float)mpu->Accel_Z_Raw / 16384.0f;

        if (mpu->Ax != 0.0f || mpu->Ay != 0.0f || mpu->Az != 0.0f) {
            mpu->Pitch_Accel = atan2f(-mpu->Ax, sqrtf(mpu->Ay*mpu->Ay + mpu->Az*mpu->Az)) * RAD_TO_DEG;
        }

        float Gyro_Rate_Y = (float)mpu->Gyro_Y_Raw / 131.0f; // deg/s for FS = +-250dps
        mpu->Pitch = 0.98f * (mpu->Pitch + Gyro_Rate_Y * DT) + 0.02f * mpu->Pitch_Accel;
    }
}