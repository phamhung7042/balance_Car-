#ifndef INC_LQR_H_
#define INC_LQR_H_

#include <stdint.h>

/**
 * Simple LQR controller structure.  The control signal is
 * u = -(k1*theta + k2*theta_dot + k3*x + k4*x_dot)
 * and is saturated between out_min and out_max.
 */
typedef struct {
    float k1, k2, k3, k4;   /* gains */
    float out_min, out_max; /* saturation limits */
} LQR_t;

void LQR_Init(LQR_t *lqr, float k1, float k2, float k3, float k4);
void LQR_SetLimits(LQR_t *lqr, float min, float max);
float LQR_Compute(LQR_t *lqr, float theta, float theta_dot, float x, float x_dot);

/*
 * Convenience wrapper that takes raw sensor/encoder quantities and
 * computes the PWM command in one shot.  Angles are converted to radians
 * and wheel data averaged internally.
 */
float LQR_FromMeasurements(LQR_t *lqr,
                           const MPU6050_t *mpu, /* requires mpu6050.h included by caller */
                           float posL_m, float posR_m,
                           float speedL_mps, float speedR_mps);

#endif /* INC_LQR_H_ */
