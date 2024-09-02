// Copyright (c) 2024 Meinhard Kissich
// SPDX-License-Identifier: MIT
// -----------------------------------------------------------------------------
// File  :  gamepad_wrapper.sv
// Usage :  Wrapper for the Gamepad example

// Ports
//  - clk_i   Clock
//  - rst_in  Low active reset
// -----------------------------------------------------------------------------

module gamepad_wrapper (
  input logic clk_i,
  input logic rst_in
);

logic en1, en2, out1, out2;

blink2en dut (
  .clk_i    ( clk_i   ),
  .rst_in   ( rst_in  ),

  .en1_i    ( en1     ),
  .en2_i    ( en2     ),
  .out1_o   ( out1    ),
  .out2_o   ( out2    )
);

gamepad i_gamepad (
  .clk_i        ( clk_i ),
  .led1_i       ( out1  ),
  .led2_i       ( out2  ),
  .key_up_o     ( /* not needed here */ ),
  .key_down_o   ( /* not needed here */ ),
  .key_right_o  ( /* not needed here */ ),
  .key_left_o   ( /* not needed here */ ),
  .key_a_o      ( en1   ),
  .key_b_o      ( en2   )
);

endmodule