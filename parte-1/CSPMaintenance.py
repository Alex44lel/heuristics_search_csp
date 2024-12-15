import sys
import os
import csv
from constraint import *
import time


def generate_csv(solutions, file_path, planes, numero_franjas, matriz_airport):
    output_file = f"{os.path.splitext(file_path)[0]}.csv"

    with open(output_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([f"N. Sol: {len(solutions)}"])
        for idx, solution in enumerate(solutions):
            writer.writerow([f"Solucion {idx + 1}:"])
            for plane in planes:
                plane_id = plane["full_name"]
                assignments = []
                for n in range(numero_franjas):
                    variable_name = f"P{planes.index(plane)}_T{n}"
                    pos = solution[variable_name]
                    assignments.append(
                        f"{matriz_airport[pos[0]][pos[1]]}({pos[0]},{pos[1]})"
                    )
                writer.writerow([f"{plane_id}: " + ", ".join(assignments)])

    print(f"Output written to {output_file}")


def obtain_data(path):
    print(path)
    with open(path, 'r') as f:
        data_lines = f.readlines()

    numero_franjas = int(data_lines[0].strip().split(" ")[1])

    matriz_dim_n, matriz_dim_m = data_lines[1].strip().split("x")
    matriz_dim_n = int(matriz_dim_n)
    matriz_dim_m = int(matriz_dim_m)

    talleres_std = []
    print(data_lines[2].strip().split(" "))
    print("HI")
    for i, tup in enumerate(data_lines[2].strip().split(" ")):
        if i == 0:
            tup = tup.split(":")
            print(tup)
            if tup[1] != "":
                tup = tup[1].strip()
            else:
                break
        talleres_std.append(eval(tup))

    talleres_scp = []
    for i, tup in enumerate(data_lines[3].strip().split(" ")):
        if i == 0:
            tup = tup.split(":")
            if tup[1] != "":
                tup = tup[1].strip()
            else:
                break

        talleres_scp.append(eval(tup))

    parkings = []
    for i, tup in enumerate(data_lines[4].strip().split(" ")):
        if i == 0:
            tup = tup.split(":")
            if tup[1] != "":
                tup = tup[1].strip()
            else:
                break
        parkings.append(eval(tup))

    print(numero_franjas, matriz_dim_n, matriz_dim_m,
          talleres_std, talleres_scp, parkings)

    matriz_airport = [[0 for _ in range(matriz_dim_m)]
                      for _ in range(matriz_dim_n)]

    for x, y in talleres_std:
        matriz_airport[x][y] = "STD"
    for x, y in talleres_scp:
        matriz_airport[x][y] = "SCP"
    for x, y in parkings:
        matriz_airport[x][y] = "PARKING"

    planes = []

    for line in data_lines[5:]:

        full_name = line.strip()
        data_plane = line.strip().split("-"
                                        )
        avion = {
            "full_name": full_name,
            "id": data_plane[0],
            "type": data_plane[1],
            "order": data_plane[2] == 'T',
            "t1": int(data_plane[3]),
            "t2": int(data_plane[4])
        }

        planes.append(avion)
    print(matriz_airport)

    print(planes)
    return numero_franjas, matriz_dim_n, matriz_dim_m, matriz_airport, planes


def main():
    start_time = time.time()

    problem = Problem()

    file_path = sys.argv[1]

    numero_franjas, matriz_dim_n, matriz_dim_m, matriz_airport, planes = obtain_data(
        file_path)

    # Lista de posiciones válidas
    valid_positions = [
        (x, y) for x in range(matriz_dim_n) for y in range(matriz_dim_m) if matriz_airport[x][y] != 0
    ]
    for i, plane in enumerate(planes):
        for n in range(numero_franjas):
            variable_name = f"P{i}_T{n}"
            problem.addVariable(variable_name, valid_positions)

    print("\nProblem variables added:")
    constraints_start_time = time.time()

    # CONSTRAINT_1, todo avión ha de tener un parking/taller asignado en cada franja horaria
    # esta implicita en la definicion con lo cual no la usamos
    def have_one_assigment_per_time_slot(*valores_variables):
        for pos in valores_variables:
            if pos not in valid_positions:
                return False
        return True

    # CONSTRAINT_2 cada taller puede atender hasta 2 aviones en una franja,
    def dos_aviones_por_taller(*valores_variables):
        count = {}
        for plane_var_ass in valores_variables:
            if matriz_airport[plane_var_ass[0]][plane_var_ass[1]] != "PARKING":
                if str(plane_var_ass) in count:
                    count[str(plane_var_ass)] += 1

                else:
                    count[str(plane_var_ass)] = 1

            if str(plane_var_ass) in count and count[str(plane_var_ass)] > 2:
                return False

        # print(count)
        return True

    # CONSTRAINT 3 nunca puede haber más de un avión JUMBO en un mismo taller
    def un_jumbo_por_taller(*valores_variables):
        count_jumbo_each_pos = {}
        for i, plane_var_ass in enumerate(valores_variables):
            plane_type = planes[i]["type"]
            if plane_type == "JMB":  # and plane_var_ass != 0
                if str(plane_var_ass) in count_jumbo_each_pos:
                    count_jumbo_each_pos[str(plane_var_ass)] += 1
                else:
                    count_jumbo_each_pos[str(plane_var_ass)] = 1

            if str(plane_var_ass) in count_jumbo_each_pos and count_jumbo_each_pos[str(plane_var_ass)] > 1:
                return False

        return True

    for n in range(numero_franjas):
        variables_franja = [f"P{i}_T{n}" for i in range(len(planes))]
        problem.addConstraint(dos_aviones_por_taller, variables_franja)
        problem.addConstraint(un_jumbo_por_taller, variables_franja)

    # CONSTRAINT 4 Si un avión tiene asignadas N tareas especialistas, deberá de tener asignados n talleres especialistas en n franjas
    def enough_scp_assignments(*valores_variables, plane_index):
        plane = planes[plane_index]
        t2_tasks = plane["t2"]
        scp_count = 0
        for pos in valores_variables:
            if matriz_airport[pos[0]][pos[1]] == "SCP":
                scp_count += 1
        return scp_count >= t2_tasks

    for i, plane in enumerate(planes):
        same_plane_all_time_slots = []
        for n in range(numero_franjas):
            same_plane_all_time_slots.append(f"P{i}_T{n}")

        def enough_scp_assignments_with_plane_index(*valores_variables, plane_index=i):
            return enough_scp_assignments(*valores_variables, plane_index=plane_index)

        problem.addConstraint(enough_scp_assignments_with_plane_index,
                              same_plane_all_time_slots)

    # Constraint 5: Orden de tareas en aviones que lo requieran
    def t2_before_t1(*valores_variables, plane_index):
        plane = planes[plane_index]
        t2_tasks = plane["t2"]

        scp_count = 0
        i = 0
        while i < len(valores_variables) and scp_count < t2_tasks:
            pos = valores_variables[i]
            if matriz_airport[pos[0]][pos[1]] == "SCP":
                scp_count += 1

            if matriz_airport[pos[0]][pos[1]] == "STD" and scp_count < t2_tasks:

                return False
            i += 1
        if scp_count < t2_tasks:
            return False

        return True

    for i, plane in enumerate(planes):
        if planes[i]["order"] and planes[i]["t2"] > 0:
            same_plane_all_time_slots = []
            for n in range(numero_franjas):
                same_plane_all_time_slots.append(f"P{i}_T{n}")

        def t2_before_t1_with_plane_index(*valores_variables, plane_index=i):
            return t2_before_t1(*valores_variables, plane_index=plane_index)

        problem.addConstraint(t2_before_t1_with_plane_index,
                              same_plane_all_time_slots)

    # Constraint_6: Un avión con x tareas (t1+t2) ha de tener como mínimo x talleres asignados
    def cover_all_tasks(*valores_variables, plane_index):
        plane = planes[plane_index]
        total_tasks = plane["t1"] + plane["t2"]

        # Count all valid workshop assignments
        assigned_workshops = sum(
            1 for pos in valores_variables if matriz_airport[pos[0]][pos[1]] != "PARKING")

        return assigned_workshops >= total_tasks

    for i, plane in enumerate(planes):
        same_plane_all_time_slots = [
            f"P{i}_T{n}" for n in range(numero_franjas)]

        def cover_all_tasks_with_plane_index(*valores_variables, plane_index=i):
            return cover_all_tasks(*valores_variables, plane_index=plane_index)

        problem.addConstraint(
            cover_all_tasks_with_plane_index,
            same_plane_all_time_slots
        )

    # Constraint 7:  Si un taller o parking tiene asignado algun avi ´ on en una franja horaria, al menos uno de los talleres o ´
    # parkings adyacentes vertical y horizontalmente debera estar vac ´ ´ıo
    def at_least_one_empty_adj(*valores_variables):
        # conseguir todas las empty postions
        occupied_positions = set(valores_variables)

        valid_postions_set = set(valid_positions)

        empty_positions = valid_postions_set - occupied_positions

        for pos in valores_variables:
            # conseguir adjacentes
            x, y = pos[0], pos[1]
            adj_positions = [
                (x - 1, y),
                (x + 1, y),
                (x, y - 1),
                (x, y + 1)
            ]
            # Verifica si alguno de los adyacentes está dentro del tablero; si una posición no es válida (fuera de rango o no existe), no estará en el tablero.
            has_valid_adj = False
            for adj_pos in adj_positions:
                if adj_pos in empty_positions:
                    has_valid_adj = True
                    break
            if not has_valid_adj:
                return False
        return True

    # Constraint 8: En ningun caso dos aviones JUMBO podr ´ an tener asignados talleres adyacentes en la misma franja ´horaria
    def no_adj_jumbo(*valores_variables):

        all_jumbo_in_workshops_pos = set([])
        for i, pos in enumerate(valores_variables):
            # tiene que ser un jumbo en un workshop
            if planes[i]["type"] == "JMB" and matriz_airport[pos[0]][pos[1]] != "PARKING":
                all_jumbo_in_workshops_pos.add(pos)

        for jumbo_pos in all_jumbo_in_workshops_pos:
            x, y = jumbo_pos[0], jumbo_pos[1]
            adj_positions = [
                (x - 1, y),
                (x + 1, y),
                (x, y - 1),
                (x, y + 1)
            ]

            for pos_adj in adj_positions:
                if pos_adj in all_jumbo_in_workshops_pos:
                    return False

        return True

    for n in range(numero_franjas):
        variables_franja = [f"P{i}_T{n}" for i in range(len(planes))]
        # problem.addConstraint(
        #     have_one_assigment_per_time_slot, variables_franja)
        problem.addConstraint(at_least_one_empty_adj, variables_franja)
        problem.addConstraint(no_adj_jumbo, variables_franja)

    # ----------------------------------------
    constraints_end_time = time.time()
    print(
        f"Constraints setup time: {constraints_end_time - constraints_start_time:.2f} seconds")

    solving_start_time = time.time()
    solutions = problem.getSolutions()
    solving_end_time = time.time()
    print(f"Solving time: {solving_end_time - solving_start_time:.2f} seconds")
    csv_start_time = time.time()
    generate_csv(solutions, file_path, planes, numero_franjas, matriz_airport)
    csv_end_time = time.time()
    print(f"CSV generation time: {csv_end_time - csv_start_time:.2f} seconds")
    total_time = time.time() - start_time
    print(f"Total program execution time: {total_time:.2f} seconds")


if __name__ == "__main__":
    main()
