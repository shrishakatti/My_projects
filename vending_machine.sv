module vending_machine(
    input logic clk, reset,    // Clock & Reset
    input logic T3, R2, U1,    // Selection buttons (Tea, Coffee, Lemon Tea)
    input logic [7:0] coin,    // Coin input (₹5, ₹10, ₹20)
    output logic [6:0] display // 7-Segment Display Output
);

    // Price Definitions
    localparam TEA_PRICE = 5;
    localparam COFFEE_PRICE = 10;
    localparam LEMON_TEA_PRICE = 20;

    always_ff @(posedge clk or posedge reset) begin
        if (reset) 
            display <= 7'b0000000; // Clear display on reset
        else begin
            case(1'b1)
                (T3 && coin == TEA_PRICE): display <= 7'b0110000; // Show 3 for Tea
                (R2 && coin == COFFEE_PRICE): display <= 7'b0100100; // Show 2 for Coffee
                (U1 && coin == LEMON_TEA_PRICE): display <= 7'b1111001; // Show 1 for Lemon Tea
                default: display <= 7'b0000000; // No output for incorrect amount
            endcase
        end
    end
endmodule
