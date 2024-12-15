from itertools import product
from sortedcontainers import SortedSet
import sys
import time
import os

TRANSITABLE = 0
GRIS = 1
AMARILLA = 2


MOVIMIENTOS = {
    'arriba': (-1, 0),
    'izquierda': (0, -1),
    'abajo': (1, 0),
    'derecha': (0, 1),
    'esperar': (0, 0)  # Esperar
}


def obtain_data(path):
    print(path)
    with open(path, 'r') as f:
        data_lines = f.readlines()

    # leer num aviones
    planes_number = int(data_lines[0].strip())
    initial_planes_positions = {}
    final_planes_positions = {}
    # leer posiciones
    i = 0
    for line in data_lines[1:planes_number+1]:
        line_explited = line.strip().split(" ")

        initial_planes_positions[f"plane_{i}"] = eval(line_explited[0])
        final_planes_positions[f"plane_{i}"] = eval(line_explited[1])
        i += 1
    # leer mapa
    lineas_mapa = data_lines[planes_number+1:]
    map_grid = []
    for line in lineas_mapa:
        row = line.split(';')
        row_cells = []
        for cell in row:
            cell = cell.strip()
            if cell == 'B':
                row_cells.append(TRANSITABLE)
            elif cell == 'G':
                row_cells.append(GRIS)
            elif cell == 'A':
                row_cells.append(AMARILLA)

        map_grid.append(row_cells)

    print(planes_number, initial_planes_positions, final_planes_positions)
    print(map_grid)

    return map_grid, planes_number, initial_planes_positions, final_planes_positions


class State:

    def __init__(self, state_configuration, time=0, parent=None, heur_number=1, final_state=None):
        self.state_configuration = state_configuration
        self.time = time
        self.heur = 0
        self.parent = parent
        self.heur_number = heur_number
        self.final_state = final_state
        self._calculate_heuristic()

    # permite hacer comprobaciones de igualdad entre objetos
    # def __eq__(self, other):
    #     if not isinstance(other, State):
    #         return False
    #     print("-------------------------------------")
    #     print(self._extract_positions())
    #     print(other._extract_positions())
    #     return self._extract_positions() == other._extract_positions()

    def _calculate_heuristic(self):

        if not self.heur_number or self.heur_number == 0 or self.final_state == None:
            return 0

        # posiciones finales de los aviones
        final_positions = {plane: info["position"] for plane,
                           info in self.final_state.state_configuration.items()}

        if self.heur_number == 1:
            # Máximo entre las distancias Manhattan de los aviones
            # Máximo entre las distancias Manhattan de los aviones
            max_distance = 0
            for plane, info in self.state_configuration.items():
                current_position = info["position"]
                final_position = final_positions[plane]
                distance = abs(
                    current_position[0] - final_position[0]) + abs(current_position[1] - final_position[1])
                if distance > max_distance:
                    max_distance = distance
            self.heur = max_distance

        elif self.heur_number == 2:
            # Cada avión que no esté en su estado final suma 1
            count = 0
            for plane, info in self.state_configuration.items():
                if info["position"] != final_positions[plane]:
                    count += 1
            self.heur = count

        elif self.heur_number == 3:
            # implementa la distancia de manhattan, resta 2 por cada avión que esté en la posicion final
            total_distance = 0
            final_count = 0
            for plane, info in self.state_configuration.items():
                current_position = info["position"]
                final_position = final_positions[plane]
                distance = abs(
                    current_position[0] - final_position[0]) + abs(current_position[1] - final_position[1])
                total_distance += distance
                if current_position == final_position:
                    final_count += 1
            self.heur = total_distance - (2 * final_count)
            if self.heur < 0:
                self.heur = 0
            # si el valor es menor que 0, entonces retornar 0xº

        elif self.heur_number == 4:
            # distancia de manhattan menos  0.1 * distancia_i_j
            total_manhattan = 0
            for plane, info in self.state_configuration.items():
                current_position = info["position"]
                final_position = final_positions[plane]
                distance = abs(
                    current_position[0] - final_position[0]) + abs(current_position[1] - final_position[1])
                total_manhattan += distance

            # Penalización por proximidad
            total_proximity_penalty = 0
            planes = list(self.state_configuration.keys())
            for i in range(len(planes)):
                for j in range(i + 1, len(planes)):
                    plane_i_pos = self.state_configuration[planes[i]
                                                           ]["position"]
                    plane_j_pos = self.state_configuration[planes[j]
                                                           ]["position"]
                    distance = abs(
                        plane_i_pos[0] - plane_j_pos[0]) + abs(plane_i_pos[1] - plane_j_pos[1])
                    total_proximity_penalty += 0.001 * distance

            self.heur = total_manhattan - total_proximity_penalty

            if self.heur < 0:
                self.heur = 0

    def __eq__(self, other):
        # permite comparar que dos estados son iguales, solo tiene en cuenta las posiciones de los aviones
        if not isinstance(other, State):
            return False
        return self._get_ordered_positions() == other._get_ordered_positions()

    def __hash__(self):
        # es necesario para poder meter los estados en sets
        return hash(self._get_ordered_positions())

    def _get_ordered_positions(self):

        items = self.state_configuration.items()
        return tuple((plane, info["position"]) for plane, info in items)

    def __lt__(self, other):
        # permite comparar  con < dos estados,solo tiene en cuenta las posiciones de los aviones
        return (self.heur, self._get_ordered_positions()) > (other.heur, other._get_ordered_positions())

    def __repr__(self):
        return f"State({self.state_configuration}, heur={self.heur})"


def expand_state(state, map_grid):
    # Esta funcion expande los estados a partir de un estado
    succesors = []
    # calculamos todas las posibles acciones para cada avión
    all_actions = {}
    for plane, info_plane_current_state in state.state_configuration.items():
        current_x = info_plane_current_state["position"][0]
        current_y = info_plane_current_state["position"][1]
        all_actions_per_plane = []
        for action_name, action_values in MOVIMIENTOS.items():
            new_x = current_x + action_values[0]
            new_y = current_y + action_values[1]

            if 0 <= new_x < len(map_grid) and 0 <= new_y < len(map_grid[0]):

                type_cell = map_grid[new_x][new_y]

                if type_cell == GRIS:
                    continue
                else:

                    if type_cell == AMARILLA and action_name == "esperar":
                        continue
                    else:
                        all_actions_per_plane.append(
                            {"action_name": action_name, "position": (new_x, new_y)})

        all_actions[plane] = all_actions_per_plane

    # hallamos todas las combinaciones de dichas acciones
    # el asterisco convierte el arrat de arrays en [],[]...
    all_combinations_of_actions = list(product(*all_actions.values()))

    # eliminamos los estados no válidos
    for set_of_actions_new_pos in all_combinations_of_actions:
        # set_of_actions es una tupla que contine para cada avion una accion de forma ordenada
        if check_valid_state(state, set_of_actions_new_pos):
            next_poss = {}
            for idx, action_pos in enumerate(set_of_actions_new_pos):
                next_poss[f"plane_{idx}"] = action_pos

            succesors.append(State(next_poss, state.time+1,
                             state, state.heur_number, state.final_state))

    # print("Generated Successor States:")
    # for idx, successor in enumerate(succesors):
    #     print(f"Successor {idx + 1}:")
    #     print(f"Heur {successor.heur}:")
    #     print(f"  Time: {successor.time}")
    #     for plane, plane_info in successor.state_configuration.items():
    #         print(
    #             f"    {plane}: Action={plane_info['action_name']}, Position={plane_info['position']}")
    #     print("-" * 40)

    return succesors


def check_valid_state(current_state, set_of_actions_new_pos):
    # Esta funcion comprueba que un estado es valido

    occupied_pos = set([])
    # check for two planes in same positions
    for action_pos in set_of_actions_new_pos:

        new_position = action_pos["position"]
        if new_position not in occupied_pos:
            occupied_pos.add(new_position)
        else:
            return False

    for i, action_pos in enumerate(set_of_actions_new_pos):
        pos_i_state = current_state.state_configuration[f"plane_{i}"]["position"]
        # print(current_state)
        pos_i_next = action_pos["position"]
        for j in range(i+1, len(set_of_actions_new_pos)):
            pos_j_state = current_state.state_configuration[f"plane_{j}"]["position"]
            pos_j_next = set_of_actions_new_pos[j]["position"]

            # print("DEBUG----------------------")
            # print(pos_i_state, pos_j_next, pos_j_state, pos_i_next)
            if pos_i_state == pos_j_next and pos_j_state == pos_i_next:
                return False
    return True


def reconstruct_path(state):
    # Reconstruye el camino dandole la vuelta
    path = []
    while state is not None:
        path.append(state)
        state = state.parent
    path.reverse()
    return path

# Funcion para escribir las estadisticas


def write_stats(total_time, makespan, h_initial, nodes_expanded, output_stats_path):
    with open(output_stats_path, 'w') as f:
        f.write(f"Tiempo total: {total_time:.2f}s\n")
        f.write(f"Makespan: {makespan}\n")
        f.write(f"h inicial: {h_initial}\n")
        f.write(f"Nodos expandidos: {nodes_expanded}\n")


# Funcion para escribir las soluciones de los aviones
def write_solution(path, output_solution_path, initial_planes_positions):
    planes = list(initial_planes_positions.keys())
    plane_movements = {plane: [] for plane in planes}
    for state in path:
        for plane in planes:
            position = state.state_configuration[plane]["position"]
            action = state.state_configuration[plane].get("action_name", None)
            plane_movements[plane].append((position, action))
    with open(output_solution_path, 'w', encoding='utf-8') as f:
        for plane in planes:
            movements = plane_movements[plane]
            movement_strings = []
            for i in range(len(movements)):
                position, action = movements[i]
                if i == 0:
                    movement_strings.append(f"{position}")
                else:
                    if action == 'esperar':
                        movement_strings.append(f"W {position}")
                    elif action == "arriba":
                        movement_strings.append(f"↑ {position}")
                    elif action == "abajo":
                        movement_strings.append(f"↓ {position}")
                    elif action == "derecha":
                        movement_strings.append(f"→ {position}")
                    elif action == "izquierda":
                        movement_strings.append(f"← {position}")

            line = ' '.join(movement_strings)
            f.write(line + "\n")


def a_start_implementation(initial_state: State, final_state: State, map_grid):
    EXPANDED_NODES = 0
    EXPANDED_NODES += 1
    # sortedSet utiliza una sorted list para el orden y un set para el retrieval
    abierta = SortedSet([])
    abierta.add(initial_state)
    cerrada = set([])
    exito = False
    sol = None
    i = 0
    # Hasta que abierta esta vacia O EXITO
    while len(abierta) > 0 and not exito:
        # quitar el primer nodo de abierta
        # print all nodes heur values in abierta
        # print("Heuristic values of nodes in abierta:")
        # for node in abierta:
        #     print(f"Node Heuristic Value: {node.heur}")
        # print("-" * 40)
        nodo_actual = abierta.pop()
        # print("Nodo_escogido huer: ", nodo_actual.heur)
        # i += 1
        # if i > 7:
        #     exit()
        if nodo_actual == final_state:
            print("WE HAVE REACH FINAL STATE")
            exito = True
            sol = nodo_actual
        else:
            # meter en cerrada
            cerrada.add(nodo_actual)
            # expandir
            sucesores = expand_state(nodo_actual, map_grid)

            EXPANDED_NODES += len(sucesores)

            for s in sucesores:
                if s not in abierta and s not in cerrada:
                    abierta.add(s)
                elif s in abierta:
                    # find item
                    # print(s in abierta)
                    # print(s)
                    # for i in abierta:
                    #     print(i)
                    # print("AAAAAAAAAAAAAAAAAAAAAAA")
                    index_already = abierta.index(s)
                    already_s = abierta[index_already]

                    if s.heur < already_s.heur:
                        abierta.discard(already_s)
                        abierta.add(s)
                elif s in cerrada:
                    pass
    if exito:
        print("La solucion es: ", sol)
        return sol, EXPANDED_NODES
    else:
        print("no existe solucion")
        return None, EXPANDED_NODES
# obtain_data("./pruebas_busq/prueba.csv")


if __name__ == "__main__":

    # Verificar si el número de argumentos es correcto
    if len(sys.argv) != 3:
        print("Falta <path mapa.csv> p <num-h>")
        sys.exit(1)
    map_path = sys.argv[1]
    heuristic_number = int(sys.argv[2])

    map_grid, planes_number, initial_planes_positions, final_planes_positions = obtain_data(
        map_path)

    start_time = time.time()
    # create initial state with heur = 0
    initial_state_configuration = {}
    for plane, position in initial_planes_positions.items():
        initial_state_configuration[plane] = {
            "position": position, "action": None}

    # create final state with heur = 0
    final_state_configuration = {}
    for plane, position in final_planes_positions.items():
        final_state_configuration[plane] = {
            "position": position, "action": None}

    final_state = State(final_state_configuration,
                        0, None, heuristic_number, None)

    initial_state = State(initial_state_configuration,
                          0, None, heuristic_number, final_state)

    final_node_solution, EXPANDED_NODES = a_start_implementation(
        initial_state, final_state, map_grid)

    input_filename = os.path.basename(map_path)
    input_name = input_filename.split(".")[0]
    output_dir = os.path.dirname(map_path)
    output_solution_path = f"./ASTAR_test/{input_name}-{heuristic_number}.output"
    output_stats_path = f"./ASTAR_test/{input_name}-{heuristic_number}.stat"
    end_time = time.time()
    total_time = end_time - start_time
    initial_heur_val = initial_state.heur
    if final_node_solution:

        path = reconstruct_path(final_node_solution)
        makespan = final_node_solution.time

        write_solution(path, output_solution_path,
                       initial_planes_positions)
        write_stats(total_time, makespan, initial_heur_val,
                    EXPANDED_NODES, output_stats_path)

        print(f"Total time: {total_time}, expanded: {EXPANDED_NODES}")

    else:

        # Write "no solution" in the output solution file
        with open(output_solution_path, 'w', encoding='utf-8') as f:
            f.write("No solution found.\n")

        # Write stats with placeholders for "no solution"
        with open(output_stats_path, 'w') as f:
            f.write(f"Tiempo total: {total_time:.2f}s\n")
            f.write("Makespan: N/A\n")
            f.write("h inicial: {initial_heur_val}\n")
            f.write(f"Nodos expandidos: {EXPANDED_NODES}\n")

        print(
            f"No solution found. Total time: {total_time}, expanded: {EXPANDED_NODES}")
