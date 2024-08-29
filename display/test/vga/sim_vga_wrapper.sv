
module sim_vga_wrapper (
  input clk_i,
  input rst_in
);

logic [1:0] r;
logic [1:0] g;
logic [1:0] b;
logic hs;
logic vs;

tiny_vga i_tiny_vga (
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