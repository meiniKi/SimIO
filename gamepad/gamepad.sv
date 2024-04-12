// Copyright (c) 2024 Meinhard Kissich
// SPDX-License-Identifier: MIT
// -----------------------------------------------------------------------------
// File  :  gamepad.sv
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

module gamepad(
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

  // Adapt server and port here
  localparam SOCK_ADDR = "tcp://localhost:1080";

  timeunit 1ns;
  chandle h;
  string  rd = "\n";

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
      rd = sock_readln(h);
      if (rd != "") begin
        $display(rd);
      end
    end
  end

final begin
	sock_close(h);
	sock_shutdown();
end


endmodule