#include "mpu6050.h"
#include <math.h>

void MPU_Init(MPU6050_t *mpu, I2C_HandleTypeDef *hi2c) {
    mpu->hi2c = hi2c;
    mpu->FS_GYRO = 0x0;    /* +-250 dps */
    mpu->FS_ACCEL = 0x0;   /* +-2g */
    
    /* Set LSB sensitivities based on full-scale */
    switch(mpu->FS_GYRO) {
        case 0: mpu->LSB_Sensitivity_GYRO = 131.0f; break;
        case 1: mpu->LSB_Sensitivity_GYRO = 65.5f; break;
        case 2: mpu->LSB_Sensitivity_GYRO = 32.8f; break;
        case 3: mpu->LSB_Sensitivity_GYRO = 16.4f; break;
    }
    switch(mpu->FS_ACCEL) {
        case 0: mpu->LSB_Sensitivity_ACCEL = 16384.0f; break;
        case 1: mpu->LSB_Sensitivity_ACCEL = 8192.0f; break;
        case 2: mpu->LSB_Sensitivity_ACCEL = 4096.0f; break;
        case 3: mpu->LSB_Sensitivity_ACCEL = 2048.0f; break;
    }
    
    /* Wake up MPU6050 */
    uint8_t data = 0x00;
    HAL_I2C_Mem_Write(mpu->hi2c, MPU6050_ADDR, MPU6050_PWR_MGMT_1, 1, &data, 1, 100);
    
    /* Configure gyro full-scale */
    uint8_t gyro_cfg = mpu->FS_GYRO << 3;
    HAL_I2C_Mem_Write(mpu->hi2c, MPU6050_ADDR, MPU6050_GYRO_CONFIG, 1, &gyro_cfg, 1, 100);
    
    /* Configure accel full-scale */
    uint8_t accel_cfg = mpu->FS_ACCEL << 3;
    HAL_I2C_Mem_Write(mpu->hi2c, MPU6050_ADDR, MPU6050_ACCEL_CONFIG, 1, &accel_cfg, 1, 100);
    
    /* Initialize offsets */
    mpu->Pitch_Offset = 0.0f;
    mpu->Gyro_X_Offset = 0.0f;
    mpu->Gyro_Y_Offset = 0.0f;
    mpu->Gyro_Z_Offset = 0.0f;
    mpu->Pitch = 0.0f;
    
    HAL_Delay(100);
}

void MPU_Calibrate(MPU6050_t *mpu) {
    float sum_pitch = 0.0f;
    float sum_gx = 0.0f, sum_gy = 0.0f, sum_gz = 0.0f;
    const int samples = 100;
    
    for (int i = 0; i < samples; ++i) {
        MPU_Read_Raw_Data(mpu);
        MPU_Convert_Data(mpu);
        
        /* Accel-based pitch from flat position */
        float pitch_acc = atan2f(-mpu->Ax, sqrtf(mpu->Ay*mpu->Ay + mpu->Az*mpu->Az)) * RAD_TO_DEG;
        sum_pitch += pitch_acc;
        
        /* Accumulate gyro readings for bias computation */
        sum_gx += mpu->Gx;
        sum_gy += mpu->Gy;
        sum_gz += mpu->Gz;
        
        HAL_Delay(5);
    }
    
    mpu->Pitch_Offset = sum_pitch / (float)samples;
    mpu->Gyro_X_Offset = sum_gx / (float)samples;
    mpu->Gyro_Y_Offset = sum_gy / (float)samples;
    mpu->Gyro_Z_Offset = sum_gz / (float)samples;
    mpu->Pitch = 0.0f;
}

void MPU_Read_Raw_Data(MPU6050_t *mpu) {
    uint8_t buf[14];
    if (HAL_I2C_Mem_Read(mpu->hi2c, MPU6050_ADDR, MPU6050_ACCEL_XOUT_H, 1, buf, 14, 20) == HAL_OK) {
        mpu->Accel_X_Raw = (int16_t)((buf[0] << 8) | buf[1]);
        mpu->Accel_Y_Raw = (int16_t)((buf[2] << 8) | buf[3]);
        mpu->Accel_Z_Raw = (int16_t)((buf[4] << 8) | buf[5]);
        mpu->Temperature_Raw = (int16_t)((buf[6] << 8) | buf[7]);
        mpu->Gyro_X_Raw = (int16_t)((buf[8] << 8) | buf[9]);
        mpu->Gyro_Y_Raw = (int16_t)((buf[10] << 8) | buf[11]);
        mpu->Gyro_Z_Raw = (int16_t)((buf[12] << 8) | buf[13]);
    }
}

void MPU_Convert_Data(MPU6050_t *mpu) {
    /* Convert accelerometer raw to g */
    mpu->Ax = (float)mpu->Accel_X_Raw / mpu->LSB_Sensitivity_ACCEL;
    mpu->Ay = (float)mpu->Accel_Y_Raw / mpu->LSB_Sensitivity_ACCEL;
    mpu->Az = (float)mpu->Accel_Z_Raw / mpu->LSB_Sensitivity_ACCEL;
    
    /* Convert gyro raw to deg/s and subtract bias */
    mpu->Gx = (float)mpu->Gyro_X_Raw / mpu->LSB_Sensitivity_GYRO - mpu->Gyro_X_Offset;
    mpu->Gy = (float)mpu->Gyro_Y_Raw / mpu->LSB_Sensitivity_GYRO - mpu->Gyro_Y_Offset;
    mpu->Gz = (float)mpu->Gyro_Z_Raw / mpu->LSB_Sensitivity_GYRO - mpu->Gyro_Z_Offset;
    
    /* Convert temperature */
    mpu->Temperature = (float)mpu->Temperature_Raw / 340.0f + 36.53f;
}

void MPU_Read_And_Filter(MPU6050_t *mpu) {
    MPU_Read_Raw_Data(mpu);
    MPU_Convert_Data(mpu);
    
    /* Compute pitch from accelerometer */
    float pitch_acc = atan2f(-mpu->Ax, sqrtf(mpu->Ay*mpu->Ay + mpu->Az*mpu->Az)) * RAD_TO_DEG;
    pitch_acc -= mpu->Pitch_Offset;
    
    /* Complementary filter: gyro integration + accel correction */
    const float alpha = 0.98f;
    mpu->Pitch = alpha * (mpu->Pitch + mpu->Gy * DT) + (1.0f - alpha) * pitch_acc;
}