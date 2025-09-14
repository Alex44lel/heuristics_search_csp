# Heuristics Search & CSP - Aircraft Operations

This repository contains two main components for solving aircraft operations problems using different AI techniques:

## Overview

- **Part 1 - CSP (Constraint Satisfaction Problem)**: Aircraft maintenance scheduling
- **Part 2 - A\* Search Algorithm**: Aircraft routing and taxiing pathfinding

## Requirements

- Python 3.6+
- Required packages:
  ```bash
  pip install python-constraint sortedcontainers
  ```

## Part 1: Aircraft Maintenance Scheduling (CSP)

Solves aircraft maintenance scheduling problems using constraint satisfaction.

### Usage
```bash
cd parte-1
python CSPMaintenance.py <input_file>
```

### Example
```bash
python CSPMaintenance.py CSP_test/manteinance1.txt
```

### Input Format
```
Franjas: <number_of_time_slots>
<rows>x<columns>
STD:<pos1> <pos2> ...
SPC:<pos1> <pos2> ...
PRK:<pos1> <pos2> ...
<aircraft_data_lines>
```

### Output
- Generates CSV files with all possible solutions
- Shows assignments of aircraft to maintenance positions over time slots

## Part 2: Aircraft Routing (A* Search)

Finds optimal paths for aircraft movement on airport grounds using A* algorithm.

### Usage
```bash
cd parte-2
python ASTARRodaje.py <map_file> <heuristic_type>
```

### Example
```bash
python ASTARRodaje.py ASTAR_test/mapa0.csv 4
```

### Input Format
```
<number_of_planes>
<initial_pos> <final_pos>
<initial_pos> <final_pos>
...
<grid_map_with_semicolon_separated_cells>
```

### Map Legend
- `B`: Transitable area
- `G`: Gray area (obstacle)
- `A`: Yellow area (obstacle)

### Output
- Shows the optimal path solution
- Displays execution time and number of expanded nodes

## Running All Tests

```bash
# CSP tests
cd parte-1
python CSPMaintenance.py CSP_test/manteinance1.txt
python CSPMaintenance.py CSP_test/manteinance2.txt
# ... (add more as needed)

# A* tests
cd parte-2
python ASTARRodaje.py ASTAR_test/mapa0.csv 4
python ASTARRodaje.py ASTAR_test/mapa1.csv 4
# ... (add more as needed)
```

## Project Structure
```
├── parte-1/           # CSP aircraft maintenance scheduling
│   ├── CSPMaintenance.py
│   ├── CSP_test/      # Test input files
│   └── CSP-calls.bat  # Windows batch runner
├── parte-2/           # A* aircraft routing
│   ├── ASTARRodaje.py  
│   ├── ASTAR_test/    # Test map files
│   └── ASTAR-calls.bat # Windows batch runner
└── requirements.txt   # Python dependencies
```

