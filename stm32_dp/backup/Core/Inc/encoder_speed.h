/*
 * encoder_speed.h
 *
 *  Created on: Dec 2, 2025
 *      Author: khoi2
 */

#ifndef INC_ENCODER_SPEED_H_
#define INC_ENCODER_SPEED_H_

#include <stdint.h>
#include "encoder.h"

void EncoderSpeed_Init(void);

// return distance in meters since reset
float Encoder_GetPosition_m(EncoderId id);

// return wheel speed in meters per second
// dt = time elapsed since last call (seconds)
// the implementation applies a simple low-pass filter to reduce noise.
float Encoder_GetSpeed_mps(EncoderId id, float dt);

#endif /* INC_ENCODER_SPEED_H_ */
