

.PHONY: example.gamepad
example.gamepad:
	make -C examples/gamepad

.PHONY: example.vga.sprite
example.vga.sprite:
	make -C examples/vga/sprite

.PHONY: example.vga.shader
example.vga.shader:
	make -C examples/vga/shader

.PHONY: example.vga.donut
example.vga.donut:
	make -C examples/vga/donut

.PHONY: example.ssd1306
example.ssd1306:
	make -C examples/ssd1306

.PHONY: clean
clean:
	make -C examples/gamepad clean
	make -C examples/vga/shader clean
	make -C examples/vga/sprite clean
	make -C examples/vga/donut clean
	make -C examples/ssd1306 clean