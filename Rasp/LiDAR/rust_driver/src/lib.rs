use pyo3::prelude::*;
use serialport::SerialPort;
use std::io::{Read, Write};
use std::time::{Duration, Instant};

#[pyclass]
struct RPLidarC1M1 {
    port: String,
    baud: u32,
    timeout_secs: f32,
    serial: Option<Box<dyn SerialPort>>,
    buf: Vec<u8>,
    last_s: u8,
}

#[pymethods]
impl RPLidarC1M1 {
    #[new]
    fn new(port: String, baud: u32, timeout: f32) -> Self {
        RPLidarC1M1 {
            port,
            baud,
            timeout_secs: timeout,
            serial: None,
            buf: Vec::with_capacity(4096),
            last_s: 0,
        }
    }

    fn connect(&mut self) -> PyResult<()> {
        let port_builder = serialport::new(&self.port, self.baud)
            .timeout(Duration::from_secs_f32(self.timeout_secs));
        
        match port_builder.open() {
            Ok(mut port) => {
                let _ = port.write_data_terminal_ready(false); // Motor enabled (Active Low)
                let _ = port.write_request_to_send(false);
                println!("[LIDAR-RS] Connecté sur {}", self.port);
                self.serial = Some(port);
                Ok(())
            }
            Err(e) => {
                println!("[LIDAR-RS] Erreur de connexion sur {} : {}", self.port, e);
                // In Python code, it gracefully fails and sets self.ser = None
                self.serial = None;
                Ok(()) // Don't raise Python exception to match python behavior if possible, or maybe raise
            }
        }
    }

    fn close(&mut self) {
        if let Some(mut port) = self.serial.take() {
            let _ = port.write_all(b"\xA5\x25"); // CMD_STOP
            let _ = port.flush();
            std::thread::sleep(Duration::from_millis(50));
            // droppping port closes it
        }
        println!("[LIDAR-RS] Port fermé.");
    }

    fn start_scan(&mut self) -> PyResult<()> {
        if let Some(ref mut port) = self.serial {
            // Reset
            let _ = port.write_all(b"\xA5\x25"); // STOP
            let _ = port.flush();
            std::thread::sleep(Duration::from_millis(50));
            let _ = port.clear(serialport::ClearBuffer::Input);

            // Start scan
            let _ = port.write_all(b"\xA5\x20"); // SCAN
            let _ = port.flush();

            // Read descriptor (7 bytes)
            let mut desc = vec![0u8; 7];
            let start = Instant::now();
            let mut read_count = 0;
            
            while read_count < 7 && start.elapsed().as_secs_f32() < 1.0 {
                if let Ok(n) = port.read(&mut desc[read_count..]) {
                    read_count += n;
                }
            }
            
            let expected_desc = [0xA5, 0x5A, 0x05, 0x00, 0x00, 0x40, 0x81];
            if desc != expected_desc {
                println!("[LIDAR-RS] WARN: Descripteur inattendu {:?}", desc);
            }

            self.buf.clear();
            self.last_s = 0;
        }
        Ok(())
    }
    
    fn clean_input(&mut self) {
        if let Some(ref mut port) = self.serial {
             let _ = port.clear(serialport::ClearBuffer::Input);
        }
        self.buf.clear();
        self.last_s = 0;
    }

    /// Returns a list of (angle, dist, qual) tuples or None
    fn get_scan(&mut self, min_dist: f32, max_dist: f32) -> Option<Vec<(f32, f32, u8)>> {
        if self.serial.is_none() {
            return None;
        }
        let port = self.serial.as_mut().unwrap();

        let mut revolution = Vec::with_capacity(360);
        let mut temp_buf = [0u8; 512];
        let deadline = Instant::now() + Duration::from_millis(500);

        while Instant::now() < deadline {
            // Read available data
            match port.bytes_to_read() {
                Ok(n) if n > 0 => {
                   let to_read = (n as usize).min(temp_buf.len());
                   if let Ok(count) = port.read(&mut temp_buf[..to_read]) {
                       self.buf.extend_from_slice(&temp_buf[..count]);
                   }
                },
                _ => {
                    // Try a small blocking read
                    match port.read(&mut temp_buf[..64]) {
                        Ok(n) if n > 0 => {
                            self.buf.extend_from_slice(&temp_buf[..n]);
                        },
                        _ => { continue; }
                    }
                }
            }

            // Process all complete packets in buffer
            loop {
                if self.buf.len() < 5 { break; }

                // Sync with 0xA5
                if self.buf[0] != 0xA5 {
                    if let Some(idx) = self.buf.iter().position(|&x| x == 0xA5) {
                        self.buf.drain(..idx);
                    } else {
                        self.buf.clear();
                        break;
                    }
                    if self.buf.len() < 5 { break; }
                }

                // Decode sample
                let b0 = self.buf[0];
                let b1 = self.buf[1];
                let b2 = self.buf[2];
                let b3 = self.buf[3];
                let b4 = self.buf[4];

                let s = b0 & 0x01;
                let s_bar = (b0 >> 1) & 0x01;
                let c = b1 & 0x01;

                if (s ^ s_bar) != 1 || c != 1 {
                    self.buf.drain(..1);
                    continue;
                }

                // Valid packet, consume 5 bytes
                self.buf.drain(..5);

                let qual = (b0 >> 2) & 0x3F;
                let angle_q6 = ((b2 as u16) << 7) | ((b1 as u16) >> 1);
                let dist_q2 = ((b4 as u16) << 8) | (b3 as u16);

                let angle = (angle_q6 as f32) / 64.0;
                let dist = (dist_q2 as f32) / 4.0;

                // Handle revolution
                if s == 1 && self.last_s == 0 {
                    self.last_s = s;
                    if revolution.len() > 50 {
                        return Some(revolution);
                    } else {
                        revolution.clear();
                    }
                }
                self.last_s = s;

                if dist > min_dist && dist < max_dist {
                    revolution.push((angle, dist, qual));
                }
            }
        }

        None
    }
}

#[pymodule]
fn robot_lidar(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RPLidarC1M1>()?;
    Ok(())
}
