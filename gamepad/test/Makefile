
VERILATOR := /tools/verilator/verilator/bin/verilator

SRC_TB 			= tb.cpp
SRC_MODEL		= ../gamepad.sv
SRC_DPI_SOCK 	= ../../sock.sv/sock.c
SRC_DPI_JSON	= ../../JSON.sv/sv/util.sv ../../JSON.sv/sv/json.sv 

INC_SOCK = ../../sock.sv/sock.sv
INC_JSON = ../../JSON.sv/sv/json.svh

SRCS	= $(SRC_DPI_JSON) $(SRC_TB) $(SRC_MODEL) $(SRC_DPI_SOCK)
INC 	= $(INC_SOCK) $(INC_JSON)

build: $(SRCS)
	$(VERILATOR) --trace-fst --timing --cc --exe --build  --relative-includes -j 0 -I $(INC) --timescale-override "1ns/1ps" --top gamepad $(SRCS)

clean:
	rm -rf obj_dir
