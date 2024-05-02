# simio

simio is a library of peripheral models to provide virtualized hardware for digital design simulation. For example, a virtual OLED display can be instantiated in the testbench via an interface identical to the actual hardware. Thus, the output image can be seen live as the simulation progresses. The library builds on the SystemVerilog Direct Programming Interface (DPI) to be simulator-agnostic.

While simio comes with a set of dedicated peripherals models, the concept is kept gerneric to add new models when needed.

> [!IMPORTANT]  
> :triangular_ruler: Please note that the library is work in progress.

# Operation

![Overview Diagram](./doc/simio.png)

The following example depicts the data flow for an SSD1306 OLED display with SPI interface. `ssd1306_spi4.sv` implements the SystemVerilog model that can be instantiated in the simulation. It receives the data and maintains an internal state, e.g., the addressing mode it is configured to. The hardware-specific configuration is converted into a display-generic interpretation, e.g., (a) display inverted: true/false, (b) display pixel data, etc. This information is parsed to a JSON string by `json.sv`. Once parsed, the DPI-C is used to communicate with a Python socket server by `sock.sv`. It receives the JSON string and distributes it to all clients  (GUIs) connected to the server. Each JSON string is prefixed by an identifier, so only the addressed client will process it. The client decodes the data and, in the case of the display GUI, draws the data on a tkinter canvas.