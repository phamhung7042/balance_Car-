/* USER CODE BEGIN Header */
/**
  * SYSTEM: STM32F407
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "i2c.h"
#include "tim.h"
#include "gpio.h"

// --- INCLUDE MODULES ---
#include "MPU6050_scale.h"
#include <math.h>
#include "motor.h"
#include "encoder.h"
#include "encoder_speed.h" 

/* Private variables ---------------------------------------------------------*/
// Use MPU6050_scale module's global `MPU6050`
// current pitch estimated by complementary filter
float Current_Pitch = 0.0f;

// --- BIẾN DEBUG ---
// 2. Tốc độ (m/s)
float Speed_L_mps = 0.0f;
float Speed_R_mps = 0.0f;

// 3. Quãng đường (m)
float Pos_L_m = 0.0f;
float Pos_R_m = 0.0f;

// 4. Test Motor 
int16_t Test_Speed_PWM = 500; 

uint32_t Timer_20ms = 0;
uint32_t Timer_1s = 0;

/* Function Prototypes */
void SystemClock_Config(void);

int main(void)
{
  HAL_Init();
  SystemClock_Config();
  MX_GPIO_Init();
  MX_I2C2_Init();
  MX_TIM1_Init(); 
  MX_TIM3_Init(); 
  MX_TIM9_Init(); 

  // --- 1. KHOI DONG MODULE ---
  Motor_Init();      
  Encoder_Init();       // Reset counter về 0
  EncoderSpeed_Init();  // Lấy mẫu đầu tiên
  
  // Khởi động MPU (MPU6050_scale)
  HAL_Delay(100);
  MPU6050_Initialization();

  // Simple calibration: average accel-derived pitch for offset
  {
    float sum = 0.0f;
    const int samples = 100;
    for (int i = 0; i < samples; ++i) {
      MPU6050_ProcessData(&MPU6050);
      float ax = MPU6050.acc_x;
      float ay = MPU6050.acc_y;
      float az = MPU6050.acc_z;
      float pitch_acc = atan2f(-ax, sqrtf(ay*ay + az*az)) * 57.29577951308232f;
      sum += pitch_acc;
      HAL_Delay(5);
    }
    float pitch_offset = sum / (float)samples;
    // store offset in MPU6050 struct for later use
    MPU6050.pitch_offset = pitch_offset;
    Current_Pitch = 0.0f; // start from zero
  }

  Timer_20ms = HAL_GetTick();

  while (1)
  {
    // ====================================================
    // LOOP 20ms (50Hz)
    // ====================================================
    if (HAL_GetTick() - Timer_20ms >= 20)
    {
        // 1. Đọc MPU6050 (MPU6050_scale)
        MPU6050_ProcessData(&MPU6050);
        // complementary filter: combine accel pitch and gyro integration
        float ax = MPU6050.acc_x;
        float ay = MPU6050.acc_y;
        float az = MPU6050.acc_z;
        float pitch_acc = atan2f(-ax, sqrtf(ay*ay + az*az)) * 57.29577951308232f;
        // subtract calibrated offset
        pitch_acc -= MPU6050.pitch_offset;
        float gyro_rate_y = MPU6050.gyro_y; // already in deg/s after DataConvert
        const float alpha = 0.98f;
        const float dt = 0.02f;
        Current_Pitch = alpha * (Current_Pitch + gyro_rate_y * dt) + (1.0f - alpha) * pitch_acc;

        // 2. Đọc Encoder (Gọi hàm từ encoder_speed.c)
        // dt = 0.02s (20ms)
        Speed_L_mps = Encoder_GetSpeed_mps(ENCODER_2, 0.02f); // Bánh Trái (TIM3)
        Speed_R_mps = Encoder_GetSpeed_mps(ENCODER_1, 0.02f); // Bánh Phải (TIM1)
        
        Pos_L_m = Encoder_GetPosition_m(ENCODER_2);
        Pos_R_m = Encoder_GetPosition_m(ENCODER_1);

        // 3. Test Motor (Chạy Open-Loop để check Encoder)
        // Nhập giá trị Test_Speed_PWM trong Live Expressions (ví dụ 300)
        // Nếu bánh quay mà Speed_mps vẫn = 0 -> Sai dây Encoder
        // Nếu bánh quay tiền mà Speed_mps bị âm -> Đổi chiều trong encoder.c
        Motor_SetSpeed(MOTOR_1, Test_Speed_PWM);
        Motor_SetSpeed(MOTOR_2, Test_Speed_PWM);

        Timer_20ms += 20; 
    }

    // ====================================================
    // LOOP 1s - LED
    // ====================================================
    if (HAL_GetTick() - Timer_1s >= 1000)
    {
        HAL_GPIO_TogglePin(GPIOD, GPIO_PIN_12); 
        Timer_1s = HAL_GetTick();
    }
  }
}

/**
  * @brief System Clock Configuration
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 8;
  RCC_OscInitStruct.PLL.PLLN = 168;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 7;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) Error_Handler();
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK|RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;
  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_5) != HAL_OK) Error_Handler();
}

void Error_Handler(void) { __disable_irq(); while (1) {} }
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
