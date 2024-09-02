// Copyright (c) 2024 Meinhard Kissich
// SPDX-License-Identifier: MIT
// -----------------------------------------------------------------------------
// File  :  sim_vga_wrapper.sv
// Usage :  Wrapper for a VGA example

// Ports
//  - clk_i   Clock
//  - rst_in  Low active reset
// -----------------------------------------------------------------------------

module sim_vga_wrapper (
  input clk_i,
  input rst_in
);

logic [1:0] r;
logic [1:0] g;
logic [1:0] b;
logic hs;
logic vs;

simio_vga i_simio_vga (
  .r_i  ( r   ),
  .g_i  ( g   ),
  .b_i  ( b   ),
  .hs_i ( hs  ),
  .vs_i ( vs  )
);

tt_um_tiny_shader_mole99 i_tt_um_tiny_shader_mole99 (
  .ui_in        ( 'b0    ),
  .uo_out       ( {hs, b[0], g[0], r[0], vs, b[1], g[1], r[1]} ),
  .uio_in       ( 8'hff  ),
  .uio_out      (  ),
  .uio_oe       (  ),
  .ena          ( 1'b1   ),
  .clk          ( clk_i  ),
  .rst_n        ( rst_in )
);


endmodule