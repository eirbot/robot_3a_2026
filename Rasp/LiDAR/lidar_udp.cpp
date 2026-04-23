#include <arpa/inet.h>
#include <cmath>
#include <cstring>
#include <fcntl.h>
#include <iostream>
#include <sys/socket.h>
#include <termios.h>
#include <unistd.h>

using namespace std;

#pragma pack(push, 1)
struct LidarPoint {
  float angle;
  float distance;
  float intensity;
};
#pragma pack(pop)

void read_exactly(int fd, unsigned char *buf, int n) {
  int total = 0;
  while (total < n) {
    int r = read(fd, buf + total, n - total);
    if (r > 0)
      total += r;
  }
}

float normalize_angle(float angle) {
  angle = fmod(angle, 360.0f);
  if (angle < 0)
    angle += 360.0f;
  return angle;
}

int main() {
  int sock = socket(AF_INET, SOCK_DGRAM, 0);
  sockaddr_in addr;
  memset(&addr, 0, sizeof(addr));
  addr.sin_family = AF_INET;
  addr.sin_port = htons(8080);
  inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr);

  const char *port = "/dev/ttyUSB0";
  int serial_fd = open(port, O_RDWR | O_NOCTTY | O_SYNC);
  if (serial_fd < 0)
    return 1;

  struct termios tty;
  tcgetattr(serial_fd, &tty);
  cfsetospeed(&tty, B460800);
  cfsetispeed(&tty, B460800);
  tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8;
  tty.c_iflag &= ~IGNBRK;
  tty.c_lflag = 0;
  tty.c_oflag = 0;
  tty.c_cc[VMIN] = 1;
  tty.c_cc[VTIME] = 1;
  tty.c_iflag &= ~(IXON | IXOFF | IXANY);
  tty.c_cflag |= (CLOCAL | CREAD);
  tcsetattr(serial_fd, TCSANOW, &tty);

  unsigned char stop_cmd[] = {0xA5, 0x25};
  write(serial_fd, stop_cmd, 2);
  usleep(50000);
  unsigned char start_cmd[] = {0xA5, 0x20};
  write(serial_fd, start_cmd, 2);
  unsigned char desc[7];
  read_exactly(serial_fd, desc, 7);

  unsigned char chunk[1024];
  unsigned char buf[5] = {0};

  float min_dist = 99999.0f, min_angle = 0.0f, min_qual = 0.0f;
  bool has_points = false;
  float last_angle_sync = -1.0f;

  // --- VARIABLES DU FILTRE DE COHÉRENCE ---
  float last_obj_dist = 0.0f;
  float last_obj_angle = 0.0f;
  int coherent_points = 0;

  cout << "[LIDAR] C++ Prêt ! Filtre de grappe (Cluster) ACTIVÉ." << endl;

  while (true) {
    int n = read(serial_fd, chunk, sizeof(chunk));
    if (n <= 0) {
      cerr << "[LIDAR C++] ⚡ ERREUR CRITIQUE: Perte de connexion USB de "
              "lecture (n="
           << n << ") ! Le port a saut\u00e9." << endl;
      break;
    }

    for (int i = 0; i < n; i++) {
      buf[0] = buf[1];
      buf[1] = buf[2];
      buf[2] = buf[3];
      buf[3] = buf[4];
      buf[4] = chunk[i];

      if (((buf[0] & 0x01) ^ ((buf[0] >> 1) & 0x01)) == 1 &&
          (buf[1] & 0x01) == 1) {

        int S = buf[0] & 0x01;
        float angle = normalize_angle(((buf[2] << 7) | (buf[1] >> 1)) / 64.0f);
        float dist = ((buf[4] << 8) | buf[3]) / 4.0f;
        float qual = (float)((buf[0] >> 2) & 0x3F);

        // Anti-désynchronisation (Vérif angle)
        bool angle_ok = true;
        if (last_angle_sync >= 0.0f && S == 0) {
          float diff = angle - last_angle_sync;
          if (diff < -180.0f)
            diff += 360.0f;
          else if (diff > 180.0f)
            diff -= 360.0f;
          if (diff < -2.0f || diff > 20.0f)
            angle_ok = false;
        }

        if (!angle_ok) {
          last_angle_sync = -1.0f;
          continue;
        }

        last_angle_sync = angle;

        // --- GESTION DU TOUR COMPLET ---
        if (S == 1) {
          // ALWAYS send a packet. If no obstacles, dist is 99999.0f
          LidarPoint pt = {min_angle, min_dist, min_qual};
          sendto(sock, &pt, sizeof(pt), 0, (struct sockaddr *)&addr,
                 sizeof(addr));

          min_dist = 99999.0f;
          has_points = false;
          coherent_points = 0; // Reset du cluster en début de tour
        }

        // --- FILTRE DE DISTANCE & QUALITÉ ---
        if (dist > 80.0f && qual > 10.0f) {

          // Calcul de la distance avec le point précédent
          float angle_diff = angle - last_obj_angle;
          if (angle_diff < -180.0f)
            angle_diff += 360.0f;
          else if (angle_diff > 180.0f)
            angle_diff -= 360.0f;

          // Si le point est à moins de 50mm et 5° du point précédent, c'est le
          // même objet
          if (fabs(dist - last_obj_dist) < 50.0f && fabs(angle_diff) < 5.0f) {
            coherent_points++;
          } else {
            coherent_points = 1; // C'est un point isolé, on reset le compteur
          }

          last_obj_dist = dist;
          last_obj_angle = angle;

          // --- VALIDATION : Au moins 3 points collés ---
          if (coherent_points >= 3) {
            if (dist < min_dist) {
              min_dist = dist;
              min_angle = angle;
              min_qual = qual;
              has_points = true;
            }
          }
        }

        buf[0] = 0;
        buf[1] = 0;
        buf[2] = 0;
        buf[3] = 0;
        buf[4] = 0;
      }
    }
  }
  return 0;
}