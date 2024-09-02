// Copyright (c) 2024 Meinhard Kissich
// SPDX-License-Identifier: MIT
// -----------------------------------------------------------------------------
// File  :  gui_gamepad.sv
// Usage :  SystemVerilog Gamepad model.
//
// Ports
//  - clk_i       Clock input.
//  - led1_i      Status LED 1 to show on gamepad.
//  - led2_i      Status LED 2 to show on gamepad.
//  - key_up_o    Button UP pressed on gamepad.
//  - key_down_o  Button DOWN pressed on gamepad.
//  - key_right_o Button RIGHT pressed on gamepad.
//  - key_left_o  Button LEFT pressed on gamepad.
//  - key_a_o     Button A pressed on gamepad.
//  - key_b_o     button B pressed on gamepad.
// -----------------------------------------------------------------------------

import sock::*;
import json::*;

module gamepad
#(
  parameter SOCK_ADDR = "tcp://localhost:1080"
) (
  input  logic clk_i,

  input  logic led1_i,
  input  logic led2_i,

  output logic key_up_o,
  output logic key_down_o,
  output logic key_right_o,
  output logic key_left_o,
  output logic key_a_o,
  output logic key_b_o
);
  
  // Server commands
  localparam SRV_PREFIX = "[gamepad]-";

  timeunit 1ns;
  chandle h;
  string  rd = "\n";
  Object j = null;
  util::String s;
  int r;

  logic prev_led1_r;
  logic prev_led2_r;

  Boolean led1;
  Boolean led2;

  initial begin
    if (sock_init() < 0) begin
      $fatal("[Error] Cannot init library.");
    end

    h = sock_open(SOCK_ADDR);
    if (h == null) begin
      $error("[Error] Cannot connect.");
      sock_shutdown();
	    $stop();
    end

    while (1) begin
      @(negedge clk_i);
      //#100

      // receive
      rd = sock_readln(h);
      if ((rd != "") && (rd.substr(0, 9).compare(SRV_PREFIX) == 0)) begin
        s = new(rd.substr(10, rd.len()-1));
        j = json::LoadS(s);
        assert(j != null);

        key_up_o    = j.getByKey("u").isTrue();
        key_down_o  = j.getByKey("d").isTrue();
        key_right_o = j.getByKey("r").isTrue();
        key_left_o  = j.getByKey("l").isTrue();
        key_a_o     = j.getByKey("a").isTrue();
        key_b_o     = j.getByKey("b").isTrue();
      end

      // send
      if ((prev_led1_r != led1_i) || (prev_led2_r != led2_i)) begin
        j = new();
        // cannot be done within j.append() (verilator)
        led1 = new(led1_i);
        led2 = new(led2_i);
        s = new();
        j.append("led1", led1);
        j.append("led2", led2);
        j.dumpS(s);
        r = sock_writeln(h, {SRV_PREFIX, s.get()});
      end
      prev_led1_r = led1_i;
      prev_led2_r = led2_i;

    end
  end

final begin
	sock_close(h);
	sock_shutdown();
end

endmodule
