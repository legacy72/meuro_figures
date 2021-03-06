from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import numpy.random as r
import numpy as np
import random
import cv2
import re


COUNT_TRAINING_ITEMS = 80 # сколько из каждого файла берем фигур на тренировку
IMAGE_PIXELES = 28 * 28 # размер выходного слоя
OUTPUT_VARIANTS = 3 # размер выходного слоя
SECOND_LAYER = 5 # размер скрытого слоя


# запись в файл весов
def write_file(W, b):
    f = open('weights.txt', 'w')
    for index in W[1]:
        f.write(str(index) + '\n\n')
    f.close()

    f = open('weights.txt', 'a')
    f.write('-----\n\n')
    for index in W[2]:
        f.write(str(index) + '\n\n')
    f.close()

    f = open('weights.txt', 'a')
    f.write('Weights\n\n')
    for index in b[1]:
        f.write(str(index) + '\n\n')
    f.close()


# чтение весов из файла
def read_file():
    text = open('weights.txt').read()
    mass = re.split(r"-----|Weights", text)
    a1 = [[float(j) for j in
           i.replace('\n', '').replace('[ ', '[').replace('[', '').replace(' ]', ']').replace(']', '').replace('    ',
                                                                                                               ' ').replace(
               '   ', ' ').replace('  ', ' ').split(' ') if j != ''] for i in mass[0].split('\n\n') if i != '']
    a2 = [[float(j) for j in
           i.replace('\n', '').replace('[ ', '[').replace('[', '').replace(' ]', ']').replace(']', '').replace('    ',
                                                                                                               ' ').replace(
               '   ', ' ').replace('  ', ' ').split(' ') if j != ''] for i in mass[1].split('\n\n') if i != '']
    a3 = ['' if i == '' else float(i) for i in mass[2].split('\n\n')]
    for i in a3:
        if (i == ''):
            a3.remove(i)
    return a1, a2, a3


# перевод двумерный массив в одномерный numpy массив
def convert_to_numpy_simple_array(arr):
    arr = np.array(arr)
    return arr.reshape(1, IMAGE_PIXELES)[0]


# перевод картинок для тренировки в массив
def get_matrix_images_for_train():
    images = []
    target = []

    for i in range(1, COUNT_TRAINING_ITEMS + 1):
        image = cv2.imread('./circles/drawing(' + str(i) + ').png', 0)
        images.append(convert_to_numpy_simple_array(image))
        target.append(0)

    for i in range(1, COUNT_TRAINING_ITEMS + 1):
        image = cv2.imread('./squares/drawing(' + str(i) + ').png', 0)
        images.append(convert_to_numpy_simple_array(image))
        target.append(1)

    for i in range(1, COUNT_TRAINING_ITEMS + 1):
        image = cv2.imread('./triangles/drawing(' + str(i) + ').png', 0)
        images.append(convert_to_numpy_simple_array(image))
        target.append(2)

    return images, target


# перевод картинок для тестирования в массив
def get_matrix_images_for_test():
    images = []
    target = []

    for i in range(COUNT_TRAINING_ITEMS + 1, 100):
        image = cv2.imread('./circles/drawing(' + str(i) + ').png', 0)
        images.append(convert_to_numpy_simple_array(image))
        target.append(0)

    for i in range(COUNT_TRAINING_ITEMS + 1, 100):
        image = cv2.imread('./squares/drawing(' + str(i) + ').png', 0)
        images.append(convert_to_numpy_simple_array(image))
        target.append(1)

    for i in range(COUNT_TRAINING_ITEMS + 1, 100):
        image = cv2.imread('./triangles/drawing(' + str(i) + ').png', 0)
        images.append(convert_to_numpy_simple_array(image))
        target.append(2)

    return images, target


def convert_y_to_vect(y):
    y_vect = np.zeros((len(y), OUTPUT_VARIANTS))
    for i in range(len(y)):
        y_vect[i, y[i]] = 1
    return y_vect


def f(x):
    return 1 / (1 + np.exp(-x))


def f_deriv(x):
    return f(x) * (1 - f(x))


def setup_and_init_weights(nn_structure):
    W = {}
    b = {}
    for l in range(1, len(nn_structure)):
        W[l] = r.random_sample((nn_structure[l], nn_structure[l-1]))
        b[l] = r.random_sample((nn_structure[l],))
    return W, b


def setup_and_init_weights_from_file():
    a1, a2, a3 = read_file()
    W = {}
    W[1] = np.array(a1)
    W[2] = np.array(a2)
    b = np.array(a3)
    return W, b


def init_tri_values(nn_structure):
    tri_W = {}
    tri_b = {}
    for l in range(1, len(nn_structure)):
        tri_W[l] = np.zeros((nn_structure[l], nn_structure[l-1]))
        tri_b[l] = np.zeros((nn_structure[l],))
    return tri_W, tri_b


def feed_forward(x, W, b):
    h = {1: x}
    z = {}
    for l in range(1, len(W) + 1):
        # if it is the first layer, then the input into the weights is x, otherwise,
        # it is the output from the last layer
        if l == 1:
            node_in = x
        else:
            node_in = h[l]
        z[l+1] = W[l].dot(node_in) + b[l] # z^(l+1) = W^(l)*h^(l) + b^(l)
        h[l+1] = f(z[l+1]) # h^(l) = f(z^(l))
    return h, z


def calculate_out_layer_delta(y, h_out, z_out):
    # delta^(nl) = -(y_i - h_i^(nl)) * f'(z_i^(nl))
    return -(y-h_out) * f_deriv(z_out)


def calculate_hidden_delta(delta_plus_1, w_l, z_l):
    # delta^(l) = (transpose(W^(l)) * delta^(l+1)) * f'(z^(l))
    return np.dot(np.transpose(w_l), delta_plus_1) * f_deriv(z_l)


def train_nn(nn_structure, X, y, iter_num=1000, alpha=0.25):
    W, b = setup_and_init_weights(nn_structure)
    cnt = 0
    m = len(y)
    avg_cost_func = []
    print('Starting gradient descent for {} iterations'.format(iter_num))
    while cnt < iter_num:
        if cnt % 100 == 0:
            print('Iteration {} of {}'.format(cnt, iter_num))
        tri_W, tri_b = init_tri_values(nn_structure)
        avg_cost = 0
        for i in range(len(y)):
            delta = {}
            # perform the feed forward pass and return the stored h and z values, to be used in the
            # gradient descent step
            h, z = feed_forward(X[i, :], W, b)
            # loop from nl-1 to 1 backpropagating the errors
            for l in range(len(nn_structure), 0, -1):
                if l == len(nn_structure):
                    delta[l] = calculate_out_layer_delta(y[i,:], h[l], z[l])
                    avg_cost += np.linalg.norm((y[i,:]-h[l]))
                else:
                    if l > 1:
                        delta[l] = calculate_hidden_delta(delta[l+1], W[l], z[l])
                    # triW^(l) = triW^(l) + delta^(l+1) * transpose(h^(l))
                    tri_W[l] += np.dot(delta[l+1][:,np.newaxis], np.transpose(h[l][:,np.newaxis]))
                    # trib^(l) = trib^(l) + delta^(l+1)
                    tri_b[l] += delta[l+1]
        # perform the gradient descent step for the weights in each layer
        for l in range(len(nn_structure) - 1, 0, -1):
            W[l] += -alpha * (1.0/m * tri_W[l])
            b[l] += -alpha * (1.0/m * tri_b[l])
        # complete the average cost calculation
        avg_cost = 1.0/m * avg_cost
        avg_cost_func.append(avg_cost)
        cnt += 1

    return W, b, avg_cost_func


def predict_y(W, b, X, n_layers):
    m = X.shape[0]
    y = np.zeros((m,))
    for i in range(m):
        h, z = feed_forward(X[i, :], W, b)
        y[i] = np.argmax(h[n_layers])
    return y, h


# Прогоняем через сеть картинку
def predict_image(W, b, X):
    h, z = feed_forward(X, W, b)
    return h


# Тренировка сети
def train():
    images, y_train = get_matrix_images_for_train() # массив пикселей картинки и соответсвующее им значение (круг, квадрат, треугольник)
    X_scale = StandardScaler()
    X_train = X_scale.fit_transform(images)

    y_v_train = convert_y_to_vect(y_train)

    nn_structure = [IMAGE_PIXELES, SECOND_LAYER, OUTPUT_VARIANTS]
    W, b, avg_cost_func = train_nn(nn_structure, X_train, y_v_train)
    plt.plot(avg_cost_func)
    plt.ylabel('Average J')
    plt.xlabel('Iteration number')
    plt.show()

    write_file(W, b)


# Тестирование сети
def test():
    images, y_test = get_matrix_images_for_test() # массив пикселей картинки
    X_test = StandardScaler().fit_transform(images)
    W, b = setup_and_init_weights_from_file()

    # случайно индекс для выбора рандомной картинки на сверку
    rand = random.randint(1, 56)

    y_pred, h_pred = predict_y(W, b, X_test, 3)

    predicted_result = predict_image(W, b, X_test[rand])
    answer = predicted_result[3]

    # вероятность угадать
    accuracy_score(y_test, y_pred) * 100
    print('Prediction accuracy is {}%'.format(accuracy_score(y_test, y_pred) * 100))

    # вывод картинки
    plt.matshow([predicted_result[1][i: i + 28] for i in range(0, len(predicted_result[1]), 28)])
    plt.show()

    figure_index = answer.tolist().index(max(answer))
    if figure_index == 0:
        print('Круг')
    elif figure_index == 1:
        print('Квадрат')
    elif figure_index == 2:
        print('Треугольник')


if __name__ == "__main__":
    print("1 - тренировка\n2 - тестирование")
    menu = int(input())

    if menu == 1:
        train()
    elif menu == 2:
        test()
    else:
        print('некорректный ввод')