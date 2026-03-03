#!/usr/bin/env python3
"""
MPU6050 3D Visualizer for STM32F407 Robot
Displays a 3D model based on Pitch (and optional Roll/Yaw) angles from MPU6050.

Usage:
    python mpu_3d_visualizer.py
    
Then input angles when prompted:
    - Pitch (degrees): rotation around Y axis
    - Roll (degrees): rotation around X axis  
    - Yaw (degrees): rotation around Z axis
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import TextBox
import sys

class Robot3DVisualizer:
    def __init__(self):
        self.pitch = 0.0
        self.roll = 0.0
        self.yaw = 0.0
        
        # Create figure and 3D axis
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Add text boxes for input
        self.fig.subplots_adjust(bottom=0.35)
        
        # Pitch input
        ax_pitch = self.fig.add_axes([0.2, 0.25, 0.3, 0.03])
        self.text_pitch = TextBox(ax_pitch, 'Pitch (°):', initial='0.0')
        self.text_pitch.on_submit(self.on_pitch_change)
        
        # Roll input
        ax_roll = self.fig.add_axes([0.2, 0.20, 0.3, 0.03])
        self.text_roll = TextBox(ax_roll, 'Roll (°):', initial='0.0')
        self.text_roll.on_submit(self.on_roll_change)
        
        # Yaw input
        ax_yaw = self.fig.add_axes([0.2, 0.15, 0.3, 0.03])
        self.text_yaw = TextBox(ax_yaw, 'Yaw (°):', initial='0.0')
        self.text_yaw.on_submit(self.on_yaw_change)
        
        # Info text
        self.fig.text(0.1, 0.05, 
                     'Enter angle values and press Enter to update 3D model.\n'
                     'Perfect horizontal = Pitch=0, Roll=0, Yaw=0',
                     fontsize=10, style='italic')
        
        self.draw_robot()
    
    def on_pitch_change(self, text):
        try:
            self.pitch = float(text)
            self.draw_robot()
        except ValueError:
            pass
    
    def on_roll_change(self, text):
        try:
            self.roll = float(text)
            self.draw_robot()
        except ValueError:
            pass
    
    def on_yaw_change(self, text):
        try:
            self.yaw = float(text)
            self.draw_robot()
        except ValueError:
            pass
    
    def euler_to_rotation_matrix(self, pitch, roll, yaw):
        """Convert Euler angles (in degrees) to rotation matrix (ZYX convention)"""
        pitch_rad = np.radians(pitch)
        roll_rad = np.radians(roll)
        yaw_rad = np.radians(yaw)
        
        # Rotation around X axis (Roll)
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(roll_rad), -np.sin(roll_rad)],
            [0, np.sin(roll_rad), np.cos(roll_rad)]
        ])
        
        # Rotation around Y axis (Pitch)
        Ry = np.array([
            [np.cos(pitch_rad), 0, np.sin(pitch_rad)],
            [0, 1, 0],
            [-np.sin(pitch_rad), 0, np.cos(pitch_rad)]
        ])
        
        # Rotation around Z axis (Yaw)
        Rz = np.array([
            [np.cos(yaw_rad), -np.sin(yaw_rad), 0],
            [np.sin(yaw_rad), np.cos(yaw_rad), 0],
            [0, 0, 1]
        ])
        
        # Combined rotation: Z(Yaw) * Y(Pitch) * X(Roll)
        R = Rz @ Ry @ Rx
        return R
    
    def draw_robot(self):
        self.ax.clear()
        
        # Get rotation matrix
        R = self.euler_to_rotation_matrix(self.pitch, self.roll, self.yaw)
        
        # Define robot body as a box (simple representation)
        # Box from (-0.1, -0.05, -0.15) to (0.1, 0.05, 0.15) in local coords
        vertices_local = np.array([
            [-0.1, -0.05, -0.15],  # 0
            [0.1, -0.05, -0.15],   # 1
            [0.1, 0.05, -0.15],    # 2
            [-0.1, 0.05, -0.15],   # 3
            [-0.1, -0.05, 0.15],   # 4
            [0.1, -0.05, 0.15],    # 5
            [0.1, 0.05, 0.15],     # 6
            [-0.1, 0.05, 0.15],    # 7
        ])
        
        # Apply rotation
        vertices_rotated = vertices_local @ R.T
        
        # Draw box edges
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # front face
            [4, 5], [5, 6], [6, 7], [7, 4],  # back face
            [0, 4], [1, 5], [2, 6], [3, 7],  # connecting edges
        ]
        
        for edge in edges:
            points = vertices_rotated[edge]
            self.ax.plot3D(*points.T, 'b-', linewidth=2)
        
        # Draw coordinate axes at origin (for reference)
        self.ax.quiver(0, 0, 0, 0.2, 0, 0, color='r', label='X-axis', arrow_length_ratio=0.2)
        self.ax.quiver(0, 0, 0, 0, 0.2, 0, color='g', label='Y-axis', arrow_length_ratio=0.2)
        self.ax.quiver(0, 0, 0, 0, 0, 0.2, color='b', label='Z-axis', arrow_length_ratio=0.2)
        
        # Draw robot axes (rotated)
        scale = 0.15
        x_axis = np.array([1, 0, 0]) @ R.T
        y_axis = np.array([0, 1, 0]) @ R.T
        z_axis = np.array([0, 0, 1]) @ R.T
        
        self.ax.quiver(0, 0, 0, scale*x_axis[0], scale*x_axis[1], scale*x_axis[2], 
                      color='red', arrow_length_ratio=0.3, linewidth=2, alpha=0.7)
        self.ax.quiver(0, 0, 0, scale*y_axis[0], scale*y_axis[1], scale*y_axis[2], 
                      color='green', arrow_length_ratio=0.3, linewidth=2, alpha=0.7)
        self.ax.quiver(0, 0, 0, scale*z_axis[0], scale*z_axis[1], scale*z_axis[2], 
                      color='blue', arrow_length_ratio=0.3, linewidth=2, alpha=0.7)
        
        # Set labels and title
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title(f'Robot 3D Orientation\nPitch={self.pitch:.1f}°, Roll={self.roll:.1f}°, Yaw={self.yaw:.1f}°',
                         fontsize=12, fontweight='bold')
        
        # Set equal aspect ratio and limits
        self.ax.set_xlim([-0.3, 0.3])
        self.ax.set_ylim([-0.3, 0.3])
        self.ax.set_zlim([-0.3, 0.3])
        
        # Add grid
        self.ax.grid(True, alpha=0.3)
        
        plt.draw()
    
    def run(self):
        """Display the visualizer"""
        print("=" * 60)
        print("MPU6050 3D Robot Orientation Visualizer")
        print("=" * 60)
        print("\nInstructions:")
        print("  1. Enter Pitch angle (degrees): forward/backward tilt")
        print("  2. Enter Roll angle (degrees): left/right tilt")
        print("  3. Enter Yaw angle (degrees): rotation around vertical axis")
        print("\nExample values:")
        print("  - Pitch = 0°: Robot level (horizontal)")
        print("  - Pitch = 30°: Robot tilted forward 30°")
        print("  - Roll = 15°: Robot tilted right 15°")
        print("\n" + "=" * 60 + "\n")
        
        plt.show()


def main():
    """Main function"""
    visualizer = Robot3DVisualizer()
    visualizer.run()


if __name__ == '__main__':
    main()
