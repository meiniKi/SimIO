
VERILATOR ?= /tools/verilator/verilator/bin/verilator

SRC_TB 			= ../tb_vga.cpp

SRC_SIMIO		= ../../../components/verilog/vga/simio_vga.sv

RTL 			= tt05-one-sprite-pony/src/top.sv \
    			  tt05-one-sprite-pony/src/timing.sv \
    			  tt05-one-sprite-pony/src/sprite_access.sv \
    			  tt05-one-sprite-pony/src/sprite_data.sv \
    			  tt05-one-sprite-pony/src/sprite_movement.sv \
    			  tt05-one-sprite-pony/src/background.sv \
    			  tt05-one-sprite-pony/src/synchronizer.sv \
    			  tt05-one-sprite-pony/src/spi_receiver.sv

SRC_DPI_SOCK 	= ../../../sock.sv/sock.c
SRC_DPI_JSON	= ../../../JSON.sv/sv/util.sv ../../../JSON.sv/sv/json.sv 

INC_SOCK = ../../../sock.sv/sock.sv
INC_JSON = ../../../JSON.sv/sv/json.svh

SRCS	= $(RTL) $(SRC_DPI_JSON) $(SRC_SIMIO) $(SRC_TB) $(SRC_DPI_SOCK) sim_vga_wrapper.sv
INC 	= $(INC_SOCK) $(INC_JSON)

.PHONY: sprite
sprite: $(SRCS)
	$(VERILATOR) --trace-fst --timing --cc --exe --build  --relative-includes -j 0 -I $(INC) --timescale-override "1ns/1ps" --top sim_vga_wrapper $(SRCS)

.PHONY: clean
clean:
	rm -rf obj_dir
