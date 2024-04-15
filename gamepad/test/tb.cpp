// Copyright (c) 2024 Meinhard Kissich
// SPDX-License-Identifier: MIT
// -----------------------------------------------------------------------------
// File  :  tb.cpp
// Usage :  Testbench for SystemVerilog Gamepad model.
// -----------------------------------------------------------------------------

#include <svdpi.h>
#include <fcntl.h>
#include <stdint.h>
#include <signal.h>

#include "verilated_fst_c.h"
#include "Vgamepad.h"

using namespace std;

static bool finish;
vluint64_t time_sim = 0;

double sc_time_stamp () { return time_sim; }

void INThandler(int signal)
{
  printf("\nCaught ctrl-c\n");
  finish = true;
}

typedef struct {
  bool led1;
  bool led2;
  bool key_up;
  bool key_down;
  bool key_right;
  bool key_left;
  bool key_a;
  bool key_b;
} state_gpio_t;

void do_gpio(state_gpio_t *state, Vgamepad* top)
{
  if (state->key_up != top->key_up_o)
    printf("[CHG] key_up -> %s\n", top->key_up_o ? "ON" : "OFF");

  if (state->key_down != top->key_down_o)
    printf("[CHG] key_down -> %s\n", top->key_down_o ? "ON" : "OFF");

  if (state->key_left != top->key_left_o)
    printf("[CHG] key_left -> %s\n", top->key_left_o ? "ON" : "OFF");

  if (state->key_right != top->key_right_o)
    printf("[CHG] key_right -> %s\n", top->key_right_o ? "ON" : "OFF");

  if (state->key_a != top->key_a_o)
    printf("[CHG] key_a -> %s\n", top->key_a_o ? "ON" : "OFF");

  if (state->key_b != top->key_b_o)
    printf("[CHG] key_b -> %s\n", top->key_b_o ? "ON" : "OFF");

  state->key_up     = top->key_up_o;
  state->key_down   = top->key_down_o;
  state->key_right  = top->key_right_o;
  state->key_left   = top->key_left_o;
  state->key_a      = top->key_a_o;
  state->key_b      = top->key_b_o;

  top->led1_i = top->key_left_o;
  top->led2_i = top->key_right_o;
}

int main(int argc, char **argv, char **env)
{
  state_gpio_t state_gpio;
  Verilated::commandArgs(argc, argv);

  Vgamepad* top = new Vgamepad;

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
  top->led1_i = 0;
  top->led2_i = 0;

  while (!finish && !Verilated::gotFinish())
  {
    if (tfp) { tfp->dump(time_sim); }

    top->eval();
    do_gpio(&state_gpio, top);

    if (time_sim % half_period == 0) {
      top->clk_i = !top->clk_i;
    }

    time_sim += half_period/2;
  }

  if (tfp) { tfp->close(); }
  exit(0);
}