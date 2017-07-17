module Adder(
  input  wire clock,
  input  wire reset,

  input  wire [31:0] a,
  input  wire [31:0] b,

  output reg [31:0] c
);
  always @(posedge clock) begin
    if (reset) begin
      c <= '0;
    end else begin
      c <= a + b;
    end
  end
endmodule
