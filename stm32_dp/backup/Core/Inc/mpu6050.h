#ifndef INC_MPU6050_H_
#define INC_MPU6050_H_

#include "main.h"

#define MPU6050_ADDR         0xD0
#define RAD_TO_DEG           57.296f
#define DT                   0.02f   

typedef struct {
    I2C_HandleTypeDef *hi2c;
    int16_t Accel_X_Raw, Accel_Y_Raw, Accel_Z_Raw;
    int16_t Gyro_Y_Raw;
    float Ax, Ay, Az;
    float Pitch;        
    float Pitch_Accel;  
    float Pitch_Offset; 
} MPU6050_t;

void MPU_Init(MPU6050_t *mpu, I2C_HandleTypeDef *hi2c);
void MPU_Calibrate(MPU6050_t *mpu); 
void MPU_Read_And_Filter(MPU6050_t *mpu);

#endif