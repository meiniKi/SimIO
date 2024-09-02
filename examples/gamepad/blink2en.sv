// Copyright (c) 2024 Meinhard Kissich
// SPDX-License-Identifier: MIT
// -----------------------------------------------------------------------------
// File  :  blink2en.sv
// Usage :  Simple 2-output counter with separate enable signals
//          to demonstrate the Gamepad SimIO component.
// GUI   :  gui_gamepad.py
//
// Ports
//  - r_i   VGA red.
//  - g_i   VGA green.
//  - b_i   VGA blue.
//  - hs_i  Horizontal sync.
//  - vs_i  Vertical sync.
// -----------------------------------------------------------------------------

module blink2en (
  input  logic clk_i,
  input  logic rst_in,

  input  logic en1_i,
  input  logic en2_i,
  output logic out1_o,
  output logic out2_o
);

localparam NR_BITS = 21; 

logic [NR_BITS-1:0] cnt_r;

assign out1_o = en1_i & cnt_r[NR_BITS-1];
assign out2_o = en2_i & cnt_r[NR_BITS-3];

always_ff @( posedge clk_i ) begin
  cnt_r <= cnt_r + 'b1;
  if (~rst_in) begin
    cnt_r <= 'b0;
  end
end

endmodule