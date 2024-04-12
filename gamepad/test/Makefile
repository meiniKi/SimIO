
VERILATOR := verilator

SRC_TB 		= tb.cpp
SRC_MODEL	= ../gamepad.sv
SRC_DPI 	= ../../sock.sv/sock.c

INC_SOCK = ../../sock.sv/sock.sv

SRCS	= $(SRC_TB) $(SRC_MODEL) $(SRC_DPI)
INC 	= $(INC_SOCK) 

build: $(SRCS)
	$(VERILATOR) --trace-fst --timing --cc --exe --build  --relative-includes -j 0 -I $(INC) --timescale-override "1ns/1ps" --top gamepad $(SRCS)

clean:
	rm -rf obj_dir
