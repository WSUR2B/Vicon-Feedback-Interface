# Vicon Data Interface 📊📡

Using Vicon’s DataStream SDK, we designed the **Vicon Data Interface** to capture real-time Vicon data and enhance the capabilities of the Vicon Capture system for biomechanics research. This interface collects data from Vicon markers, calculates joint angles, and monitors various devices like force plates and EMG systems directly from the Vicon System.

## Features ✨

- **Real-time Data Collection**: Capture data from Vicon markers and devices, calculate joint angles, and display device data.
- **Data Exporting**: Save data in three modes: duration, manual, and window.
- **UDP Streaming**: Stream data to other applications on the local network with customizable packet size and format.
- **Data Visualization**: Plot joint angles and device data for review.
- **Filtering**: Apply bandpass, moving average, and moving median filters to angle data with configurable parameters.

## Configuration 🚀

### Before Launching the Interface

1. **Network Setup**: Ensure the PC is on the same network as the Vicon PC and has the Vicon PC's IP address.
2. **Vicon System Configuration**: 
   - Create a subject in Vicon Nexus.
   - Label all markers so the Vicon Data Interface can recognize them.
3. **Connection**: Once Nexus is ready and live, connect the PC with the Vicon Data Interface to Nexus over the local network.

### Incoming Data Quality

- **Data Relevance**: Select only the most relevant data to the scenario to enhance performance. This minimizes processing time between interface frames, allowing more data to be received over time.
- **Device Data**: Each frame can have multiple values per device. For instance, if a device collects at 1000Hz and Vicon's acquisition frequency is 100Hz, each frame received by the interface will contain 10 value points.

## Streaming Capability 📡

The interface can reroute data to other applications on the local network using UDP communication. Here’s how:

1. **Configuration**: Input the application's local IP address and network port.
2. **Packet Customization**: Adjust the packet size and format as needed.
3. **Data Selection**: Use the table in the interface to select the data to send to the application.

## Additional Functions 🔧

### Plotting 📈

- **Data Review**: The plotting capability allows for the review of received data.
- **Display**: The plot can display 2 joint angles and 1 device data output.

### Exporting 💾

- **Modes**: 
  - **Duration**: Save a specified number of seconds.
  - **Manual**: Manually start and stop the recording.
  - **Window**: Save data for the duration equal to the plotting duration.

### Filtering 🌐

- **Types**: 
  - **Bandpass**
  - **Moving Average**
  - **Moving Median**
- **Configuration**: Parameters for each filter are configurable within the interface.


## Usage 📚

1. **Run the application**:
    ```bash
    python main.py
    ```

2. **Connect to Vicon System**: The application will connect to the Vicon system and start streaming data.

3. **Visualize Data**: Use the GUI to select devices, channels, and angles for visualization. Customize the chart display using the provided controls.

4. **Export Data**: Use the export tab to specify data to record and export to CSV files. Start and stop recordings as needed.

5. **Stream Data**: Configure UDP streaming settings and start streaming to the target IP and port.

