// Copyright (c) 2024 Meinhard Kissich
// SPDX-License-Identifier: MIT
// -----------------------------------------------------------------------------
// File  :  ssd1306_spi.sv
// Usage :  SystemVerilog SSD1306 SPI 4-wire model.
//
// Limitations: Only a subset of commands are supported. All others are ignored.
//  Command:
//    Entire Display ON:    A4/A5
//    Set Normal/Inverse:   A6/A7
//    Set ON/OFF:           AE/AF
//  Scrolling Command:
//    (none)
//
//  Hardware Configuration:
//    Set Segment Re-map:   A0/A1
//    COM Scan Direction:   C0/C8
//  Addressing Setting:
//    Set Addressing Mode:  20 + A[1:0]
//
//
//  Deviations from datasheet:
//    * Devices does _not_ start in page addressing mode
//
// Ports
//  - cs_in       Chip select, low active.
//  - sdi_i       Serial data in.
//  - sck_i       Serial clock.
//  - dc_i        Data / command select.
// -----------------------------------------------------------------------------

import sock::*;
import json::*;

module ssd1306_spi4(
  input  logic cs_in,
  input  logic sdi_i,
  input  logic sck_i,
  input  logic dc_i
);

  // Adapt server and port here
  localparam SOCK_ADDR = "tcp://localhost:1080";
  
  // Server commands
  string SRV_PREFIX     = "[display]-";

  string SRV_INV        = "<inverse>";
  string SRV_ONOFF      = "<onoff>";
  string SRV_ENTIRE_ON  = "<globon>";
  string SRV_FLIP_HOR   = "<flipx>";
  string SRV_FLIP_VERT  = "<flipy>";
  string SRV_ADR_MODE   = "<adr>";

  string SRV_ADR_MODE_invalid     = "invalid";
  string SRV_ADR_MODE_horizontal  = "horizontal";
  string SRV_ADR_MODE_vertical    = "vertical";
  string SRV_ADR_MODE_paging      = "paging";

  // Settings
  localparam DISP_WIDTH   = 128;
  localparam DISP_HEIGHT  = 64;

  timeunit 1ns;
  chandle h;
  Object j = null;
  json::Integer data_int;
  util::String s;
  json::String data_str;
  int r;

  json::Boolean const_false;
  json::Boolean const_true;

  // Display commands
  localparam DC_CMD_DISP_ENTIRE_ON_DISABLE  = 9'h0_A4;
  localparam DC_CMD_DISP_ENTIRE_ON_ACTIVE   = 9'h0_A5;

  localparam DC_CMD_DISP_INVERSE_DISABLE    = 9'h0_A6;
  localparam DC_CMD_DISP_INVERSE_ACTIVE     = 9'h0_A7;

  localparam DC_CMD_DISPLAY_ONOFF_OFF       = 9'h0_AE;
  localparam DC_CMD_DISPLAY_ONOFF_ON        = 9'h0_AF;

  localparam DC_CMD_SEG_REMAP_DEFAULT       = 9'h0_A0;
  localparam DC_CMD_SEG_REMAP_INVERSE       = 9'h0_A1;

  localparam DC_CMD_COM_DIR_DEFAULT         = 9'h0_C0;
  localparam DC_CMD_COM_DIR_REVERSE         = 9'h0_C8;

  localparam DC_CMD_ADR_MODE                = 9'h0_20;

  // Display state
  enum int unsigned { ADR_HOR=0, ADR_VERT=1, ADR_PAGE=2, ADR_INVALID=3 } disp_adr_mode = ADR_PAGE;

  int adr_pntr_col = 0;
  int adr_pntr_row = 0;

  initial begin
    const_false = new(0);
    const_true  = new(1);

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

final begin
	sock_close(h);
	sock_shutdown();
end


logic [7:0] buffer;
int         bitcnt = 0;
int         bytecnt = 0;
bit   [8:0] active_cmd = 0;

logic       rx_frame_done;

assign rx_frame_done = (bitcnt == 8);

always @(posedge sck_i) begin
  if (!cs_in) begin
    buffer = {buffer[6:0], sdi_i};
    bitcnt += 1;
  end
end

always @(negedge sck_i) begin
  if (rx_frame_done) begin
    if (~dc_i) spi_action_cmd;
    else       spi_action_data;
    bitcnt = 0;
  end
end

task send_data (input int x, input int y, input bit [7:0] data);
  // is this too inefficient? allocation statically
  j = new();
  s = new();

  data_str  = new("data");
  
  j.append("type", data_str);

  data_int  = new(x);
  j.append("x", data_int);

  data_int  = new(y);
  j.append("y", data_int);

  data_int  = new(int'(data));
  j.append("data", data_int);

  j.dumpS(s);
  r = sock_writeln(h, {SRV_PREFIX, s.get()});
endtask

task send_cmd (input string key, input Object value);
  j = new();
  s = new();

  data_str  = new("cmd");
  j.append("type", data_str);
  j.append(key, value);
  j.dumpS(s);
  r = sock_writeln(h, {SRV_PREFIX, s.get()});
endtask

bit [7:0] spi_dat;
bit       spi_dc;

// does not allow incline json::String::new()
json::String adr_string;
  
task spi_action_cmd;
begin
  spi_dat = buffer;
  spi_dc  = 1'b0;

  if ((~|active_cmd) && (bytecnt == 0)) begin
    case({spi_dc, spi_dat})
      DC_CMD_DISP_ENTIRE_ON_DISABLE: send_cmd(SRV_ENTIRE_ON, const_false);
      DC_CMD_DISP_ENTIRE_ON_ACTIVE:  send_cmd(SRV_ENTIRE_ON, const_true);
      DC_CMD_DISP_INVERSE_DISABLE:   send_cmd(SRV_INV, const_false);
      DC_CMD_DISP_INVERSE_ACTIVE:    send_cmd(SRV_INV, const_true);
      DC_CMD_DISPLAY_ONOFF_OFF:      send_cmd(SRV_ONOFF, const_false);
      DC_CMD_DISPLAY_ONOFF_ON:       send_cmd(SRV_ONOFF, const_true);
      DC_CMD_SEG_REMAP_DEFAULT:      send_cmd(SRV_FLIP_HOR, const_false);
      DC_CMD_SEG_REMAP_INVERSE:      send_cmd(SRV_FLIP_HOR, const_true);
      DC_CMD_COM_DIR_DEFAULT:        send_cmd(SRV_FLIP_VERT, const_false);
      DC_CMD_COM_DIR_REVERSE:        send_cmd(SRV_FLIP_VERT, const_true);
      DC_CMD_ADR_MODE: begin
        active_cmd  = DC_CMD_ADR_MODE;
        bytecnt     = 'd1;
      end
      default: begin end
    endcase
  end
  else begin
    // --- DC_CMD_ADR_MODE ---
    if ((active_cmd == DC_CMD_ADR_MODE) && (bytecnt == 1)) begin
      bytecnt     = 0;
      active_cmd  = 'b0;
      case (spi_dat[1:0])
        2'b00: disp_adr_mode = ADR_HOR;
        2'b01: disp_adr_mode = ADR_VERT;
        2'b10: disp_adr_mode = ADR_PAGE;
        2'b11: disp_adr_mode = ADR_INVALID;
      endcase
    end
    // ---  ---

  end
end
endtask

task spi_action_data;
begin
  spi_dat = buffer;
  spi_dc  = 1'b1;

  case(disp_adr_mode)
  ADR_HOR: begin
    send_data(adr_pntr_col, adr_pntr_row, spi_dat);
    if (adr_pntr_col == (DISP_WIDTH-1)) begin
      adr_pntr_col = 0;
      if (adr_pntr_row == (DISP_HEIGHT-8)) begin
        adr_pntr_row = 0;
      end else begin
        adr_pntr_row += 8;
      end
    end else begin
      adr_pntr_col += 1;
    end
  end
  default: begin
    adr_pntr_col = 0;
    adr_pntr_row = 0;
  end
  endcase
end
endtask


endmodule
