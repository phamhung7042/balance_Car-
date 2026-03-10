#!/usr/bin/env python3
"""Read encoder counters, calculate revolutions, and monitor PWM over SWD using pyOCD

Features:
- Text mode: Real-time console output
- Graph mode: Oscilloscope-like display with matplotlib

Requires:
    pip install pyocd pyelftools matplotlib numpy

Usage:
    python read_encoder_revolutions.py /path/to/your_project.elf [--graph]

Options:
    --graph    Enable oscilloscope-like graphical display
    --help     Show this help

This script extends read_encoder.py to also calculate revolutions based on:
- PPR: 11 pulses per revolution per channel
- Quadrature: x4
- Gear ratio: 30:1
- Total: 1320 ticks per revolution

Additionally monitors PWM values for motor control debugging.

Connect an ST-Link/v2 or CMSIS-DAP probe to the board and run the script.
"""

import sys
import time
import argparse
from pyocd.core.helpers import ConnectHelper
from elftools.elf.elffile import ELFFile

import os

# Optional imports for graph mode
try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.gridspec import GridSpec
    import numpy as np
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False

# Encoder specifications from robot_params.h
ENCODER_PPR = 11        # pulses per revolution per channel
QUAD_FACTOR = 4         # quadrature encoding x4
GEAR_RATIO = 30.0       # gear ratio
TICKS_PER_REV = ENCODER_PPR * QUAD_FACTOR * GEAR_RATIO  # 1320 ticks/rev

WHEEL_DIAMETER_M = 0.10  # 10cm wheel
WHEEL_CIRC_M = 3.1415926 * WHEEL_DIAMETER_M

# PWM specifications (assuming 0-1000 range for STM32 TIM PWM)
PWM_MAX = 1000
PWM_MIN = -1000  # for bidirectional PWM

# Parse command line arguments
parser = argparse.ArgumentParser(description='Read encoder data and PWM from STM32 over SWD')
parser.add_argument('elf_path', help='Path to the ELF file')
parser.add_argument('--graph', action='store_true', help='Enable graphical oscilloscope display')
parser.add_argument('--samples', type=int, default=200, help='Number of samples to show in graph (default: 200)')
args = parser.parse_args()

elf_path = args.elf_path
graph_mode = args.graph
max_samples = args.samples

if graph_mode and not GRAPH_AVAILABLE:
    print("Error: matplotlib and numpy required for graph mode. Install with:")
    print("pip install matplotlib numpy")
    sys.exit(1)

if not os.path.isfile(elf_path):
    print(f"Error: ELF file not found: {elf_path}")
    # try to help by listing .elf files in current directory
    candidates = [f for f in os.listdir('.') if f.lower().endswith('.elf')]
    if candidates:
        print("Found the following ELF files in this directory:")
        for c in candidates:
            print('  ', c)
    sys.exit(1)

# open elf and locate symbols
with open(elf_path, 'rb') as f:
    elf = ELFFile(f)
    symtab = elf.get_section_by_name('.symtab')
    if symtab is None:
        raise RuntimeError('ELF has no symbol table')
    def find_addr(name):
        sym = symtab.get_symbol_by_name(name)
        if not sym:
            raise KeyError(f'symbol {name} not found in ELF')
        return sym[0]['st_value']

    addr_enc1 = find_addr('Debug_Enc1_Count')
    addr_enc2 = find_addr('Debug_Enc2_Count')
    
    # Try to find PWM variables (may not exist in all firmware versions)
    pwm_vars = []
    pwm_names = ['Test_Speed_PWM', 'PWM_Motor1', 'PWM_Motor2', 'Motor1_PWM', 'Motor2_PWM']
    for pwm_name in pwm_names:
        try:
            addr = find_addr(pwm_name)
            pwm_vars.append((pwm_name, addr))
            print(f'Found PWM variable: {pwm_name} at 0x{addr:08X}')
        except KeyError:
            continue
    
    if not pwm_vars:
        print('Warning: No PWM variables found. PWM monitoring disabled.')
        pwm_vars = None

# Oscilloscope display class
class OscilloscopeDisplay:
    def __init__(self, max_samples=200, pwm_vars=None):
        self.max_samples = max_samples
        self.pwm_vars = pwm_vars
        
        # Data buffers
        self.time_data = []
        self.enc1_data = []
        self.enc2_data = []
        self.rev1_data = []
        self.rev2_data = []
        self.pulse_rate1_data = []
        self.pulse_rate2_data = []
        self.pwm_data = {}  # dict of pwm_name -> list of values
        
        # Previous values for rate calculation
        self.prev_v1 = 0
        self.prev_v2 = 0
        
        # Initialize PWM data buffers
        if self.pwm_vars:
            for name, _ in self.pwm_vars:
                self.pwm_data[name] = []
        
        # Setup the figure
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(14, 10))
        self.fig.suptitle('STM32 Encoder & PWM Oscilloscope', fontsize=16, color='cyan')
        
        # Create subplots
        gs = GridSpec(4, 1, height_ratios=[2, 1, 1, 1], hspace=0.3)
        
        # Encoder counts subplot
        self.ax1 = self.fig.add_subplot(gs[0])
        self.line_enc1, = self.ax1.plot([], [], 'r-', linewidth=2, label='Encoder 1')
        self.line_enc2, = self.ax1.plot([], [], 'b-', linewidth=2, label='Encoder 2')
        self.ax1.set_ylabel('Encoder Counts', color='white')
        self.ax1.legend(loc='upper left')
        self.ax1.grid(True, alpha=0.3)
        
        # Pulse rate subplot
        self.ax2 = self.fig.add_subplot(gs[1])
        self.line_rate1, = self.ax2.plot([], [], 'r--', linewidth=1.5, label='Pulse Rate 1')
        self.line_rate2, = self.ax2.plot([], [], 'b--', linewidth=1.5, label='Pulse Rate 2')
        self.ax2.set_ylabel('Pulse Rate (pulses/s)', color='white')
        self.ax2.legend(loc='upper left')
        self.ax2.grid(True, alpha=0.3)
        
        # Revolutions subplot
        self.ax3 = self.fig.add_subplot(gs[2])
        self.line_rev1, = self.ax3.plot([], [], 'r--', linewidth=1.5, label='Rev 1')
        self.line_rev2, = self.ax3.plot([], [], 'b--', linewidth=1.5, label='Rev 2')
        self.ax3.set_ylabel('Revolutions', color='white')
        self.ax3.legend(loc='upper left')
        self.ax3.grid(True, alpha=0.3)
        
        # PWM subplot
        self.ax4 = self.fig.add_subplot(gs[3])
        self.pwm_lines = {}
        colors = ['yellow', 'green', 'magenta', 'cyan', 'orange']
        for i, (name, _) in enumerate(self.pwm_vars or []):
            color = colors[i % len(colors)]
            self.pwm_lines[name], = self.ax4.plot([], [], color=color, linewidth=2, label=name)
        self.ax4.set_ylabel('PWM Value', color='white')
        self.ax4.set_xlabel('Time (samples)', color='white')
        self.ax4.legend(loc='upper left')
        self.ax4.grid(True, alpha=0.3)
        
        # Set background colors
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.set_facecolor('#1a1a1a')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('white')
        
        plt.tight_layout()
    
    def update_data(self, enc1, enc2, rev1, rev2, pulse_rate1, pulse_rate2, pwm_values):
        """Update data buffers with new readings"""
        current_time = len(self.time_data)
        self.time_data.append(current_time)
        self.enc1_data.append(enc1)
        self.enc2_data.append(enc2)
        self.rev1_data.append(rev1)
        self.rev2_data.append(rev2)
        self.pulse_rate1_data.append(pulse_rate1)
        self.pulse_rate2_data.append(pulse_rate2)
        
        # Update PWM data
        if self.pwm_vars and pwm_values:
            for name, value in pwm_values.items():
                if name in self.pwm_data:
                    self.pwm_data[name].append(value)
        
        # Keep only recent data
        if len(self.time_data) > self.max_samples:
            self.time_data.pop(0)
            self.enc1_data.pop(0)
            self.enc2_data.pop(0)
            self.rev1_data.pop(0)
            self.rev2_data.pop(0)
            self.pulse_rate1_data.pop(0)
            self.pulse_rate2_data.pop(0)
            for name in self.pwm_data:
                if self.pwm_data[name]:
                    self.pwm_data[name].pop(0)
    
    def update_plot(self, frame):
        """Update the plot for animation"""
        if not self.time_data:
            return []
        
        # Update encoder plot
        self.line_enc1.set_data(self.time_data, self.enc1_data)
        self.line_enc2.set_data(self.time_data, self.enc2_data)
        self.ax1.set_xlim(max(0, self.time_data[0]), max(self.max_samples, self.time_data[-1]))
        self.ax1.set_ylim(min(self.enc1_data + self.enc2_data) - 100, 
                         max(self.enc1_data + self.enc2_data) + 100)
        
        # Update pulse rate plot
        self.line_rate1.set_data(self.time_data, self.pulse_rate1_data)
        self.line_rate2.set_data(self.time_data, self.pulse_rate2_data)
        self.ax2.set_xlim(max(0, self.time_data[0]), max(self.max_samples, self.time_data[-1]))
        rate_min = min(self.pulse_rate1_data + self.pulse_rate2_data) - 10
        rate_max = max(self.pulse_rate1_data + self.pulse_rate2_data) + 10
        self.ax2.set_ylim(rate_min, rate_max)
        
        # Update revolutions plot
        self.line_rev1.set_data(self.time_data, self.rev1_data)
        self.line_rev2.set_data(self.time_data, self.rev2_data)
        self.ax3.set_xlim(max(0, self.time_data[0]), max(self.max_samples, self.time_data[-1]))
        rev_min = min(self.rev1_data + self.rev2_data) - 0.1
        rev_max = max(self.rev1_data + self.rev2_data) + 0.1
        self.ax3.set_ylim(rev_min, rev_max)
        
        # Update PWM plot
        if self.pwm_vars:
            pwm_min = float('inf')
            pwm_max = float('-inf')
            for name, line in self.pwm_lines.items():
                if name in self.pwm_data and self.pwm_data[name]:
                    line.set_data(self.time_data, self.pwm_data[name])
                    pwm_min = min(pwm_min, min(self.pwm_data[name]))
                    pwm_max = max(pwm_max, max(self.pwm_data[name]))
            
            if pwm_min != float('inf') and pwm_max != float('-inf'):
                self.ax4.set_xlim(max(0, self.time_data[0]), max(self.max_samples, self.time_data[-1]))
                self.ax4.set_ylim(pwm_min - 50, pwm_max + 50)
        
        return [self.line_enc1, self.line_enc2, self.line_rate1, self.line_rate2, self.line_rev1, self.line_rev2] + list(self.pwm_lines.values())

# connect to target
session = ConnectHelper.session_with_chosen_probe()
with session:
    target = session.target
    target.resume()          # let CPU run

    if graph_mode:
        print(f'Starting oscilloscope display with {max_samples} samples...')
        print('Close the graph window to stop monitoring')

        # Initialize oscilloscope
        scope = OscilloscopeDisplay(max_samples, pwm_vars)

        def animate(frame):
            # Read data
            v1 = target.read32(addr_enc1)
            v2 = target.read32(addr_enc2)

            # Calculate revolutions
            rev1 = v1 / TICKS_PER_REV
            rev2 = v2 / TICKS_PER_REV

            # Calculate pulse rates (pulses per second)
            dt = 0.1  # 100ms interval
            pulse_rate1 = (v1 - scope.prev_v1) / dt
            pulse_rate2 = (v2 - scope.prev_v2) / dt
            scope.prev_v1 = v1
            scope.prev_v2 = v2

            # Read PWM values
            pwm_values = {}
            if pwm_vars:
                for name, addr in pwm_vars:
                    try:
                        pwm_val = target.read32(addr)
                        pwm_values[name] = pwm_val
                    except:
                        pwm_values[name] = 0

            # Update scope data
            scope.update_data(v1, v2, rev1, rev2, pulse_rate1, pulse_rate2, pwm_values)

            return scope.update_plot(frame)

        # Start animation
        ani = animation.FuncAnimation(scope.fig, animate, interval=100, blit=True, cache_frame_data=False)
        plt.show()

    else:
        # Text mode (original behavior)
        print('Reading encoder data and PWM, press Ctrl-C to stop')
        print('Format: counts (revolutions) [distance_m] | PWM: value (duty%) [direction]')
        print('-' * 80)

        # Keep track of previous values for direction detection
        prev_v1 = prev_v2 = 0

        try:
            while True:
                v1 = target.read32(addr_enc1)
                v2 = target.read32(addr_enc2)

                # Calculate revolutions
                rev1 = v1 / TICKS_PER_REV
                rev2 = v2 / TICKS_PER_REV

                # Calculate distance (approximate)
                dist1 = rev1 * WHEEL_CIRC_M
                dist2 = rev2 * WHEEL_CIRC_M

                # Detect direction (simple: increasing = forward, decreasing = backward)
                dir1 = "→" if v1 > prev_v1 else "←" if v1 < prev_v1 else "■"
                dir2 = "→" if v2 > prev_v2 else "←" if v2 < prev_v2 else "■"

                # Read PWM values and calculate duty cycle
                pwm_info = ""
                if pwm_vars:
                    pwm_values = []
                    for name, addr in pwm_vars:
                        try:
                            pwm_val = target.read32(addr)
                            # Calculate duty cycle percentage
                            if pwm_val >= 0:
                                duty_pct = (pwm_val / PWM_MAX) * 100
                                pwm_values.append(f"{name}={pwm_val} ({duty_pct:5.1f}%)")
                            else:
                                duty_pct = (abs(pwm_val) / abs(PWM_MIN)) * 100
                                pwm_values.append(f"{name}={pwm_val} ({duty_pct:5.1f}%)")
                        except:
                            pwm_values.append(f"{name}=ERR")
                    pwm_info = f" | PWM: {' '.join(pwm_values)}"

                print(f'enc1={v1:8d} ({rev1:7.3f} rev) [{dist1:6.3f}m] {dir1}  '
                      f'enc2={v2:8d} ({rev2:7.3f} rev) [{dist2:6.3f}m] {dir2}{pwm_info}', end='\r')

                # Update previous values
                prev_v1, prev_v2 = v1, v2

                time.sleep(0.1)
        except KeyboardInterrupt:
            print('\nDone.')