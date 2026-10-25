import os
import sys
import numpy as np
import pygame
import imageio

os.environ['SDL_VIDEODRIVER'] = 'dummy'
import flower2

W, H = flower2.W, flower2.H
FPS = 30
DURATION = 16.0  # seconds
TOTAL_FRAMES = int(FPS * DURATION)

def generate_video_and_poster():
    print(f"Initializing video generation: {TOTAL_FRAMES} frames @ {FPS} fps...")
    pygame.display.init()
    screen = pygame.display.set_mode((W, H))
    buf = np.zeros((W, H, 3), np.uint8)

    writer = imageio.get_writer(
        'flower.mp4',
        fps=FPS,
        codec='libx264',
        pixelformat='yuv420p',
        output_params=['-movflags', '+faststart']
    )

    for i in range(TOTAL_FRAMES):
        t = i / FPS
        flower2.render(t, buf)
        pygame.surfarray.blit_array(screen, buf)
        flower2.glow(screen)
        frame = np.transpose(pygame.surfarray.array3d(screen), (1, 0, 2))
        writer.append_data(frame)

        if i == 0:
            imageio.imwrite('poster.jpg', frame)
            print("Saved poster.jpg (frame 0)")

        if (i + 1) % 60 == 0 or (i + 1) == TOTAL_FRAMES:
            print(f"Rendered {i + 1}/{TOTAL_FRAMES} frames ({((i + 1)/TOTAL_FRAMES)*100:.1f}%)")

    writer.close()
    print("Successfully generated flower.mp4!")

if __name__ == '__main__':
    generate_video_and_poster()
