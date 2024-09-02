// Copyright (c) 2024 Meinhard Kissich
// SPDX-License-Identifier: MIT
// -----------------------------------------------------------------------------
// File  :  tb_vga.cpp
// Usage :  Testbench for SystemVerilog Tiny VGA model.
// -----------------------------------------------------------------------------

#include <svdpi.h>
#include <fcntl.h>
#include <stdint.h>
#include <signal.h>

#include "verilated_fst_c.h"
#include "Vsim_vga_wrapper.h"

using namespace std;

static bool finish;
vluint64_t time_sim = 0;

double sc_time_stamp () { return time_sim; }

void INThandler(int signal)
{
  printf("\nCaught ctrl-c\n");
  finish = true;
}


int main(int argc, char **argv, char **env)
{
  Verilated::commandArgs(argc, argv);

  Vsim_vga_wrapper* top = new Vsim_vga_wrapper;

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

  top->clk_i = 1;
  top->rst_in = 0;

  while (!finish && !Verilated::gotFinish())
  {
    if (tfp) { tfp->dump(time_sim); }
    top->eval();

    if (time_sim % half_period == 0)
    {
      top->clk_i = !top->clk_i;
    }
    time_sim += half_period/2;

    if (time_sim > 20*half_period)
    {
      top->rst_in = 1;
    }
  }

  if (tfp) { tfp->close(); }
  exit(0);
}