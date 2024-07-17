import cv2
import numpy as np

def truncate_gray_values(img: np.ndarray, p: int) -> np.ndarray:
    x, y = img.shape
    for i in range(x):
        for j in range(y):
            img[i][j] = 250 if img[i][j] > (p-1) else img[i][j]
    return img

def create_sections(img: np.ndarray, r: int) -> list:
    sections = []
    temp_section = []
    x, y = img.shape
    
    for i in range(x):
        for j in range(y):
            temp_section.append(img[i][j])
            if len(temp_section) == r:
                sections.append(temp_section)
                temp_section = []

    return sections

def generate_shadow_images(sections: list, img_shape: tuple, n: int) -> list:
    r = len(sections[0])
    l = len(sections)
    x, y = img_shape
    y = y // r
    shadows = [np.zeros(shape=(x,y)) for _ in range(n)]

    for i in range(l):
        for j in range(n):
            temp_pixel = 0
            for k in range(r):
                temp_pixel += sections[i][k] * ((j+1) ** k)
            shadows[j][i//y][i%y] = temp_pixel % 251
    
    return shadows

def save_shadow_images(shadows: list, image_path: str) -> None:
    for i, shadow in enumerate(shadows, start = 1):
        cv2.imwrite(f'{image_path[:-4]}_shadow_images/{i}.bmp', shadow)
        print(f"Shadow image saved successfully at {image_path[:-4]}shadow_images")
    

def lossy_SIS_sharing_phase(img: np.ndarray, r: int, n: int, p: int) -> list:
    img = truncate_gray_values(img, p)
    sections = create_sections(img, r)
    shadows = generate_shadow_images(sections, img.shape, n)
    return shadows

def main(image_path: str, n: int, r: int) -> None:
    p = 251
    try:
        img = cv2.imread(image_path, 0)
        shadows = lossy_SIS_sharing_phase(img, r, n, p)
        save_shadow_images(shadows, image_path)
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    path = input("Enter the path of the image: ")
    n = int(input("Enter the number of shadow images: "))
    r = int(input("Enter the least number of keys required to reconstruct the image: "))
    main(path, n, r)