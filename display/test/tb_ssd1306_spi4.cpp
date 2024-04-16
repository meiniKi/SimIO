// Copyright (c) 2024 Meinhard Kissich
// SPDX-License-Identifier: MIT
// -----------------------------------------------------------------------------
// File  :  tb_ssd1306_spi4.cpp
// Usage :  Testbench for SystemVerilog SSD1306 4-wire SPI model.
// -----------------------------------------------------------------------------

#include <svdpi.h>
#include <fcntl.h>
#include <stdint.h>
#include <signal.h>

#include "verilated_fst_c.h"
#include "Vssd1306_spi4.h"

using namespace std;

static bool finish;
vluint64_t time_sim = 0;

double sc_time_stamp () { return time_sim; }

void INThandler(int signal)
{
  printf("\nCaught ctrl-c\n");
  finish = true;
}


uint8_t pause_cycles      = 16;
uint8_t pause_cycles_cnt  = 0;

uint8_t frame_active = 0;
uint8_t frame_bit_cnt = 0;
uint8_t frame_cnt = 0;

uint8_t spi_data[]  = {0xA7, 0x20, 0x00, 0x55, 0xFF, 0x00, 0x50};
uint8_t spi_dc[]    = {0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF};

uint32_t nr_frames = sizeof(spi_data) / sizeof(spi_data[0]);


void handle_spi(Vssd1306_spi4* top)
{
  // longer pause
  if (!frame_active && (pause_cycles_cnt != 0))
  {
    printf("cs -> 1\n");
    top->cs_in = 1;
    pause_cycles_cnt--;
    return;
  }

  // start a frame
  if (!frame_active && (frame_cnt < nr_frames))
  {
    printf("cs -> 0\n");
    frame_active  = 1;
    frame_bit_cnt = 7;
    top->cs_in = 0;
  }

  if (frame_cnt == nr_frames)
    return;

  // send frame if active
  if (frame_active)
  {
    printf("next bit\n");
    top->sdi_i  = ((spi_data[frame_cnt] & (1 << frame_bit_cnt)) != 0);
    top->dc_i   = ((spi_dc[frame_cnt] & (1 << frame_bit_cnt)) != 0);
  }

  // end of frame
  if (frame_active)
  {
    if (frame_bit_cnt == 0)
    {
      printf("frame end\n");
      frame_active = 0;
      pause_cycles_cnt = pause_cycles;
      frame_cnt++;
    }
    frame_bit_cnt--;
  }

}


int main(int argc, char **argv, char **env)
{
  Verilated::commandArgs(argc, argv);

  Vssd1306_spi4* top = new Vssd1306_spi4;

  VerilatedFstC *tfp = 0;
  const char *fst = Verilated::commandArgsPlusMatch("fst=");
  if (fst[0]) {
    Verilated::traceEverOn(true);
    tfp = new VerilatedFstC;
    top->trace(tfp, 99);
    tfp->open("trace.fst");
  }

  signal(SIGINT, INThandler);
  const vluint64_t half_period = 500; // ns

  top->cs_in = 1;
  top->dc_i = 0;

  while (!finish && !Verilated::gotFinish())
  {
    if (tfp) { tfp->dump(time_sim); }
    top->eval();

    if (time_sim % half_period == 0)
    {
      top->sck_i = !top->sck_i;
      // Change data at falling edge
      if (top->sck_i == 0)
      {
        handle_spi(top);
      }

    }
    time_sim += half_period/2;
  }

  if (tfp) { tfp->close(); }
  exit(0);
}