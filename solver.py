import networkx as nx
import os

###########################################
# Change this variable to the path to
# the folder containing all three input
# size category folders
###########################################
path_to_inputs = "./all_inputs"

###########################################
# Change this variable if you want
# your outputs to be put in a
# different folder
###########################################
path_to_outputs = "./outputs"

def parse_input(folder_name):
    '''
        Parses an input and returns the corresponding graph and parameters

        Inputs:
            folder_name - a string representing the path to the input folder

        Outputs:
            (graph, num_buses, size_bus, constraints)
            graph - the graph as a NetworkX object
            num_buses - an integer representing the number of buses you can allocate to
            size_buses - an integer representing the number of students that can fit on a bus
            constraints - a list where each element is a list vertices which represents a single rowdy group
    '''
    graph = nx.read_gml(folder_name + "/graph.gml")
    graph.remove_edges_from(graph.selfloop_edges())
    parameters = open(folder_name + "/parameters.txt")
    num_buses = int(parameters.readline())
    size_bus = int(parameters.readline())
    constraints = []

    for line in parameters:
        line = line[1: -2]
        curr_constraint = [num.replace("'", "") for num in line.split(", ")]
        constraints.append(curr_constraint)

    return graph, num_buses, size_bus, constraints

def solve(graph, num_buses, size_bus, constraints):
    #TODO: Write this method as you like. We'd recommend changing the arguments here as well
    #Inputs: graph, num_buses, size_bus, constraints

    #Heuristic Order #1
    rowdy_number = {}
    for rowdy_list in constraints:
        for student in rowdy_list:
            if student in rowdy_number:
                rowdy_number[student] += 1
            else:
                rowdy_number[student] = 1
    for student in graph.nodes():
        if student not in rowdy_number:
            rowdy_number[student] = 0

    print(len(rowdy_number))
    #Heuristic Order #2
    semi_popular_students = {}
    for student in graph.nodes():
        if graph.degree[student] <= size_bus:
            semi_popular_students[student] = graph.degree()[student]
    for student in graph.nodes():
        if student not in semi_popular_students:
            semi_popular_students[student] = 0

    #Heuristic Order # 3
    most_popular_students = {}
    for student in graph.nodes():
        most_popular_students[student] = graph.degree()[student]

    print(len(most_popular_students))

    #Preprocessing of G' where G' is G, but without edges found in constraints
    graph_prime = graph.copy()
    #for student1 in graph_prime.nodes:
    #    for student2 in graph_prime.nodes:
    #        if graph_prime.has_edge(student1, student2):
    #            graph_prime[student1][student2]['weight'] = 1
    #            print(graph_prime[student1][student2]['weight'])


    for edge in graph_prime.edges():
        graph_prime[edge[0]][edge[1]]['weight'] = 1

    for rowdy_list in constraints:
        for student1 in rowdy_list:
            for student2 in rowdy_list:
                if graph_prime.has_edge(student1, student2):
                    graph_prime[student1][student2]['weight'] = 2

                else:
                    graph_prime.add_edge(student1, student2)
                    graph_prime[student1][student2]['weight'] = 2

    #Process Heuristics on G and G'
    points1, buses1 = heuristic_one(graph_prime, num_buses, size_bus, constraints, rowdy_number)
    points2, buses2 = heuristic_two(graph_prime, num_buses, size_bus, constraints, semi_popular_students)
    points3, buses3 = heuristic_three(graph_prime, num_buses, size_bus, constraints, most_popular_students)

    #Do Optimization (AKA swapping students for specific amount of iterations!)

    #Compare Results
    best_result = max(points1, points2, points3)
    # best_result = max(points1, points3)

    if (best_result == points1):
        best_buses = buses1
    elif (best_result == points2):
        best_buses = buses2
    else:
        best_buses = buses3

    attendance(best_buses)

    loner = ''
    blacklist = []

    for bus1 in best_buses:
        if len(bus1) == 0:
            for bus2 in best_buses:
                if bool(rowdy_number) == False:
                    break
                if list(rowdy_number.keys())[0] in bus2 and list(rowdy_number.keys())[0] not in blacklist:
                    loner = list(rowdy_number.keys())[0]
                    bus2.remove(list(rowdy_number.keys())[0])
                    bus1.append(loner)
                    blacklist.append(loner)
                    rowdy_number.pop(loner)
                    break

    attendance(best_buses)
    #Create .out output_file

    return best_buses


def heuristic_one(graph_prime, num_buses, size_bus, constraints, rowdy_number):
    #Sort students into buses
    buses = [[] for _ in range(num_buses)]
    best_bus = 0
    best_score = 0
    for student in sorted(rowdy_number, key=rowdy_number.get, reverse=True):
        for bus_num in range(num_buses):
            if (len(buses[bus_num]) >= size_bus):
                pass
            else:
                current_bus = buses[bus_num].copy()
                current_bus.append(student)
                current_score = bus_score(graph_prime, current_bus)
                if (current_score >= best_score):
                    best_bus = bus_num
                    best_score = current_score
        buses[best_bus].append(student)
    #Create an overall score based on the bus list created, then returns it.
    overall_score = 0
    for bus in buses:
        overall_score += bus_score(graph_prime, bus)

    return overall_score, buses

def heuristic_two(graph_prime, num_buses, size_bus, constraints, semi_popular_students):
    buses = [[] for _ in range(num_buses)]
    best_bus = 0
    best_score = 0
    for student in sorted(semi_popular_students, key=semi_popular_students.get, reverse=True):
        for bus_num in range(num_buses):
            if (len(buses[bus_num]) >= size_bus):
                pass
            else:
                current_bus = buses[bus_num].copy()
                current_bus.append(student)
                current_score = bus_score(graph_prime, current_bus)
                if (current_score >= best_score):
                    best_bus = bus_num
                    best_score = current_score
        buses[best_bus].append(student)

    #Create an overall score based on the bus list created, then returns it.
    overall_score = 0
    for bus in buses:
        overall_score += bus_score(graph_prime, bus)
    return overall_score, buses

def heuristic_three(graph_prime, num_buses, size_bus, constraints, most_popular_students):
    buses = [[] for _ in range(num_buses)]
    best_bus = 0
    best_score = 0
    for student in sorted(most_popular_students, key=most_popular_students.get, reverse=True):
        for bus_num in range(num_buses):
            if (len(buses[bus_num]) >= size_bus):
                pass
            else:
                current_bus = buses[bus_num].copy()
                current_bus.append(student)
                current_score = bus_score(graph_prime, current_bus)
                if (current_score >= best_score):
                    best_bus = bus_num
                    best_score = current_score
        buses[best_bus].append(student)

    #Create an overall score based on the bus list created, then returns it.
    overall_score = 0
    for bus in buses:
        overall_score += bus_score(graph_prime, bus)
    return overall_score, buses

def bus_score(graph_prime, bus):
    score = 0
    for student1 in range(len(bus)):
        for student2 in range(student1+1, len(bus)):
            if graph_prime.has_edge(student1, student2) and graph_prime[student1][student2]['weight'] == 1:
                score += 1
            else:
                pass
    #print(score)
    return score

def attendance(buses):
    count = 0
    for bus in buses:
        count += len(bus)
    print(count)

def main():
    '''
        Main method which iterates over all inputs and calls `solve` on each.
        The student should modify `solve` to return their solution and modify
        the portion which writes it to a file to make sure their output is
        formatted correctly.
    '''
    size_categories = ["small", "medium", "large"]
    if not os.path.isdir(path_to_outputs):
        os.mkdir(path_to_outputs)

    for size in size_categories:
        category_path = path_to_inputs + "/" + size
        output_category_path = path_to_outputs + "/" + size
        category_dir = os.fsencode(category_path)

        if not os.path.isdir(output_category_path):
            os.mkdir(output_category_path)

        for input_folder in os.listdir(category_dir):
            input_name = os.fsdecode(input_folder)
            if (input_name == '190'):
                graph, num_buses, size_bus, constraints = parse_input(category_path + "/" + input_name)
                solution = solve(graph, num_buses, size_bus, constraints)
                output_file = open(output_category_path + "/" + input_name + ".out", "w")

                #TODO: modify this to write your solution to your
                #      file properly as it might not be correct to
                #      just write the variable solution to a file
                for bus in solution:
                    print(bus)

                seat = 1
                for bus in solution:
                    output_file.write("[")
                    for student in bus:
                        if (seat != 1):
                            output_file.write(", '" + student + "'")
                        if (seat == 1):
                            output_file.write("'" + student + "'")
                            seat += 1
                    seat = 1
                    output_file.write("]\n")
                output_file.close()

if __name__ == '__main__':
    main()
