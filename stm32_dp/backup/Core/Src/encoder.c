/*
 * encoder.c
 *
 *  Created on: Dec 2, 2025
 *      Author: khoi2
 */
#include "encoder.h"
#include "tim.h"

#define ENC1_SIGN   (-1)
#define ENC2_SIGN   (+1)

extern TIM_HandleTypeDef htim1;   // Encoder 1
extern TIM_HandleTypeDef htim3;   // Encoder 2

// ----- Biến mở rộng đếm encoder -----
static int16_t prev_raw_1 = 0;
static int16_t prev_raw_2 = 0;

static int32_t acc_count_1 = 0;
static int32_t acc_count_2 = 0;

// debug symbols exported for external monitoring (e.g., Python over SWD)
volatile int32_t Debug_Enc1_Count = 0;
volatile int32_t Debug_Enc2_Count = 0;

void Encoder_Init(void)
{
    HAL_TIM_Encoder_Start(&htim1, TIM_CHANNEL_ALL);
    HAL_TIM_Encoder_Start(&htim3, TIM_CHANNEL_ALL);

    __HAL_TIM_SET_COUNTER(&htim3, 0);
    __HAL_TIM_SET_COUNTER(&htim1, 0);

    prev_raw_1  = (int16_t)__HAL_TIM_GET_COUNTER(&htim3);
    prev_raw_2  = (int16_t)__HAL_TIM_GET_COUNTER(&htim1);

    acc_count_1 = 0;
    acc_count_2 = 0;
}

int32_t Encoder_GetCount(EncoderId id)
{
    TIM_HandleTypeDef *htim;
    int16_t *prev_raw;
    int32_t *acc;
    int8_t  sign;

    if (id == ENCODER_1) {
        htim     = &htim1;
        prev_raw = &prev_raw_1;
        acc      = &acc_count_1;
        sign     = ENC1_SIGN;
    } else {
        htim     = &htim3;
        prev_raw = &prev_raw_2;
        acc      = &acc_count_2;
        sign     = ENC2_SIGN;
    }

    int16_t now    = (int16_t)__HAL_TIM_GET_COUNTER(htim);
    int16_t diff16 = now - *prev_raw;   // đã xử lý overflow nhờ 2's complement

    *acc      += (int32_t)(sign * diff16);
    *prev_raw  = now;

    // update debug variables (mirror acc_count)
    if (id == ENCODER_1) {
        Debug_Enc1_Count = *acc;
    } else {
        Debug_Enc2_Count = *acc;
    }

    return *acc;
}

void Encoder_Reset(EncoderId id)
{
    if (id == ENCODER_1) {
        __HAL_TIM_SET_COUNTER(&htim1, 0);
        prev_raw_1  = 0;
        acc_count_1 = 0;
    } else {
        __HAL_TIM_SET_COUNTER(&htim3, 0);
        prev_raw_2  = 0;
        acc_count_2 = 0;
    }
}

