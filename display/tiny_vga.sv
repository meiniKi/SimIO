// Copyright (c) 2024 Meinhard Kissich
// SPDX-License-Identifier: MIT
// -----------------------------------------------------------------------------
// File  :  tiny_vga.sv
// Usage :  SystemVerilog Tiny VGA model.
//
// Ports
//  - cs_in       Chip select, low active.
//  - sdi_i       Serial data in.
//  - sck_i       Serial clock.
//  - dc_i        Data / command select.
// -----------------------------------------------------------------------------

import sock::*;
import json::*;

module tiny_vga(
  input  logic [1:0] r_i,
  input  logic [1:0] g_i,
  input  logic [1:0] b_i,
  input  logic hs_i,
  input  logic vs_i
);

  // Adapt server and port here
  localparam SOCK_ADDR = "tcp://localhost:1080";
  
  localparam RGB_DEPTH = 2;

  // Server commands
  string SRV_PREFIX     = "[displayvga]-";

  timeunit 1ns;
  chandle h;
  Object j = null;
  json::Integer data_int;
  util::String s;
  json::String data_str;
  int r;


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
end

// Send data on any change and let the python handle
// any computations
always @({r_i, g_i, b_i})
  send_rgb(r_i, g_i, b_i);

always @(hs_i)
  send_hs_vs("hs", hs_i);

always @(vs_i)
  send_hs_vs("vs", vs_i);


task send_hs_vs (input string hs_vs, input bit val);
  // is this too inefficient? allocation statically
  j = new();
  s = new();

  data_str  = new(hs_vs);
  j.append("type", data_str);

  data_int  = new($stime);
  j.append("timestamp", data_int);

  data_int  = new({31'b0, val});
  j.append("value", data_int);

  j.dumpS(s);
  r = sock_writeln(h, {SRV_PREFIX, s.get()});
endtask

task send_rgb (input bit [RGB_DEPTH-1:0] cr,
              input bit [RGB_DEPTH-1:0] cg,
              input bit [RGB_DEPTH-1:0] cb);
  // is this too inefficient? allocation statically
  j = new();
  s = new();

  data_str  = new("rgb");
  j.append("type", data_str);

  data_int  = new($stime);
  j.append("timestamp", data_int);

  data_int  = new({{32-RGB_DEPTH{1'b0}}, cr});
  j.append("r", data_int);

  data_int  = new({{32-RGB_DEPTH{1'b0}}, cg});
  j.append("g", data_int);

  data_int  = new({{32-RGB_DEPTH{1'b0}}, cb});
  j.append("b", data_int);

  j.dumpS(s);
  r = sock_writeln(h, {SRV_PREFIX, s.get()});
endtask


final begin
	sock_close(h);
	sock_shutdown();
end


endmodule
