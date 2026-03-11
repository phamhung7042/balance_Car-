#include "lqr.h"
#include "motor.h" // for MOTOR_SPEED_MAX

void LQR_Init(LQR_t *lqr, float k1, float k2, float k3, float k4)
{
    lqr->k1 = k1;
    lqr->k2 = k2;
    lqr->k3 = k3;
    lqr->k4 = k4;
    /* default limits match motor command range */
    lqr->out_max = MOTOR_SPEED_MAX;
    lqr->out_min = -MOTOR_SPEED_MAX;
}

void LQR_SetLimits(LQR_t *lqr, float min, float max)
{
    if (min < max) {
        lqr->out_min = min;
        lqr->out_max = max;
    }
}

float LQR_Compute(LQR_t *lqr, float theta, float theta_dot, float x, float x_dot)
{
    float u = -(lqr->k1 * theta +
                lqr->k2 * theta_dot +
                lqr->k3 * x +
                lqr->k4 * x_dot);
    if (u > lqr->out_max) u = lqr->out_max;
    if (u < lqr->out_min) u = lqr->out_min;
    return u;
}

/* wrapper that combines sensor measurements */
float LQR_FromMeasurements(LQR_t *lqr,
                           const MPU6050_t *mpu,
                           float posL_m, float posR_m,
                           float speedL_mps, float speedR_mps)
{
    // convert pitch to radians
    float theta = mpu->Pitch * 0.01745329252f;
    float theta_dot = mpu->Gx * 0.01745329252f;
    float x = 0.5f * (posL_m + posR_m);
    float x_dot = 0.5f * (speedL_mps + speedR_mps);
    return LQR_Compute(lqr, theta, theta_dot, x, x_dot);
}
