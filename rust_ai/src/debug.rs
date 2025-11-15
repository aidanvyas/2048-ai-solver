use crate::*;

pub fn debug_move_execution() {
    println!("Testing move execution:");

    // Test board: [[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    let board = [[2u32, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]];
    let packed = pack_board(&board);

    println!("Original board: {:?}", board);
    println!("Packed: {:016x}", packed);

    // Test all moves
    for dir in 0..4 {
        let (new_board, score, changed) = execute_move(packed, dir);
        let unpacked = unpack_board(new_board);
        let move_name = match dir {
            0 => "LEFT",
            1 => "RIGHT",
            2 => "UP",
            3 => "DOWN",
            _ => "?"
        };
        println!("{}: changed={}, score={}, result={:?}",
                 move_name, changed, score, unpacked[0]);
    }

    // Test evaluation
    println!("\nTesting evaluation:");
    let eval = evaluate_position(packed);
    println!("Evaluation of [[2,2,0,0],...]: {}", eval);

    // Test a merged board
    let merged_board = [[4u32, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]];
    let merged_packed = pack_board(&merged_board);
    let merged_eval = evaluate_position(merged_packed);
    println!("Evaluation of [[4,0,0,0],...]: {}", merged_eval);

    // The merged board should have higher evaluation (more empty cells)
    println!("Merged eval > original eval: {}", merged_eval > eval);
}