import numpy as np

#   Writes two arrays x and y to a text file.
def write_to_file(x, y, filename):
    with open(filename, 'w') as f:
        for i in range(len(x)):
            f.write(f"{x[i]} {y[i]}\n")

#   Writes two x arrays and one y array to a text file.
def write_to_file2x(x1, x2, y, filename):
    with open(filename, 'w') as f:
        for i in range(len(x1)):
            f.write(f"{x1[i]} {x2[i]} {y[i]}\n")

#   Writes one x array and 2 to 5 y arrays to a text file
def write_to_file_multiy(filename, x, y1, y2, y3=None, y4=None, y5=None):
    with open(filename, 'w') as f:
        for i in range(len(x)):
            output = f"{x[i]} {y1[i]} {y2[i]}"
            if y3 is not None:
                output += f" {y3[i]}"
                if y4 is not None:
                    output += f" {y4[i]}"
                    if y5 is not None:
                        output += f" {y5[i]}"
            f.write(f"{output}\n")

#   Reads two arrays from a text file.
def read_from_file(filename):
    x, y = [], []
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            values = line.split()
            x.append(float(values[0]))
            y.append(float(values[1]))
    return np.array(x), np.array(y)

#   Reads three arrays from a text file.
def read_from_file2x(filename):
    x1, x2, y = [], [], []
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            values = line.split()
            x1.append(float(values[0]))
            x2.append(float(values[1]))
            y.append(float(values[2]))
    return np.array(x1), np.array(x2), np.array(y)

#   Reads 3 to 5 arrays from a text file
def read_from_file_multiy(filename, num_y=2):
    x, y1, y2, y3, y4, y5 = [], [], [], [], [], []
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            values = line.split()
            x.append(float(values[0]))
            y1.append(float(values[1]))
            y2.append(float(values[2]))
            if num_y > 2:
                y3.append(float(values[3]))
                if num_y > 3:
                    y4.append(float(values[4]))
                    if num_y > 4:
                        y5.append(float(values[5]))
    return np.array(x), np.array(y1), np.array(y2), np.array(y3), np.array(y4), np.array(y5)

if __name__ == "__main__":
    # Example usage:
    x = np.array([1, 2, 3, 4])
    y = np.array([5, 6, 7, 8])
    y2 = np.array([5, 6, 7, 8])
    y3 = np.array([5, 6, 7, 8])
    y4 = np.array([5, 6, 7, 8])
    y5 = np.array([5, 6, 7, 8])
    filename = "data/arrays.txt"

    """ write_to_file(x, y, filename)
    x_read, y_read = read_from_file(filename)
    print("x_read:", x_read)
    print("y_read:", y_read) """

    write_to_file_multiy(filename, x, y, y2, y3, y4)
    xr, y1r, y2r, y3r, y4r, _ = read_from_file_multiy(filename, num_y=4)

    print(xr)
    print(y1r)
    print(y2r)
    print(y3r)
    print(y4r)
