#ifndef INC_MPU6050_H_
#define INC_MPU6050_H_

#include "main.h"
#include "i2c.h"

#define MPU6050_ADDR         0xD0
#define RAD_TO_DEG           57.29578f
#define DT                   0.02f

/* MPU6050 Register Addresses */
#define MPU6050_PWR_MGMT_1   0x6B
#define MPU6050_GYRO_CONFIG  0x1B
#define MPU6050_ACCEL_CONFIG 0x1C
#define MPU6050_ACCEL_XOUT_H 0x3B

typedef struct {
    I2C_HandleTypeDef *hi2c;
    
    /* Raw sensor data */
    int16_t Accel_X_Raw, Accel_Y_Raw, Accel_Z_Raw;
    int16_t Gyro_X_Raw, Gyro_Y_Raw, Gyro_Z_Raw;
    int16_t Temperature_Raw;
    
    /* Converted to physical units */
    float Ax, Ay, Az;              /* acceleration in g */
    float Gx, Gy, Gz;              /* gyro rate in deg/s */
    float Temperature;
    
    /* Calibration offsets */
    float Pitch_Offset;        /* accel-derived offset, updated by calibration and auto-correction */
    float Gyro_X_Offset, Gyro_Y_Offset, Gyro_Z_Offset;
    
    /* Filtered pitch angle (complementary filter output) */
    float Pitch;
    
    /* Full-scale settings */
    uint8_t FS_GYRO;               /* 0:250dps, 1:500dps, 2:1000dps, 3:2000dps */
    uint8_t FS_ACCEL;              /* 0:2g, 1:4g, 2:8g, 3:16g */
    
    float LSB_Sensitivity_GYRO;
    float LSB_Sensitivity_ACCEL;
} MPU6050_t;

void MPU_Init(MPU6050_t *mpu, I2C_HandleTypeDef *hi2c);
void MPU_Calibrate(MPU6050_t *mpu); 
void MPU_Read_And_Filter(MPU6050_t *mpu);
void MPU_Read_Raw_Data(MPU6050_t *mpu);
void MPU_Convert_Data(MPU6050_t *mpu);

#endif