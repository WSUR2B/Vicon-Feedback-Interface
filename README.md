# Vicon Data Interface

**A Real-Time Motion Capture Data Processing and Visualization System for Biomechanics Research**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Institution](https://img.shields.io/badge/Institution-Wayne%20State%20University-red.svg)](https://engineering.wayne.edu/)

---

## Overview

The **Vicon Data Interface** is a comprehensive software application designed to extend the capabilities of Vicon motion capture systems for biomechanics research and clinical applications. Built on top of Vicon's DataStream SDK, this interface provides real-time data acquisition, processing, visualization, and export capabilities for marker-based motion capture data and auxiliary devices (EMG, force plates, etc.).

### Key Capabilities

- **Real-Time Joint Angle Calculation**: Computes lower extremity joint angles using Plug-in Gait marker set
- **Multi-Device Integration**: Simultaneously monitors markers, EMG, force plates, and custom devices
- **Advanced Signal Processing**: Configurable filters (bandpass, moving average, moving median, Kalman)
- **UDP Network Streaming**: Broadcast data to external applications for integration with other systems
- **Visual Biofeedback**: Real-time feedback display for rehabilitation and training applications
- **Flexible Data Export**: Multiple recording modes with CSV output for post-processing

### Intended Applications

- Gait analysis and clinical biomechanics research
- Real-time biofeedback for rehabilitation
- Motion analysis for sports performance
- Integration with custom analysis pipelines
- Educational demonstrations of motion capture technology

---

## Table of Contents

- [Installation](#installation)
- [System Requirements](#system-requirements)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Usage](#usage)
- [Features](#features)
- [Calculated Angles](#calculated-angles)
- [Data Export Formats](#data-export-formats)
- [Troubleshooting](#troubleshooting)
- [Citation](#citation)
- [Authors](#authors)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Installation

### Prerequisites

1. **Python 3.8 or higher**
   ```bash
   python --version  # Verify Python installation
   ```

2. **Vicon DataStream SDK**
   - Download and install from [Vicon's website](https://www.vicon.com/software/datastream-sdk/)
   - Ensure the SDK is accessible to Python

### Install Dependencies

1. Clone or download this repository:
   ```bash
   git clone <repository-url>
   cd ViconDataStreamer
   ```

2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

   **Required packages:**
   - `PySide6` (Qt6 GUI framework)
   - `numpy` (Numerical computing)
   - `pandas` (Data management)
   - `scipy` (Signal processing)
   - `pyqtgraph` (Real-time plotting)
   - `vicon-dssdk` (Vicon DataStream SDK)
   - `PyOpenGL` (Hardware-accelerated graphics)

3. Configure Vicon connection:
   - Edit `main.py` (line ~1793)
   - Update the host IP address to match your Vicon system:
     ```python
     host = "YOUR_VICON_IP:801"  # e.g., "192.168.1.100:801"
     ```

---

## System Requirements

### Hardware
- **Minimum:**
  - CPU: Intel Core i5 or equivalent
  - RAM: 8 GB
  - Network: Gigabit Ethernet
  - GPU: OpenGL 2.0 compatible

- **Recommended:**
  - CPU: Intel Core i7 or better
  - RAM: 16 GB
  - Network: Gigabit Ethernet with dedicated NIC for Vicon
  - GPU: OpenGL 3.0+ with hardware acceleration

### Software
- **Operating System:** Windows 10/11, Linux (Ubuntu 20.04+), macOS 10.15+
- **Python:** 3.8, 3.9, 3.10, or 3.11
- **Vicon Nexus:** 2.12 or higher (running on Vicon PC)

### Network Configuration
- Both the Vicon PC and the application PC must be on the same network
- Firewall must allow communication on port 801 (default Vicon DataStream port)
- Recommended: Dedicated network interface for motion capture data

---

## Project Structure

```
ViconDataStreamer/
├── main.py                      # Main application entry point
├── Filters.py                   # Signal filtering implementations
├── feedbackTest.py              # Feedback system testing utilities
├── requirements.txt             # Python dependencies
├── README.md                    # This file
│
├── GUI/                         # Graphical user interface modules
│   ├── MainWindow_ui.py         # Main window UI (auto-generated)
│   ├── MainWindow.ui            # Qt Designer main window definition
│   ├── FeedbackWindow_ui.py    # Feedback window UI (auto-generated)
│   ├── FeedbackWindow.ui       # Qt Designer feedback window definition
│   ├── FeedbackGraph.py        # Biofeedback visualization widget
│   └── MyOpenGLCharting.py     # OpenGL-accelerated plotting
│
├── Kinematics/                  # Joint angle calculation modules
│   ├── Calculation.py           # Geometric calculation functions
│   └── MarkerKinematics.py     # Plug-in Gait kinematics implementation
│
├── ViconWrapper/                # Vicon DataStream SDK wrapper
│   ├── ViconWrapper.py         # Main Vicon interface class
│   ├── Subject.py              # Subject data representation
│   ├── Segment.py              # Body segment representation
│   └── Forceplate.py           # Force plate interface (experimental)
│
└── OtherFiles/                  # Documentation and media
    └── Capture*.PNG            # Application screenshots
```

---

## Configuration

### Before Launching the Application

#### 1. Vicon System Setup

1. **Launch Vicon Nexus** on the Vicon PC
2. **Create and calibrate a subject** in Nexus
3. **Label all markers** according to the Plug-in Gait marker set:
   - Pelvis: `LASI`, `RASI`, `LPSI`, `RPSI`
   - Lower extremity: `LKNE`, `RKNE`, `LANK`, `RANK`
   - Foot: `LHEE`, `RHEE`, `LTOE`, `RTOE`
4. **Start live mode** in Nexus
5. **Enable DataStream** (Tools → Enable DataStream SDK)

#### 2. Network Configuration

1. Ensure both PCs are on the same network
2. Note the Vicon PC's IP address (visible in Nexus system settings)
3. Configure firewall to allow traffic on port 801
4. Test connectivity using `ping <vicon-ip>`

#### 3. Application Configuration

Edit the configuration in `main.py`:

```python
# Vicon system IP address and port
host = "192.168.1.100:801"  # Update with your Vicon IP

# Subject anthropometric measurements (in millimeters)
vicon.subjectLLegMM = 800   # Left leg length
vicon.subjectRLegMM = 800   # Right leg length
vicon.subjectMarkerRMM = 7  # Marker radius
```

### Optimizing Performance

- **Select only required data streams** to minimize processing overhead
- **Disable unused devices** in the device selection tree
- **Adjust plot window size** based on your monitor refresh rate
- **Use appropriate filter window sizes** (larger = more smoothing, more delay)

---

## Usage

### Quick Start

1. **Launch the application:**
   ```bash
   python main.py
   ```

2. **Wait for connection:** The application will automatically connect to the Vicon system and display "Connected" in the status bar.

3. **Select data streams:**
   - Navigate to the **Device Selection** tab
   - Double-click devices/channels to enable/disable them
   - Navigate to the **Angle Selection** tab
   - Double-click angles to enable/disable calculation

4. **Visualize data:**
   - Go to the **Plotting** tab
   - Select angles from dropdown menus
   - Choose left/right side
   - Select device data if desired
   - Adjust Y-axis range using sliders

5. **Record data:**
   - Go to the **Exporting** tab
   - Choose recording mode (Manual/Duration/Window)
   - Set file path and name
   - Click "Start Recording" or "Record Duration"

### Advanced Features

#### Real-Time Filtering

1. Navigate to **Angle Selection** → **Filters**
2. Select filter type:
   - **None**: No filtering (lowest latency)
   - **Bandpass**: Remove specific frequency ranges
   - **Moving Average**: Smooth high-frequency noise
   - **Moving Median**: Remove spikes and outliers
3. Configure filter parameters
4. Filter is applied immediately to all calculations

#### UDP Streaming

1. Go to **Streaming** tab
2. Enter target IP address and port
3. Configure packet format:
   - **Packet Size**: Total packet length (bytes)
   - **Value Size**: Space allocated for numerical value
4. Select data to stream from the table
5. Click "Start Stream"

**Packet Format:**
```
[Label (variable) | Padding (spaces) | Value (fixed) | '$']
Example: "LHip          45.67     $"
```

#### Visual Biofeedback

1. Open the **Feedback** window (separate window)
2. In main window, go to **Feedback** tab
3. Select one angle or device measurement
4. Configure feedback ranges:
   - **Total Range**: Full display range
   - **Target Region**: Desired performance zone
5. Monitor in real-time on feedback window

---

## Features

### Data Acquisition

- **Marker Tracking**: Real-time 3D positions of all labeled markers
- **Device Integration**: EMG, force plates, accelerometers, custom analog devices
- **Multi-Rate Sampling**: Handles devices with different sampling rates
- **Frame Synchronization**: Automatic synchronization of all data sources

### Joint Angle Calculation

- **Real-Time Computation**: Joint angles calculated each frame (~100 Hz)
- **Plug-in Gait Model**: Industry-standard biomechanical model
- **Bilateral Analysis**: Simultaneous left and right side calculations
- **Zero Calibration**: Set reference position for relative measurements

### Signal Processing

- **Bandpass Filter**: FIR filter with configurable cutoff frequencies
- **Moving Average**: Simple temporal averaging (configurable window)
- **Moving Median**: Robust outlier rejection (configurable window)
- **Kalman Filter**: State estimation for prediction (experimental)

### Visualization

- **OpenGL Acceleration**: Hardware-accelerated real-time plotting
- **Multi-Series Display**: Up to 2 angles + 1 device simultaneously
- **Configurable Axes**: Custom or auto-scaling ranges
- **High Performance**: Maintains 60+ FPS with 1000-frame windows

### Data Export

Three recording modes:

1. **Manual Mode**: User-controlled start/stop
2. **Duration Mode**: Automatically record for specified time
3. **Window Mode**: Save current plot window contents

**Export Formats:**
- CSV files with timestamps
- Separate files for angles and each device
- Configurable filename and auto-incrementing

### UDP Streaming

- **Low Latency**: Real-time data broadcast over network
- **Custom Packet Format**: Configurable size and structure
- **Multi-Client**: Broadcast to multiple applications
- **Selective Streaming**: Choose which data to transmit

---

## Calculated Angles

### Sagittal Plane (Flexion/Extension)

| Angle | Description | Positive Direction |
|-------|-------------|-------------------|
| **Hip** | Hip flexion/extension | Flexion (forward) |
| **Knee** | Knee flexion/extension | Flexion |
| **Ankle** | Ankle dorsi/plantarflexion | Dorsiflexion |

### Frontal Plane (Abduction/Adduction)

| Angle | Description | Positive Direction |
|-------|-------------|-------------------|
| **Hip Adduction** | Hip ad/abduction | Adduction (toward midline) |

### Transverse Plane (Rotation)

| Angle | Description | Positive Direction |
|-------|-------------|-------------------|
| **Hip Inversion** | Hip internal/external rotation | Internal rotation |
| **Subtalar** | Foot inversion/eversion | Eversion |

### Calculation Methods

- **Hip Joint Centers**: Calculated using regression equations based on pelvic dimensions
- **Reference Frame**: Pelvis coordinate system (right-anterior-superior)
- **Angle Convention**: Right-hand rule, anatomical zero position
- **Range**: -180° to +180° (full rotation capability)

---

## Data Export Formats

### Angle Data (`*_angles.csv`)

```csv
Frame,LHip,RHip,LKnee,RKnee,LAnkle,RAnkle,LHipAdduction,RHipAdduction,...
0,12.34,15.67,45.23,43.12,8.90,7.65,5.43,4.32,...
1,13.45,16.78,46.34,44.23,9.01,8.76,5.54,4.43,...
...
```

### Device Data (`*_<device>_<channel>.csv`)

**Standard Mode** (last sample per frame):
```csv
Frame,X,Y,Z
0,123.45,234.56,345.67
1,124.56,235.67,346.78
...
```

**All Data Mode** (all samples per frame):
```csv
Frame,X,Y,Z
0.0,123.45,234.56,345.67
0.1,123.50,234.60,345.70
0.2,123.55,234.65,345.75
...
1.0,124.56,235.67,346.78
...
```

---

## Troubleshooting

### Connection Issues

**Problem:** "Cannot connect to Vicon system"

**Solutions:**
- Verify Vicon Nexus is running and in live mode
- Check IP address in `main.py` matches Vicon PC
- Ensure DataStream SDK is enabled in Nexus
- Test network connectivity: `ping <vicon-ip>`
- Check firewall settings (port 801)

### Performance Issues

**Problem:** Low FPS or lag in visualization

**Solutions:**
- Disable unused devices and angles
- Reduce plot window size (frames displayed)
- Close other applications
- Update graphics drivers
- Use a dedicated network interface for Vicon

### Missing Data

**Problem:** Markers or angles showing as zero

**Solutions:**
- Verify markers are labeled in Nexus
- Check marker names match expected names (case-sensitive)
- Ensure subject is in Nexus capture volume
- Verify markers are visible to cameras
- Check marker occlusion in Nexus

### Filter Artifacts

**Problem:** Angles look noisy or have strange behavior

**Solutions:**
- Increase filter window size for more smoothing
- Use moving median filter for spike removal
- Adjust bandpass cutoff frequencies
- Consider marker placement quality
- Check for marker swapping in Nexus

### Export Issues

**Problem:** Cannot save files or files are empty

**Solutions:**
- Verify save path exists and is writable
- Check disk space
- Ensure recording was started before data collection
- Verify selected angles/devices are active
- Close files if already open in another program

---

## Citation

If you use this software in your research, please cite:

```bibtex
@software{grubich2024vicon,
  author = {Grubich, Daniil},
  title = {Vicon Data Interface: Real-Time Motion Capture Data Processing System},
  year = {2024},
  institution = {Wayne State University, R2B Lab},
  url = {https://github.com/your-repository}
}
```

**For publications:**

Grubich, D. (2024). *Vicon Data Interface: Real-Time Motion Capture Data Processing System*. Wayne State University, Robotics and Biomechanics Lab.

---

## Authors

**Daniil Grubich**
- Institution: Wayne State University
- Laboratory: Robotics and Biomechanics (R2B) Lab
- Email: daniil.grubich@wayne.edu

**Principal Investigator:**
- Dr. [PI Name]
- Wayne State University, Department of [Department]

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Daniil Grubich, Wayne State University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## Acknowledgments

- **Vicon Motion Systems** for the DataStream SDK and technical support
- **Wayne State University** College of Engineering for facilities and resources
- **R2B Lab** members for testing and feedback
- **Open-source community** for the excellent Python libraries used in this project

### Funding

This work was supported by [Funding Source/Grant Number].

---

## Contributing

We welcome contributions! If you'd like to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add YourFeature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include unit tests for new features
- Update documentation as needed

---

## Support

For questions, issues, or suggestions:

- **Email:** daniil.grubich@wayne.edu
- **Issues:** Open an issue on the GitHub repository
- **Documentation:** See `OtherFiles/` folder for additional guides

---

## Version History

### Version 1.0.0 (2024)
- Initial release
- Real-time marker tracking and joint angle calculation
- UDP streaming capability
- Data export in multiple modes
- Visual biofeedback system
- Configurable signal filtering

---

**Last Updated:** February 2026

