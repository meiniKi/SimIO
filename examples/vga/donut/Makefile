
VERILATOR ?= /tools/verilator/verilator/bin/verilator

SRC_TB 			= ../tb_vga.cpp

SRC_SIMIO		= ../../../components/verilog/vga/simio_vga.sv

RTL 			= 	tt08-vga-donut/src/tt_um_a1k0n_vgadonut.v \
					tt08-vga-donut/src/vgadonut.v \
					tt08-vga-donut/src/cordic2step.v \
					tt08-vga-donut/src/donuthit.v \
					tt08-vga-donut/src/cordic3step.v \
					tt08-vga-donut/src/step3vec.v \
					tt08-vga-donut/src/donut.v

SRC_DPI_SOCK 	= ../../../sock.sv/sock.c
SRC_DPI_JSON	= ../../../JSON.sv/sv/util.sv ../../../JSON.sv/sv/json.sv 

INC_SOCK = ../../../sock.sv/sock.sv
INC_JSON = ../../../JSON.sv/sv/json.svh

SRCS	= $(RTL) $(SRC_DPI_JSON) $(SRC_SIMIO) $(SRC_TB) $(SRC_DPI_SOCK) sim_vga_wrapper.sv
INC 	= $(INC_SOCK) $(INC_JSON)

.PHONY: donut
donut: $(SRCS)
	$(VERILATOR) --trace-fst --timing --cc --exe --build  --relative-includes -j 0 -I $(INC) --timescale-override "1ns/1ps" --top sim_vga_wrapper $(SRCS) -Wno-WIDTHTRUNC -Wno-WIDTHEXPAND

.PHONY: clean
clean:
	rm -rf obj_dir
