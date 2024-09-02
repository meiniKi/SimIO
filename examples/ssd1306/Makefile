
VERILATOR ?= /tools/verilator/verilator/bin/verilator

SRC_TB 			= tb_ssd1306_spi4.cpp

SRC_DPI_SOCK 	= ../../sock.sv/sock.c
SRC_DPI_JSON	= ../../JSON.sv/sv/util.sv ../../JSON.sv/sv/json.sv 

INC_SOCK = ../../sock.sv/sock.sv
INC_JSON = ../../JSON.sv/sv/json.svh

SRCS	= $(SRC_DPI_JSON) $(SRC_TB) $(SRC_DPI_SOCK)
INC 	= $(INC_SOCK) $(INC_JSON)

.PHONY: ssd1306_spi4
ssd1306_spi4: $(SRCS) ../../components/verilog/ssd1306/simio_ssd1306_spi4.sv
	$(VERILATOR) --trace-fst --timing --cc --exe --build  --relative-includes -j 0 -I $(INC) --timescale-override "1ns/1ps" --top simio_ssd1306_spi4 $(SRCS) ../../components/verilog/ssd1306/simio_ssd1306_spi4.sv

.PHONY: clean
clean:
	rm -rf obj_dir
