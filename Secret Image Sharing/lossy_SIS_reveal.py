import numpy as np
from fractions import Fraction as frac
import cv2

def read_image(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path, 0)
    return img

def save_image(image: np.ndarray, image_path: str) -> None:
    cv2.imwrite(image_path, image)
    print(f"Image saved successfully at {image_path}")

def lagrange_interpolation(keys: list, p: int) -> list:
    n = len(keys)
    coeff = [0] * n

    for i in range(n):
        roots = tuple()
        deno = 1
        for j in range(n):
            if i!=j:
                roots += (keys[j][0],)
                deno *= (keys[i][0] - keys[j][0])
        coef = np.poly(roots)
        for k in range(n): coeff[k] += frac(int(coef[k]) * keys[i][1], deno)
    
    for i in range(n):
        coeff[i] = frac(coeff[i].numerator%p,coeff[i].denominator)
        num = coeff[i].numerator
        den = coeff[i].denominator
        if den != 1:
            while num%den: num += p

        coeff[i] = num//den
    
    coeff.reverse()
    return coeff

def lossy_SIS_reveal_phase(keys: list, n: list, r: int, p: int) -> np.ndarray:
    k = len(keys)
    x, y = keys[0].shape
    original_image = np.zeros(shape=(x,y*r))
    for i in range(x):
        for j in range(y):
            temp_keys = []
            for l in range(k):
                temp_keys = temp_keys + [(n[l], keys[l][i][j])]
            temp_pixel = lagrange_interpolation(temp_keys, p)
            for l in range(r):
                original_image[i][(j*r)+l] = temp_pixel[l]
    
    return original_image

def main(keys: list, r: int, ext: str) -> None:
    p = 251
    k = len(keys)
    n = [int(keys[i][-5]) for i in range(k)]
    try:
        keys = [read_image(keys[i]) for i in range(k)]
        original_image = lossy_SIS_reveal_phase(keys, n, r, p)
        save_image(original_image, f"Sample Images/original_image{ext}")
    except Exception as e:
        print('Error:', e)


if __name__ == '__main__':
    r = int(input("Enter the least number of keys required to reconstruct the image: "))
    k = int(input("Enter the number of keys you have: "))
    if k < r:
        print(f"Atleast {r} keys are required to reconstruct the image.")
        exit(0)
    keys = [] * k
    print("\nEnter the paths of the keys:")
    for i in range(k): 
        keys.append(input(f"Enter the path of the key {i+1}: "))
    ext = keys[0][keys[0].find('.'):]
    main(keys, r, ext)