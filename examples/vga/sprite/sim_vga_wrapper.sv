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

top i_top (
    .clk            ( clk_i   ),
    .reset_n        ( rst_in  ),
    .spi_sclk       ( 1'b0    ),
    .spi_mosi       ( 1'b0    ),
    .spi_miso       (),
    .spi_cs         ( 1'b1    ),
    .rrggbb         ( {r,g,b} ),
    .hsync          ( hs      ),
    .vsync          ( vs      ),
    .next_vertical  (),
    .next_frame     ()  
);


endmodule