
VERILATOR ?= /tools/verilator/verilator/bin/verilator

SRC_TB 			= ../tb_vga.cpp

SRC_SIMIO		= ../../../components/verilog/vga/simio_vga.sv

RTL 			= 	tt06-tiny-shader/src/tt_um_tiny_shader_mole99.sv \
					tt06-tiny-shader/src/tiny_shader_top.sv \
					tt06-tiny-shader/src/shader_execute.sv \
					tt06-tiny-shader/src/shader_memory.sv \
					tt06-tiny-shader/src/spi_receiver.sv \
					tt06-tiny-shader/src/timing.sv \
					tt06-tiny-shader/src/synchronizer.sv

SRC_DPI_SOCK 	= ../../../sock.sv/sock.c
SRC_DPI_JSON	= ../../../JSON.sv/sv/util.sv ../../../JSON.sv/sv/json.sv 

INC_SOCK = ../../../sock.sv/sock.sv
INC_JSON = ../../../JSON.sv/sv/json.svh

SRCS	= $(RTL) $(SRC_DPI_JSON) $(SRC_SIMIO) $(SRC_TB) $(SRC_DPI_SOCK) sim_vga_wrapper.sv
INC 	= $(INC_SOCK) $(INC_JSON)

.PHONY: sprite
sprite: $(SRCS)
	$(VERILATOR) --trace-fst --timing --cc --exe --build  --relative-includes -j 0 -I $(INC) --timescale-override "1ns/1ps" --top sim_vga_wrapper $(SRCS) -Wno-WIDTHCONCAT

.PHONY: clean
clean:
	rm -rf obj_dir
