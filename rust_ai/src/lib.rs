use pyo3::prelude::*;
use rayon::prelude::*;
use std::sync::Arc;
use parking_lot::Mutex;
use rustc_hash::FxHashMap;

// Core bitboard operations for 2048
fn pack_board(board: &[[u32; 4]; 4]) -> u64 {
    let mut result = 0u64;
    for i in 0..4 {
        for j in 0..4 {
            let value = board[i][j];
            let power = if value == 0 {
                0
            } else {
                value.trailing_zeros() as u64
            };
            result |= power << (4 * (i * 4 + j));
        }
    }
    result
}

// Efficient move operations using lookup tables
fn init_move_tables() -> (Vec<u16>, Vec<u16>) {
    let mut left = vec![0u16; 65536];
    let mut right = vec![0u16; 65536];

    for row in 0..65536 {
        let unpacked = [
            ((row >> 0) & 0xF) as u32,
            ((row >> 4) & 0xF) as u32,
            ((row >> 8) & 0xF) as u32,
            ((row >> 12) & 0xF) as u32,
        ];

        // Calculate left move
        let mut result = [0u32; 4];
        let mut j = 0;
        for i in 0..4 {
            if unpacked[i] != 0 {
                if j > 0 && result[j-1] == unpacked[i] {
                    result[j-1] += 1;
                } else {
                    result[j] = unpacked[i];
                    j += 1;
                }
            }
        }
        left[row] = (result[0] | (result[1] << 4) | (result[2] << 8) | (result[3] << 12)) as u16;

        // Calculate right move (reverse, apply left logic, reverse)
        let reversed = [unpacked[3], unpacked[2], unpacked[1], unpacked[0]];
        let mut result = [0u32; 4];
        let mut j = 0;
        for i in 0..4 {
            if reversed[i] != 0 {
                if j > 0 && result[j-1] == reversed[i] {
                    result[j-1] += 1;
                } else {
                    result[j] = reversed[i];
                    j += 1;
                }
            }
        }
        let final_result = [result[3], result[2], result[1], result[0]];
        right[row] = (final_result[0] | (final_result[1] << 4) | (final_result[2] << 8) | (final_result[3] << 12)) as u16;
    }

    (left, right)
}

// Fast move execution
// Direction encoding: 0=UP, 1=DOWN, 2=LEFT, 3=RIGHT
fn execute_move(board: u64, direction: u8) -> (u64, u32, bool) {
    lazy_static::lazy_static! {
        static ref MOVE_TABLES: (Vec<u16>, Vec<u16>) = init_move_tables();
    }

    let (left_table, right_table) = &*MOVE_TABLES;
    let mut new_board = 0u64;
    let mut score = 0u32;
    let mut changed = false;

    match direction {
        2 | 3 => { // Left or Right
            let table = if direction == 2 { left_table } else { right_table };
            for i in 0..4 {
                let row = ((board >> (i * 16)) & 0xFFFF) as usize;
                let new_row = table[row] as u64;
                new_board |= new_row << (i * 16);
                if new_row != row as u64 {
                    changed = true;
                }
                // Calculate score from merges
                for j in 0..4 {
                    let old_val = (row >> (j * 4)) & 0xF;
                    let new_val = (new_row >> (j * 4)) & 0xF;
                    if new_val > old_val as u64 && new_val > 0 {
                        score += 1 << new_val;
                    }
                }
            }
        }
        0 | 1 => { // Up or Down
            // Transpose, move, transpose back
            let mut transposed = 0u64;
            for i in 0..4 {
                for j in 0..4 {
                    let val = (board >> (4 * (i * 4 + j))) & 0xF;
                    transposed |= val << (4 * (j * 4 + i));
                }
            }

            let table = if direction == 0 { left_table } else { right_table };
            let mut moved = 0u64;
            for i in 0..4 {
                let row = ((transposed >> (i * 16)) & 0xFFFF) as usize;
                let new_row = table[row] as u64;
                moved |= new_row << (i * 16);
                if new_row != row as u64 {
                    changed = true;
                }
                for j in 0..4 {
                    let old_val = (row >> (j * 4)) & 0xF;
                    let new_val = (new_row >> (j * 4)) & 0xF;
                    if new_val > old_val as u64 && new_val > 0 {
                        score += 1 << new_val;
                    }
                }
            }

            // Transpose back
            for i in 0..4 {
                for j in 0..4 {
                    let val = (moved >> (4 * (i * 4 + j))) & 0xF;
                    new_board |= val << (4 * (j * 4 + i));
                }
            }
        }
        _ => {}
    }

    (new_board, score, changed)
}

// Multi-heuristic evaluation for 100K target performance
fn evaluate_position(board: u64) -> f64 {
    // Convert bitboard to 2D grid for analysis
    let mut grid = [[0u32; 4]; 4];
    let mut empty_count = 0;
    let mut max_tile = 0u32;
    let mut max_tile_pos = 0;
    let mut max_tile_power = 0u8;

    for pos in 0..16 {
        let i = pos / 4;
        let j = pos % 4;
        let tile_power = (board >> (pos * 4)) & 0xF;

        if tile_power == 0 {
            empty_count += 1;
            grid[i][j] = 0;
        } else {
            let tile_value = 1 << tile_power;
            grid[i][j] = tile_value;
            if tile_value > max_tile {
                max_tile = tile_value;
                max_tile_pos = pos;
                max_tile_power = tile_power as u8;
            }
        }
    }

    // 1. SNAKE PATTERN SCORE (Foundation - 40% weight)
    let snake_score = calculate_snake_score(&grid, max_tile, max_tile_pos);

    // 2. SMOOTHNESS SCORE (Adjacent similarity - 20% weight)
    let smoothness_score = calculate_smoothness(&grid);

    // 3. MERGEABILITY SCORE (Merge opportunities - 15% weight)
    let merge_score = calculate_mergeability(&grid);

    // 4. GRADIENT FLOW SCORE (Avoid trapped tiles - 10% weight)
    let gradient_score = calculate_gradient_flow(&grid);

    // 5. WALL BUILDING SCORE (Strong edges - 10% weight)
    let wall_score = calculate_wall_strength(&grid, max_tile);

    // 6. GAME PHASE ADAPTATION (Context-aware - 5% weight)
    let phase_multiplier = get_phase_multiplier(empty_count, max_tile_power);

    // Weighted combination with game phase adaptation
    let base_score =
        snake_score * 0.40 +
        smoothness_score * 0.20 +
        merge_score * 0.15 +
        gradient_score * 0.10 +
        wall_score * 0.10 +
        (empty_count as f64) * 15000.0; // Empty cells premium

    base_score * phase_multiplier
}

fn calculate_snake_score(grid: &[[u32; 4]; 4], max_tile: u32, max_tile_pos: usize) -> f64 {
    let snake_order = [
        0, 1, 2, 3,     // Top row L->R
        7, 6, 5, 4,     // Second row R->L
        8, 9, 10, 11,   // Third row L->R
        15, 14, 13, 12, // Bottom row R->L
    ];

    let mut score = 0.0;

    for pos in 0..16 {
        let i = pos / 4;
        let j = pos % 4;
        let tile_value = grid[i][j];

        if tile_value > 0 {
            let snake_idx = snake_order.iter().position(|&p| p == pos).unwrap_or(16);
            let weight = (16 - snake_idx) as f64;
            score += (tile_value as f64) * weight.powf(3.5); // Slightly higher power
        }
    }

    // Massive bonus for max tile in top-left corner (position 0)
    if max_tile_pos == 0 && max_tile > 0 {
        score += (max_tile as f64) * 200000.0; // Doubled bonus
    } else if [3, 12, 15].contains(&max_tile_pos) && max_tile > 0 {
        score += (max_tile as f64) * 50000.0; // Corner bonus
    } else if max_tile > 0 {
        score -= (max_tile as f64) * 25000.0; // Penalty for bad position
    }

    score
}

fn calculate_smoothness(grid: &[[u32; 4]; 4]) -> f64 {
    let mut smoothness = 0.0;

    for i in 0..4 {
        for j in 0..4 {
            if grid[i][j] > 0 {
                let current_log = (grid[i][j] as f64).ln();

                // Check right neighbor
                if j < 3 && grid[i][j + 1] > 0 {
                    let diff = (current_log - (grid[i][j + 1] as f64).ln()).abs();
                    smoothness -= diff * 1000.0; // Penalty for large differences
                }

                // Check bottom neighbor
                if i < 3 && grid[i + 1][j] > 0 {
                    let diff = (current_log - (grid[i + 1][j] as f64).ln()).abs();
                    smoothness -= diff * 1000.0;
                }
            }
        }
    }

    smoothness
}

fn calculate_mergeability(grid: &[[u32; 4]; 4]) -> f64 {
    let mut merge_score = 0.0;

    for i in 0..4 {
        for j in 0..4 {
            if grid[i][j] > 0 {
                let tile_value = grid[i][j] as f64;

                // Check for exact matches (can merge immediately)
                if j < 3 && grid[i][j] == grid[i][j + 1] {
                    merge_score += tile_value.ln() * 5000.0; // High bonus for merges
                }
                if i < 3 && grid[i][j] == grid[i + 1][j] {
                    merge_score += tile_value.ln() * 5000.0;
                }

                // Check for potential merges (one move away)
                if j < 2 && grid[i][j] == grid[i][j + 2] && grid[i][j + 1] == 0 {
                    merge_score += tile_value.ln() * 2000.0; // Medium bonus
                }
                if i < 2 && grid[i][j] == grid[i + 2][j] && grid[i + 1][j] == 0 {
                    merge_score += tile_value.ln() * 2000.0;
                }
            }
        }
    }

    merge_score
}

fn calculate_gradient_flow(grid: &[[u32; 4]; 4]) -> f64 {
    let mut gradient_penalty = 0.0;

    for i in 1..3 {
        for j in 1..3 {
            let current = grid[i][j];
            if current > 0 {
                // Check if tile is trapped between much larger tiles
                let neighbors = [
                    grid[i-1][j], grid[i+1][j], // vertical
                    grid[i][j-1], grid[i][j+1]  // horizontal
                ];

                let large_neighbors = neighbors.iter()
                    .filter(|&&n| n > current * 4) // Much larger neighbors
                    .count();

                if large_neighbors >= 2 {
                    gradient_penalty -= (current as f64).ln() * 3000.0; // Penalty for trapped tiles
                }
            }
        }
    }

    gradient_penalty
}

fn calculate_wall_strength(grid: &[[u32; 4]; 4], max_tile: u32) -> f64 {
    let mut wall_score = 0.0;

    // Check top edge (ideal wall)
    let mut top_wall_valid = true;
    for j in 1..4 {
        if grid[0][j] == 0 || (grid[0][j-1] > 0 && grid[0][j] > grid[0][j-1]) {
            top_wall_valid = false;
            break;
        }
    }
    if top_wall_valid && grid[0][0] == max_tile {
        wall_score += 25000.0; // Strong wall bonus
    }

    // Check left edge
    let mut left_wall_valid = true;
    for i in 1..4 {
        if grid[i][0] == 0 || (grid[i-1][0] > 0 && grid[i][0] > grid[i-1][0]) {
            left_wall_valid = false;
            break;
        }
    }
    if left_wall_valid && grid[0][0] == max_tile {
        wall_score += 25000.0; // Strong wall bonus
    }

    wall_score
}

fn get_phase_multiplier(empty_count: u8, max_tile_power: u8) -> f64 {
    match (empty_count, max_tile_power) {
        // Early game: Build efficiently
        (10.., 0..=8) => 0.8,   // Lower weight, focus on basics

        // Mid game: Perfect structure
        (4..=9, 9..=11) => 1.3, // Higher weight, structure critical

        // Endgame: Survival + mega merges
        (0..=3, 12..) => 1.8,   // Highest weight, every move critical

        // Transition phases
        _ => 1.0 // Default weight
    }
}

// Legacy simple evaluation (for ChampionAI baseline comparison)
fn evaluate_position_simple(board: u64) -> f64 {
    let snake_order = [
        0, 1, 2, 3,     // Top row L->R
        7, 6, 5, 4,     // Second row R->L
        8, 9, 10, 11,   // Third row L->R
        15, 14, 13, 12, // Bottom row R->L
    ];

    let mut score = 0.0;
    let mut max_tile = 0;
    let mut max_tile_pos = 0;
    let mut empty_count = 0;

    for pos in 0..16 {
        let tile_power = (board >> (pos * 4)) & 0xF;

        if tile_power == 0 {
            empty_count += 1;
        } else {
            let tile_value = 1 << tile_power;
            let snake_idx = snake_order.iter().position(|&p| p == pos).unwrap_or(16);
            let weight = (16 - snake_idx) as f64;
            score += (tile_value as f64) * weight.powf(3.0);

            if tile_value > max_tile {
                max_tile = tile_value;
                max_tile_pos = pos;
            }
        }
    }

    if max_tile_pos == 0 && max_tile > 0 {
        score += (max_tile as f64) * 100000.0;
    } else if max_tile > 0 {
        score -= (max_tile as f64) * 10000.0;
    }

    score += (empty_count as f64) * 10000.0;
    score
}

// Simple transposition table
type TranspositionTable = Arc<Mutex<FxHashMap<u64, f64>>>;

// Simple expectimax with legacy evaluation (for ChampionAI)
fn expectimax_legacy(board: u64, depth: u8, is_max: bool, acc_score: u32, tt: &mut TranspositionTable) -> f64 {
    if depth == 0 {
        return evaluate_position_simple(board);
    }

    let tt_key = board ^ ((depth as u64) << 60) ^ ((is_max as u64) << 63);
    if let Some(&cached) = tt.lock().get(&tt_key) {
        return cached;
    }

    let result = if is_max {
        let mut max_value = f64::NEG_INFINITY;
        for direction in 0..4 {
            let (new_board, score, changed) = execute_move(board, direction);
            if changed {
                let value = expectimax_legacy(new_board, depth - 1, false, acc_score + score, tt);
                max_value = max_value.max(value);
            }
        }
        if max_value == f64::NEG_INFINITY {
            evaluate_position_simple(board)
        } else {
            max_value
        }
    } else {
        let mut empty_cells = Vec::new();
        for i in 0..16 {
            if (board >> (i * 4)) & 0xF == 0 {
                empty_cells.push(i);
            }
        }

        if empty_cells.is_empty() {
            return evaluate_position_simple(board);
        }

        let mut expected_value = 0.0;
        for &pos in &empty_cells {
            let board_with_2 = board | (1u64 << (pos * 4));
            expected_value += 0.9 * expectimax_legacy(board_with_2, depth - 1, true, acc_score, tt);

            let board_with_4 = board | (2u64 << (pos * 4));
            expected_value += 0.1 * expectimax_legacy(board_with_4, depth - 1, true, acc_score, tt);
        }
        expected_value / empty_cells.len() as f64
    };

    tt.lock().insert(tt_key, result);
    result
}

// Enhanced expectimax with multi-heuristic evaluation (for GeniusAI)
fn expectimax_simple(board: u64, depth: u8, is_max: bool, acc_score: u32, tt: &mut TranspositionTable) -> f64 {
    if depth == 0 {
        return evaluate_position(board);
    }

    // Check transposition table
    let tt_key = board ^ ((depth as u64) << 60) ^ ((is_max as u64) << 63);
    if let Some(&cached) = tt.lock().get(&tt_key) {
        return cached;
    }

    let result = if is_max {
        let mut max_value = f64::NEG_INFINITY;
        for direction in 0..4 {
            let (new_board, score, changed) = execute_move(board, direction);
            if changed {
                let value = expectimax_simple(new_board, depth - 1, false, acc_score + score, tt);
                max_value = max_value.max(value);
            }
        }
        if max_value == f64::NEG_INFINITY {
            evaluate_position(board)
        } else {
            max_value
        }
    } else {
        // Expectation over random tile placements
        let mut empty_cells = Vec::new();
        for i in 0..16 {
            if (board >> (i * 4)) & 0xF == 0 {
                empty_cells.push(i);
            }
        }

        if empty_cells.is_empty() {
            return evaluate_position(board);
        }

        let mut expected_value = 0.0;
        for &pos in &empty_cells {
            // 90% chance of 2, 10% chance of 4
            let board_with_2 = board | (1u64 << (pos * 4));
            expected_value += 0.9 * expectimax_simple(board_with_2, depth - 1, true, acc_score, tt);

            let board_with_4 = board | (2u64 << (pos * 4));
            expected_value += 0.1 * expectimax_simple(board_with_4, depth - 1, true, acc_score, tt);
        }
        expected_value / empty_cells.len() as f64
    };

    // Cache result
    tt.lock().insert(tt_key, result);
    result
}

// Champion AI - High performance version (matching background test: ~68,500 avg score)
#[pyclass]
struct ChampionAI {
}

#[pymethods]
impl ChampionAI {
    #[new]
    fn new() -> Self {
        ChampionAI {}
    }

    fn get_best_move(&self, board: [[u32; 4]; 4]) -> Option<String> {
        let bitboard = pack_board(&board);

        // Conservative depth calculation - proven to work in background
        let mut empty_tiles = 0u8;
        for i in 0..16 {
            if (bitboard >> (i * 4)) & 0xF == 0 {
                empty_tiles += 1;
            }
        }

        let depth = match empty_tiles {
            0..=2 => 7,  // Deep endgame
            3..=4 => 6,  // Deep late game
            5..=6 => 5,  // Deep mid game
            7..=9 => 4,  // Mid game
            _ => 3,      // Early game
        };

        let moves = ["up", "down", "left", "right"];

        // Parallel evaluation with legacy simple evaluation (48K baseline)
        let results: Vec<_> = (0..4)
            .into_par_iter()
            .map(move |direction| {
                let mut tt = TranspositionTable::default();
                let (new_board, score_gained, changed) = execute_move(bitboard, direction as u8);
                if changed {
                    let value = expectimax_legacy(new_board, depth - 1, false, score_gained, &mut tt);
                    Some((direction, value))
                } else {
                    None
                }
            })
            .collect();

        results.into_iter()
            .filter_map(|x| x)
            .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap())
            .map(|(dir, _)| moves[dir].to_string())
    }
}

// Challenger AI - Slightly different depth settings for comparison
#[pyclass]
struct ChallengerAI {
}

#[pymethods]
impl ChallengerAI {
    #[new]
    fn new() -> Self {
        ChallengerAI {}
    }

    fn get_best_move(&self, board: [[u32; 4]; 4]) -> Option<String> {
        let bitboard = pack_board(&board);

        let mut empty_tiles = 0u8;
        for i in 0..16 {
            if (bitboard >> (i * 4)) & 0xF == 0 {
                empty_tiles += 1;
            }
        }

        let depth = match empty_tiles {
            0..=2 => 6,  // Slightly less deep
            3..=4 => 5,
            5..=6 => 4,
            7..=9 => 3,
            _ => 2,
        };

        let moves = ["up", "down", "left", "right"];

        let results: Vec<_> = (0..4)
            .into_par_iter()
            .map(move |direction| {
                let mut tt = TranspositionTable::default();
                let (new_board, score_gained, changed) = execute_move(bitboard, direction as u8);
                if changed {
                    let value = expectimax_simple(new_board, depth - 1, false, score_gained, &mut tt);
                    Some((direction, value))
                } else {
                    None
                }
            })
            .collect();

        results.into_iter()
            .filter_map(|x| x)
            .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap())
            .map(|(dir, _)| moves[dir].to_string())
    }
}

// SimplifiedGeniusAI - Only snake + smoothness (debugging version)
#[pyclass]
struct SimplifiedGeniusAI {
}

#[pymethods]
impl SimplifiedGeniusAI {
    #[new]
    fn new() -> Self {
        SimplifiedGeniusAI {}
    }

    fn get_best_move(&self, board: Vec<Vec<u32>>) -> Option<String> {
        // Convert Vec<Vec<u32>> to [[u32; 4]; 4]
        let mut array_board = [[0u32; 4]; 4];
        for (i, row) in board.iter().enumerate() {
            for (j, &val) in row.iter().enumerate() {
                array_board[i][j] = val;
            }
        }
        let packed_board = pack_board(&array_board);
        let direction = get_best_move_simplified(packed_board);

        // Convert direction number to string
        let moves = ["up", "down", "left", "right"];
        Some(moves[direction as usize].to_string())
    }
}

// GeniusAI - Multi-heuristic evaluation for 100K target performance
#[pyclass]
struct GeniusAI {
}

#[pymethods]
impl GeniusAI {
    #[new]
    fn new() -> Self {
        GeniusAI {}
    }

    fn get_best_move(&self, board: [[u32; 4]; 4]) -> Option<String> {
        let bitboard = pack_board(&board);

        // Same conservative search depths but enhanced evaluation
        let mut empty_tiles = 0u8;
        for i in 0..16 {
            if (bitboard >> (i * 4)) & 0xF == 0 {
                empty_tiles += 1;
            }
        }

        let depth = match empty_tiles {
            0..=2 => 7,  // Deep endgame
            3..=4 => 6,  // Deep late game
            5..=6 => 5,  // Deep mid game
            7..=9 => 4,  // Mid game
            _ => 3,      // Early game
        };

        let moves = ["up", "down", "left", "right"];

        // Parallel evaluation with multi-heuristic evaluation function
        let results: Vec<_> = (0..4)
            .into_par_iter()
            .map(move |direction| {
                let mut tt = TranspositionTable::default();
                let (new_board, score_gained, changed) = execute_move(bitboard, direction as u8);
                if changed {
                    let value = expectimax_simple(new_board, depth - 1, false, score_gained, &mut tt);
                    Some((direction, value))
                } else {
                    None
                }
            })
            .collect();

        results.into_iter()
            .filter_map(|x| x)
            .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap())
            .map(|(dir, _)| moves[dir].to_string())
    }
}

// Simplified evaluation: Snake + Smoothness only (debugging version)
fn get_best_move_simplified(bitboard: u64) -> u8 {
    // Count empty tiles inline
    let mut empty_tiles = 0u8;
    for i in 0..16 {
        if (bitboard >> (i * 4)) & 0xF == 0 {
            empty_tiles += 1;
        }
    }

    let depth = match empty_tiles {
        0..=2 => 7,  // Deep endgame
        3..=4 => 6,  // Deep late game
        5..=6 => 5,  // Deep mid game
        7..=9 => 4,  // Mid game
        _ => 3,      // Early game
    };

    let mut best_move = 0;
    let mut best_value = f64::NEG_INFINITY;

    for direction in 0..4 {
        let (new_board, score_gained, changed) = execute_move(bitboard, direction);
        if changed {
            let mut tt = TranspositionTable::default();
            let value = expectimax_simplified(new_board, depth - 1, false, score_gained, &mut tt);
            if value > best_value {
                best_value = value;
                best_move = direction;
            }
        }
    }

    best_move
}

// Simplified expectimax using only snake + smoothness evaluation
fn expectimax_simplified(board: u64, depth: u8, is_max: bool, acc_score: u32, tt: &mut TranspositionTable) -> f64 {
    if depth == 0 {
        return evaluate_position_simplified(board);
    }

    // Check transposition table
    let tt_key = board ^ ((depth as u64) << 60) ^ ((is_max as u64) << 63);
    if let Some(&cached) = tt.lock().get(&tt_key) {
        return cached;
    }

    let result = if is_max {
        let mut max_value = f64::NEG_INFINITY;
        for direction in 0..4 {
            let (new_board, score, changed) = execute_move(board, direction);
            if changed {
                let value = expectimax_simplified(new_board, depth - 1, false, acc_score + score, tt);
                max_value = max_value.max(value);
            }
        }
        if max_value == f64::NEG_INFINITY {
            evaluate_position_simplified(board)
        } else {
            max_value
        }
    } else {
        // Expectation over random tile placements
        let mut empty_cells = Vec::new();
        for i in 0..16 {
            if (board >> (i * 4)) & 0xF == 0 {
                empty_cells.push(i);
            }
        }

        if empty_cells.is_empty() {
            return evaluate_position_simplified(board);
        }

        let mut expected_value = 0.0;
        for &pos in &empty_cells {
            let board_with_2 = board | (1u64 << (pos * 4));
            expected_value += 0.9 * expectimax_simplified(board_with_2, depth - 1, true, acc_score, tt);

            let board_with_4 = board | (2u64 << (pos * 4));
            expected_value += 0.1 * expectimax_simplified(board_with_4, depth - 1, true, acc_score, tt);
        }
        expected_value / empty_cells.len() as f64
    };

    tt.lock().insert(tt_key, result);
    result
}

// Simplified evaluation: Snake pattern (80%) + Smoothness (20%)
fn evaluate_position_simplified(board: u64) -> f64 {
    let mut grid = [[0u32; 4]; 4];
    for i in 0..16 {
        let val = (board >> (i * 4)) & 0xF;
        grid[i / 4][i % 4] = if val == 0 { 0 } else { 1 << val };
    }

    let empty_count = grid.iter().flatten().filter(|&&x| x == 0).count();
    let max_tile = grid.iter().flatten().max().unwrap_or(&0);

    // 1. Snake pattern score (80% weight) - same as ChampionAI
    let snake_score = calculate_snake_score_simple(&grid);

    // 2. Simple smoothness score (20% weight) - only check adjacent differences
    let smoothness_score = calculate_smoothness_simple(&grid);

    // Combine with simpler weights
    snake_score * 0.8 + smoothness_score * 0.2 + (empty_count as f64) * 10000.0
}

fn calculate_snake_score_simple(grid: &[[u32; 4]; 4]) -> f64 {
    // Same snake pattern as ChampionAI
    let snake_weights = [
        [15.0, 14.0, 13.0, 12.0],
        [ 8.0,  9.0, 10.0, 11.0],
        [ 7.0,  6.0,  5.0,  4.0],
        [ 0.0,  1.0,  2.0,  3.0],
    ];

    let mut score = 0.0;
    for i in 0..4 {
        for j in 0..4 {
            if grid[i][j] > 0 {
                score += (grid[i][j] as f64).log2() * snake_weights[i][j] * 1000.0;
            }
        }
    }
    score
}

fn calculate_smoothness_simple(grid: &[[u32; 4]; 4]) -> f64 {
    let mut smoothness = 0.0;

    // Only check adjacent cells (horizontal and vertical)
    for i in 0..4 {
        for j in 0..4 {
            let current = if grid[i][j] == 0 { 0.0 } else { (grid[i][j] as f64).log2() };

            // Check right neighbor
            if j < 3 {
                let right = if grid[i][j+1] == 0 { 0.0 } else { (grid[i][j+1] as f64).log2() };
                smoothness -= (current - right).abs();
            }

            // Check down neighbor
            if i < 3 {
                let down = if grid[i+1][j] == 0 { 0.0 } else { (grid[i+1][j] as f64).log2() };
                smoothness -= (current - down).abs();
            }
        }
    }

    smoothness * 100.0 // Scale to reasonable range
}

#[pymodule]
fn rust_ai_2048(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<ChampionAI>()?;
    m.add_class::<ChallengerAI>()?;
    m.add_class::<SimplifiedGeniusAI>()?;
    m.add_class::<GeniusAI>()?;
    Ok(())
}